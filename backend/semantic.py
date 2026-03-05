class Symbol:
    def __init__(self, name, symbol_type, data_type=None, value=None, is_const=False, line=None, column=None, dimension=0, sizes=None):
        self.name = name
        self.symbol_type = symbol_type  # variable, function, struct, parameter
        self.data_type = data_type      # num, deci, word, single, bool
        self.value = value
        self.is_const = is_const
        self.line = line
        self.column = column
        self.dimension = dimension
        self.sizes = sizes

    def __repr__(self):
        return (f"Symbol(name={self.name}, type={self.symbol_type}, data_type={self.data_type}, "
                f"value={self.value}, const={self.is_const}, line={self.line}, "
                f"col={self.column}, dim={self.dimension}, sizes={self.sizes})")


class Semantic:
    def __init__(self):# initialize to save smthng
        self.symbol_table = {}      # {scope: {name: Symbol}}
        self.struct_table = {}      # {struct_name: [(field_name, field_type), ...]}
        self.errors = []
        self.current_scope = "global"
        self.scope_stack = ["global"]
        self.tokens = []
        self.index = 0
        self.data_types = {"num", "deci", "word", "single", "bool"}

        # What literal types are valid for each data type
        self.valid_types = {
            "num":    ["num_literal", "bool", "deci_literal"],
            "deci":   ["num_literal", "deci_literal", "bool"],
            "bool":   ["true", "false", "num_literal", "deci_literal"],
            "single": ["single_literal"],
            "word":   ["word_literal"],
        }

    # ------------------------------------------------------------------ #
    #  Main entry point
    # ------------------------------------------------------------------ #
    def semantic_analyzer(self, tokens):
        self.tokens = tokens
        self.index = 0
        self.data_types = {"num", "deci", "bool", "single", "word"}

        if self.current_scope not in self.symbol_table: #If this scope is not yet in the symbol table, create it
            self.symbol_table[self.current_scope] = {}

        while self.index < len(self.tokens):
            lexeme, token_type, line, column = self.tokens[self.index]

            if token_type == "const":
                self.const_declaration()

            elif token_type == "struct":  #"struct", "Person", "IDENTIFIER","{",  
                next_tok = self.tokens[self.index + 1][0] if self.index + 1 < len(self.tokens) else None
                next_next = self.tokens[self.index + 2][0] if self.index + 2 < len(self.tokens) else None
                if next_next == "{":
                    self.struct_declaration()
                else:
                    self.struct_variable_declaration()

            elif token_type in self.data_types:
                self.variable_declaration()

            elif token_type in ("function", "vacant", "main"):
                self.function_declaration()

            else:
                self.index += 1

        return self.errors

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #
    def _peek(self, offset=1): #Look ahead in the token list without moving the current position. And avoids crashing if there is no next token
        idx = self.index + offset # self.index = 4 offset = 1 = 5
        if idx < len(self.tokens): # this line prevents crashing, Is that position valid? 0, 1, 2, 3, 4 If idx = 10, that would crash.
            return self.tokens[idx] # If so, return the token at that position.
        return (None, None, -1, 0) # If idx is NOT valid (too big), Instead of crashing, it returns:

    def is_duplicate_variable(self, var_name, line, column):
        if (var_name in self.symbol_table.get(self.current_scope, {}) or
                var_name in self.symbol_table.get("global", {})):
            self.errors.append(
                f"⚠️ Semantic Error at (line {line}, column {column}): "
                f"Variable '{var_name}' is already declared."
            )
            return True
        return False

    def is_type_mismatch(self, data_type, value_type, var_name, line, column):
        valid_types = {
            "num":    ["num_literal", "bool", "deci_literal", "user_input"],
            "deci":   ["num_literal", "deci_literal", "bool", "user_input"],
            "bool":   ["bool", "num_literal", "deci_literal", "user_input"],
            "single": ["single_literal", "user_input"],
            "word":   ["word_literal", "user_input"],
        }
        conditions = {"if", "elseif", "while"}

        if value_type == "error":
            return True

        if value_type in valid_types.get(data_type, []):
            return False

        if var_name in conditions:
            self.errors.append(
                f"⚠️ Semantic Error at (line {line}, column {column}): "
                f"Condition returns incorrect value. "
                f"Expected '{self.valid_types.get(data_type, [])}', got '{value_type}'."
            )
        else:
            self.errors.append(
                f"⚠️ Semantic Error at (line {line}, column {column}): "
                f"Assign Value Mismatch for '{var_name}'. "
                f"Expected '{self.valid_types.get(data_type, [])}', got '{value_type}'."
            )
        return True

    def is_type_compatible(self, expected, actual):
        type_map = {
            "num":    ["num_literal", "user_input"],
            "deci":   ["deci_literal", "num_literal", "user_input"],
            "bool":   ["true", "false", "user_input"],
            "single": ["single_literal", "user_input"],
            "word":   ["word_literal", "user_input"],
        }
        return actual in type_map.get(expected, [])

    def store_variable(self, var_name, symbol_type, data_type, is_const, line, column, dimension, sizes=None):
        self.symbol_table[self.current_scope][var_name] = Symbol(
            name=var_name,
            symbol_type=symbol_type,
            data_type=data_type,
            value=None,
            is_const=is_const,
            line=line,
            column=column,
            dimension=dimension,
            sizes=sizes
        )

    def _skip_to_semi(self):
        while self.index < len(self.tokens) and self.tokens[self.index][1] != ";":
            self.index += 1
        if self.index < len(self.tokens):
            self.index += 1  # consume the semicolon

    # ------------------------------------------------------------------ #
    #  const declaration  →  const <data_type> id = <literal>, ... ;
    # ------------------------------------------------------------------ #
    def const_declaration(self):
        self.index += 1  # move past 'const'
        data_type = self.tokens[self.index][1]  # data type token
        dimension = 0

        while True:
            self.index += 1  # move to identifier
            var_name, token_type, line, column = self.tokens[self.index]

            if self.is_duplicate_variable(var_name, line, column):
                self._skip_to_semi()
                return

            self.index += 1  # move to '='
            self.index += 1  # move to value

            value_type = self.tokens[self.index][1]
            if self.is_type_mismatch(data_type, value_type, var_name, line, column):
                self._skip_to_semi()
                return

            self.store_variable(var_name, "const_declaration", data_type,
                                is_const=True, line=line, column=column, dimension=dimension)

            self.index += 1  # move to ',' or ';'
            if self.tokens[self.index][1] == ";":
                break
            elif self.tokens[self.index][1] == ",":
                continue

    # ------------------------------------------------------------------ #
    #  struct type declaration  →  struct Name { <field>* }
    # ------------------------------------------------------------------ #
    def struct_declaration(self):
        self.index += 1  # past 'struct'
        struct_name, _, line, column = self.tokens[self.index]

        if struct_name in self.struct_table:
            self.errors.append(
                f"⚠️ Semantic Error at (line {line}, column {column}): "
                f"Struct '{struct_name}' is already declared."
            )
            return

        self.index += 1  # to '{'
        self.index += 1  # inside block

        fields = []
        while self.tokens[self.index][0] != "}":
            field_type_lex, field_type_tok, line, column = self.tokens[self.index]

            if field_type_tok not in self.data_types:
                self.errors.append(
                    f"⚠️ Semantic Error at (line {line}, column {column}): "
                    f"Invalid data type '{field_type_lex}' in struct definition."
                )
                return

            self.index += 1  # to field name
            field_name, _, line, column = self.tokens[self.index]
            fields.append((field_name, field_type_lex))

            self.index += 1  # past field name
            if self.tokens[self.index][0] == ";":
                self.index += 1  # move to next field or '}'

        self.struct_table[struct_name] = fields
        self.index += 1  # past '}'

    # ------------------------------------------------------------------ #
    #  struct variable declaration  →  struct Name var [= { ... }] ;
    # ------------------------------------------------------------------ #
    def struct_variable_declaration(self):
        self.index += 1  # past 'struct'
        struct_name, _, line, column = self.tokens[self.index]

        if struct_name not in self.struct_table:
            self.errors.append(
                f"⚠️ Semantic Error at (line {line}, column {column}): "
                f"Struct '{struct_name}' is not declared."
            )
            return

        self.index += 1  # to variable name
        var_name, _, line, column = self.tokens[self.index]

        if var_name in self.symbol_table.get(self.current_scope, {}):
            self.errors.append(
                f"⚠️ Semantic Error at (line {line}, column {column}): "
                f"Variable '{var_name}' is already declared."
            )
            return

        self.index += 1  # to '=' or ';'

        if self.tokens[self.index][0] == "=":
            self.index += 1  # past '='
            self.index += 1  # past '{', now at first value

            struct_fields = self.struct_table[struct_name]
            expected_count = len(struct_fields)
            provided = []

            while self.tokens[self.index][0] != "}":
                provided.append(self.tokens[self.index])
                self.index += 1
                if self.tokens[self.index][0] == ",":
                    self.index += 1

            if len(provided) != expected_count:
                self.errors.append(
                    f"⚠️ Semantic Error at (line {line}, column {column}): "
                    f"Struct '{struct_name}' expected {expected_count} values, "
                    f"but got {len(provided)}."
                )
                return

            for (fname, ftype), (val, vtype, vline, vcol) in zip(struct_fields, provided):
                if not self.is_type_compatible(ftype, vtype):
                    self.errors.append(
                        f"⚠️ Semantic Error at (line {vline}, column {vcol}): "
                        f"Field '{fname}' in struct '{struct_name}' expects '{ftype}', "
                        f"but got '{vtype}'."
                    )
                    return

            self.index += 1  # past '}'

        # Store the struct variable
        self.symbol_table[self.current_scope][var_name] = Symbol(
            name=var_name,
            symbol_type="struct_variable",
            data_type=struct_name,
            value=None,
            line=line,
            column=column,
        )

    # ------------------------------------------------------------------ #
    #  Variable declaration  →  <type> id [<arr>] [= <expr>] , ... ;
    # ------------------------------------------------------------------ #
    def variable_declaration(self):
        symbol_type = "Variable Declaration"
        data_type = self.tokens[self.index][1]
        dimension = 0
        sizes = None

        while True:
            self.index += 1  # to identifier
            var_name, token_type, line, column = self.tokens[self.index]

            if self.is_duplicate_variable(var_name, line, column):
                while self.index < len(self.tokens) and self.tokens[self.index][1] not in (";", ","):
                    self.index += 1
                if self.index >= len(self.tokens) or self.tokens[self.index][1] == ";":
                    break
                else:
                    continue

            self.index += 1  # symbol after identifier

            if self.tokens[self.index][1] == "[":
                symbol_type, dimension, sizes = self.array_declaration(line)

            if self.tokens[self.index][1] == "=":
                self.index += 1  # to value

                if dimension > 0:
                    if self.tokens[self.index][1] == "{":
                        array_size, value_type = self.array_initialization(data_type, dimension)
                        if value_type == "error" or array_size is None:
                            return  # stop processing, error already recorded
                        if sizes is None:
                            sizes = array_size
                        else:
                            if not self.verify_array_size_match(sizes, array_size, var_name, line, column):
                                return
                else:
                    value_type = self.validate_expression()
                    if self.is_type_mismatch(data_type, value_type, var_name, line, column):
                        return

            self.store_variable(var_name, symbol_type, data_type,
                                is_const=False, line=line, column=column,
                                dimension=dimension, sizes=sizes)

            if self.tokens[self.index][1] == ";":
                break
            if self.tokens[self.index][1] == ",":
                continue

    # ------------------------------------------------------------------ #
    #  Array size declaration
    # ------------------------------------------------------------------ #
    def array_declaration(self, line):
        symbol_type = "array_declaration"
        dimension = 0
        sizes = []

        self.index += 1  # past '[' → size or ']'
        if self.tokens[self.index][1] == "num_literal":
            token_value = self.tokens[self.index][0]
            if token_value.startswith('~'):
                self.errors.append(f"⚠️ Semantic Error at (line {line}): Array size must be a positive integer")
                self.index += 1
            elif int(token_value) > 0:
                sizes.append(int(token_value))
                self.index += 1
            else:
                self.errors.append(f"⚠️ Semantic Error at (line {line}): Array size must be a positive integer")
                self.index += 1
        else:
            sizes = None

        self.index += 1  # past ']'
        dimension = 1

        if self.index < len(self.tokens) and self.tokens[self.index][1] == "[":
            self.index += 1  # to second size
            token_value = self.tokens[self.index][0]
            if token_value.startswith('~'):
                self.errors.append(f"⚠️ Semantic Error at (line {line}): Array size must be a positive integer")
            elif int(token_value) > 0:
                sizes.append(int(token_value))
            else:
                self.errors.append(f"⚠️ Semantic Error at (line {line}): Array size must be a positive integer")
            self.index += 1  # past value
            dimension = 2
            self.index += 1  # past ']'

        return symbol_type, dimension, sizes

    def array_initialization(self, data_type, dimension):
        self.index += 1  # past '{'
        element_count = 0
        row_count = 0
        col_count = 0
        max_col = 0
        value_type = None

        if dimension == 1:
            while self.index < len(self.tokens) and self.tokens[self.index][1] != "}":
                lexeme = self.tokens[self.index][0]
                value_type = self.tokens[self.index][1]
                if self.is_type_mismatch(data_type, value_type, lexeme,
                                         self.tokens[self.index][2], self.tokens[self.index][3]):
                    return None, "error"
                element_count += 1
                self.index += 1
                if self.tokens[self.index][1] == ",":
                    self.index += 1
                elif self.tokens[self.index][1] == "}":
                    break
            self.index += 1  # past '}'
            return [element_count], value_type

        elif dimension == 2:
            while self.index < len(self.tokens) and self.tokens[self.index][1] != "}":
                if self.tokens[self.index][1] == "{":
                    row_count += 1
                    col_count = 0
                    self.index += 1
                    while self.index < len(self.tokens) and self.tokens[self.index][1] != "}":
                        value_type = self.tokens[self.index][1]
                        if self.is_type_mismatch(data_type, value_type, "",
                                                 self.tokens[self.index][2], self.tokens[self.index][3]):
                            return None, "error"
                        col_count += 1
                        self.index += 1
                        if self.tokens[self.index][1] == ",":
                            self.index += 1
                        elif self.tokens[self.index][1] == "}":
                            break
                    max_col = max(max_col, col_count)
                    self.index += 1
                    if self.tokens[self.index][1] == ",":
                        self.index += 1
                    elif self.tokens[self.index][1] == "}":
                        break
            self.index += 1
            return [row_count, max_col], value_type

    def verify_array_size_match(self, declared, init_sizes, var_name, line, column):
        if len(declared) != len(init_sizes):
            self.errors.append(
                f"⚠️ Semantic Error at (line {line}, column {column}): "
                f"Dimension mismatch for array '{var_name}'."
            )
            return False
        for i in range(len(declared)):
            if declared[i] is not None and declared[i] < init_sizes[i]:
                self.errors.append(
                    f"⚠️ Semantic Error at (line {line}, column {column}): "
                    f"Exceeding elements in array '{var_name}', dimension {i+1}. "
                    f"Expected max {declared[i]}, got {init_sizes[i]}."
                )
                return False
        return True

    # ------------------------------------------------------------------ #
    #  Function / vacant / main declaration
    # ------------------------------------------------------------------ #
    def function_declaration(self):
        return_type = "vacant"

        if self.tokens[self.index][1] == "main":
            self.index -= 1  # align: will be incremented next line

        self.index += 1  # past 'function' / 'vacant' / 'main'
        function_name, token_type, line, column = self.tokens[self.index]

        if function_name in self.symbol_table.get("global", {}):
            self.errors.append(
                f"⚠️ Semantic Error at (line {line}, column {column}): "
                f"'{function_name}' is already declared."
            )

        self.symbol_table[function_name] = {}
        self.current_scope = function_name
        self.scope_stack.append(function_name)

        self.index += 1  # to '('
        self.index += 1  # into parameters

        parameters = []

        while self.tokens[self.index][0] != ")":
            param_type_lex, param_type_tok, line, column = self.tokens[self.index]
            self.index += 1  # to param name
            param_name, _, line, column = self.tokens[self.index]

            self.symbol_table[function_name][param_name] = Symbol(
                name=param_name,
                symbol_type="parameter",
                data_type=param_type_lex,
                line=line,
                column=column
            )
            parameters.append((param_name, param_type_lex))

            self.index += 1  # to ',' or ')'
            if self.tokens[self.index][0] == ",":
                self.index += 1

        self.index += 1  # past ')'

        if self.tokens[self.index][0] == "{":
            self.index += 1  # past '{'
            brace_level = 1

            conditions = {"if", "elseif", "while"}

            while self.index < len(self.tokens) and brace_level > 0:
                lexeme, token_type, line, column = self.tokens[self.index]

                if lexeme == "{":
                    brace_level += 1
                elif lexeme == "}":
                    brace_level -= 1
                    if brace_level == 0:
                        break

                # ---- local variable declarations ----
                if token_type in self.data_types:
                    self.variable_declaration()
                    continue

                elif token_type == "const":
                    self.const_declaration()
                    continue

                elif token_type == "struct":
                    nnext = self.tokens[self.index + 2][0] if self.index + 2 < len(self.tokens) else None
                    if nnext == "{":
                        self.struct_declaration()
                    else:
                        self.struct_variable_declaration()
                    continue

                # ---- statements ----
                elif token_type == "identifier":
                    next_lex = self.tokens[self.index + 1][0] if self.index + 1 < len(self.tokens) else None
                    if next_lex in ("++", "--"):
                        # post-increment / post-decrement
                        if not self._resolve_identifier(lexeme, line, column):
                            self._skip_to_semi()
                        else:
                            symbol = self._lookup(lexeme)
                            type_mapping = {"num": "num_literal", "deci": "deci_literal",
                                            "bool": "bool", "single": "single_literal", "word": "word_literal"}
                            val_type = type_mapping.get(symbol.data_type)
                            if self.is_type_mismatch("num", val_type, lexeme, line, column):
                                return
                            self.index += 1  # past identifier
                    else:
                        self.validate_id_statement()

                elif token_type in ("++", "--"):
                    # pre-increment / pre-decrement
                    self.index += 1
                    lexeme2, token_type2, line2, column2 = self.tokens[self.index]
                    if not self._resolve_identifier(lexeme2, line2, column2):
                        self._skip_to_semi()
                    else:
                        symbol = self._lookup(lexeme2)
                        type_mapping = {"num": "num_literal", "deci": "deci_literal",
                                        "bool": "bool", "single": "single_literal", "word": "word_literal"}
                        val_type = type_mapping.get(symbol.data_type)
                        if self.is_type_mismatch("num", val_type, lexeme2, line2, column2):
                            return

                elif token_type in conditions:
                    self.index += 1  # past 'if'/'elseif'/'while'
                    cond_type = self.validate_expression()
                    if cond_type != "error" and self.index < len(self.tokens) and self.tokens[self.index][1] == "{":
                        brace_level += 1
                    if cond_type != "error":
                        if self.is_type_mismatch("bool", cond_type, lexeme, line, column):
                            return

                elif token_type == "match":
                    self.index += 1  # past 'match'
                    brace_level += 1
                    _ = self.validate_expression()

                elif token_type == "pick":
                    self.index += 1  # past 'pick'
                    _ = self.validate_expression()

                elif token_type == "for":
                    self.index += 2  # past 'for' and '('
                    for_init = self.validate_expression()
                    if self.is_type_mismatch("num", for_init, lexeme, line, column):
                        return

                elif token_type == "out":
                    # out( expr + expr ... )
                    self.index += 1  # past 'out'
                    while token_type != ")":
                        self.index += 1
                        lexeme2, token_type, line2, column2 = self.tokens[self.index]
                        if token_type == "identifier":
                            if not self._resolve_identifier(lexeme2, line2, column2):
                                pass
                            else:
                                symbol = self._lookup(lexeme2)
                                if symbol and symbol.dimension > 0:
                                    if self.tokens[self.index + 1][0] == "[":
                                        self.index += 2
                                        idx_type = self.validate_expression()
                                        if idx_type != "num_literal":
                                            self.errors.append(
                                                f"⚠️ Semantic Error at (line {line2}, column {column2}): "
                                                f"Array index must be an integer"
                                            )
                                    else:
                                        self.errors.append(
                                            f"⚠️ Semantic Error at (line {line2}, column {column2}): "
                                            f"Array variable '{lexeme2}' must have index"
                                        )

                elif token_type == "return":
                    self.index += 1
                    expr_type = self.validate_expression()
                    type_mapping = {
                        "num_literal": "num", "deci_literal": "deci",
                        "single_literal": "single", "word_literal": "word", "bool": "bool"
                    }
                    return_type = type_mapping.get(expr_type, expr_type)
                    if return_type == "error":
                        return

                self.index += 1

        # store function in global scope
        self.symbol_table["global"][function_name] = Symbol(
            name=function_name,
            symbol_type="function",
            data_type=return_type,
            value=parameters,
            line=line,
            column=column
        )

        self.current_scope = self.scope_stack.pop()

    # ------------------------------------------------------------------ #
    #  Identifier lookup helpers
    # ------------------------------------------------------------------ #
    def _lookup(self, name):
        """Return Symbol or None without generating errors."""
        return (self.symbol_table.get(self.current_scope, {}).get(name) or
                self.symbol_table.get("global", {}).get(name))

    def _resolve_identifier(self, name, line, column):
        """Check existence; add error and return False if missing."""
        if self._lookup(name) is None:
            self.errors.append(
                f"⚠️ Semantic Error at (line {line}, column {column}): "
                f"Undeclared identifier '{name}'"
            )
            return False
        return True

    # ------------------------------------------------------------------ #
    #  Identifier statement  (assignment, function call, field access)
    # ------------------------------------------------------------------ #
    def validate_id_statement(self):
        lexeme, token_type, line, column = self.tokens[self.index]

        if not self._resolve_identifier(lexeme, line, column):
            self._skip_to_semi()
            return

        symbol = self._lookup(lexeme)

        type_mapping = {
            "num": "num_literal", "deci": "deci_literal",
            "bool": "bool", "single": "single_literal", "word": "word_literal"
        }
        assign_ops = {'=', '+=', '-=', '*=', '/=', '%=', '**='}

        # ---- array access ----
        if symbol.dimension > 0:
            if self.tokens[self.index + 1][0] == "[":
                self.index += 2
                idx_type = self.validate_expression()
                if idx_type not in ("num_literal", "user_input"):
                    self.errors.append(f"⚠️ Semantic Error at (line {line}, column {column}): Array index must be an integer")
                    return "error"
                if symbol.dimension > 1 and self.tokens[self.index + 1][0] == "[":
                    self.index += 1
                    idx_type = self.validate_expression()
                    if idx_type not in ("num_literal", "user_input"):
                        self.errors.append(f"⚠️ Semantic Error at (line {line}, column {column}): Array index must be an integer")
                        return "error"
                    if self.tokens[self.index][0] != "]":
                        self.errors.append(f"⚠️ Semantic Error at (line {line}, column {column}): Missing closing bracket ']'")
                        return "error"
                    self.index += 1
                else:
                    if self.tokens[self.index][0] != "]":
                        self.errors.append(f"⚠️ Semantic Error at (line {line}, column {column}): Missing closing bracket ']'")
                        return "error"
                    self.index += 1
                target_type = symbol.data_type

            else:
                self.errors.append(f"⚠️ Semantic Error at (line {line}, column {column}): Array variable '{lexeme}' must have index")
                return "error"

        # ---- const guard ----
        elif symbol.is_const:
            self.errors.append(
                f"⚠️ Semantic Error at (line {line}, column {column}): "
                f"'{lexeme}' Cannot assign value to const variable"
            )
            return "error"

        # ---- function call ----
        elif symbol.symbol_type == "function":
            self.index += 1
            if self.tokens[self.index][0] == "(":
                self.index += 1
                expected_params = symbol.value
                received_params = []
                if self.tokens[self.index][0] == ")":
                    self.index += 1
                else:
                    while self.index < len(self.tokens):
                        pt = self.validate_expression(entered_param=True)
                        received_params.append(pt)
                        cur = self.tokens[self.index][0]
                        if cur == ")":
                            break
                        elif cur == ",":
                            self.index += 1
                        else:
                            break
                self._check_params(lexeme, expected_params, received_params, line, column)
                if self.index < len(self.tokens) and self.tokens[self.index][0] == ";":
                    self.index += 1
                return symbol.data_type
            else:
                self.errors.append(f"⚠️ Semantic Error at (line {line}, column {column}): Expected '(argument/s)' after function name '{lexeme}'")
                return "error"

        # ---- struct variable ----
        elif symbol.symbol_type == "struct_variable":
            struct_type = symbol.data_type
            self.index += 1
            if self.tokens[self.index][0] != ".":
                self.errors.append(f"⚠️ Semantic Error at (line {line}, column {column}): Expected '.' after struct variable.")
                return "error"
            self.index += 1
            field_name, _, fl, fc = self.tokens[self.index]
            if struct_type not in self.struct_table:
                self.errors.append(f"⚠️ Semantic Error at (line {line}, column {column}): Struct type '{struct_type}' is not declared.")
                return "error"
            field_type = None
            for fname, ftype in self.struct_table[struct_type]:
                if fname == field_name:
                    field_type = ftype
                    break
            if field_type is None:
                self.errors.append(f"⚠️ Semantic Error at (line {fl}, column {fc}): Field '{field_name}' not found in struct '{struct_type}'.")
                return "error"
            self.index += 1
            target_type = field_type

        else:
            target_type = symbol.data_type

        # ---- assignment ----
        if symbol.symbol_type != "function":
            if self.tokens[self.index][0] == "=":
                self.index += 1
                value_type = self.validate_expression()
                if symbol.symbol_type == "struct_variable":
                    if self._struct_field_type_mismatch(target_type, value_type, field_name, fl, fc):
                        return
                else:
                    if self.is_type_mismatch(target_type, value_type, lexeme, line, column):
                        return

            elif self.tokens[self.index][0] in assign_ops:
                op = self.tokens[self.index][0]
                if target_type == "single" and op != "+=":
                    self.errors.append(f"⚠️ Semantic Error at (line {line}, column {column}): Cannot use '{op}' on single_literal.")
                    return "error"
                self.index += 1
                value_type = self.validate_expression()
                if symbol.symbol_type == "struct_variable":
                    if self._struct_field_type_mismatch(target_type, value_type, field_name, fl, fc):
                        return
                else:
                    if self.is_type_mismatch(target_type, value_type, lexeme, line, column):
                        return

            # in() input assignment
            elif self.tokens[self.index][0] == "in":
                self.index += 2  # past 'in' and '('
                self.index += 1  # past ')'

    def _struct_field_type_mismatch(self, data_type, value_type, field_name, line, column):
        if value_type == "user_input":
            return False
        type_mapping = {
            "num_literal": "num", "deci_literal": "deci",
            "single_literal": "single", "word_literal": "word", "bool": "bool"
        }
        base_val = type_mapping.get(value_type, value_type)
        if data_type != base_val:
            numeric = ["num", "deci"]
            if not (data_type in numeric and base_val in numeric):
                self.errors.append(
                    f"⚠️ Semantic Error at (line {line}, column {column}): "
                    f"Type mismatch for struct field '{field_name}': "
                    f"Expected '{data_type}', got '{value_type}'."
                )
                return True
        return False

    def _check_params(self, func_name, expected, received, line, column):
        type_mapping = {
            "num": "num_literal", "deci": "deci_literal",
            "bool": "bool", "single": "single_literal", "word": "word_literal"
        }
        if len(received) != len(expected):
            self.errors.append(
                f"⚠️ Semantic Error at (line {line}, column {column}): "
                f"Function call '{func_name}' expects {len(expected)} argument(s), "
                f"but got {len(received)}."
            )
            return
        numeric_types = ["num_literal", "deci_literal", "bool"]
        for i, ((ename, etype), rtype) in enumerate(zip(expected, received)):
            expected_mapped = type_mapping.get(etype, etype)
            if expected_mapped != rtype and rtype != "user_input":
                if not (expected_mapped in numeric_types and rtype in numeric_types):
                    self.errors.append(
                        f"⚠️ Semantic Error at (line {line}, column {column}): "
                        f"Argument type mismatch in '{func_name}' at position {i+1}: "
                        f"Expected '{etype}', got '{rtype}'."
                    )

    # ------------------------------------------------------------------ #
    #  Expression validator  (operator-precedence / shunting-yard)
    # ------------------------------------------------------------------ #
    def validate_expression(self, entered_param=False):
        start_index = self.index

        operands_set = {"num_literal", "deci_literal", "true", "false",
                        "single_literal", "word_literal", "identifier"}
        operators_set = {"+", "-", "*", "/", "%", "**", "!",
                         "==", "!=", "<", ">", "<=", ">=", "||", "&&",
                         "is", "isnot"}

        precedence = {
            "!": 1,
            "*": 2, "/": 2, "%": 2,
            "+": 3, "-": 3,
            "<": 4, ">": 4, "<=": 4, ">=": 4,
            "==": 5, "!=": 5,
            "is": 6, "isnot": 6,
            "&&": 7,
            "||": 8,
        }
        boolean_operators = {"==", "!=", "<", ">", "<=", ">=", "&&", "||", "is", "isnot", "!"}

        type_compat = {
            "+": {
                ("num_literal", "num_literal"): "num_literal",
                ("num_literal", "deci_literal"): "num_literal",
                ("deci_literal", "num_literal"): "num_literal",
                ("deci_literal", "deci_literal"): "num_literal",
                ("bool", "bool"): "num_literal",
                ("bool", "num_literal"): "num_literal",
                ("num_literal", "bool"): "num_literal",
                ("bool", "deci_literal"): "num_literal",
                ("deci_literal", "bool"): "num_literal",
                ("word_literal", "word_literal"): "word_literal",
                ("user_input", "num_literal"): "num_literal",
                ("num_literal", "user_input"): "num_literal",
                ("user_input", "deci_literal"): "deci_literal",
                ("deci_literal", "user_input"): "deci_literal",
                ("user_input", "word_literal"): "word_literal",
                ("word_literal", "user_input"): "word_literal",
                ("user_input", "bool"): "num_literal",
                ("bool", "user_input"): "num_literal",
                ("user_input", "user_input"): "user_input",
            },
        }
        # Copy arithmetic pattern to -, *, /, %, **
        arith_base = {
            ("num_literal", "num_literal"): "num_literal",
            ("num_literal", "deci_literal"): "num_literal",
            ("deci_literal", "num_literal"): "num_literal",
            ("deci_literal", "deci_literal"): "num_literal",
            ("bool", "bool"): "num_literal",
            ("bool", "num_literal"): "num_literal",
            ("num_literal", "bool"): "num_literal",
            ("bool", "deci_literal"): "num_literal",
            ("deci_literal", "bool"): "num_literal",
            ("user_input", "num_literal"): "num_literal",
            ("num_literal", "user_input"): "num_literal",
            ("user_input", "deci_literal"): "deci_literal",
            ("deci_literal", "user_input"): "deci_literal",
            ("user_input", "bool"): "num_literal",
            ("bool", "user_input"): "num_literal",
            ("user_input", "user_input"): "user_input",
        }
        for op in ("-", "*", "/", "%", "**"):
            type_compat[op] = dict(arith_base)

        def evaluate_op(op, left, right=None):
            if op in boolean_operators:
                if left == "user_input" or (right and right == "user_input"):
                    return "bool"
                if op == "!":
                    if left in ("bool", "num_literal", "deci_literal", "user_input"):
                        return "bool"
                    return "error"
                if op in ("==", "!="):
                    all_types = {"num_literal", "deci_literal", "bool",
                                 "user_input", "word_literal", "single_literal"}
                    if left == right or (left in all_types and right in all_types):
                        return "bool"
                    return "error"
                if op in ("<", ">", "<=", ">="):
                    numeric = {"num_literal", "deci_literal", "bool", "user_input"}
                    if left in numeric and right in numeric:
                        return "bool"
                    return "error"
                if op in ("&&", "||"):
                    if left in ("bool", "user_input") and right in ("bool", "user_input"):
                        return "bool"
                    return "error"
                if op in ("is", "isnot"):
                    return "bool"
            else:
                if op in type_compat:
                    if left == "user_input" or right == "user_input":
                        if left == "user_input" and right == "user_input":
                            return "user_input"
                        return right if left == "user_input" else left
                    return type_compat[op].get((left, right), "error")
            return "error"

        operand_stack = []
        operator_stack = []

        def apply_operator():
            if not operator_stack:
                return
            op = operator_stack.pop()
            if op == "!":
                if not operand_stack:
                    return
                operand = operand_stack.pop()
                result = evaluate_op(op, operand)
                if result == "error":
                    self.errors.append(f"⚠️ Semantic Error at (line {line}): Cannot apply '!' to {operand}")
                operand_stack.append(result)
            else:
                if len(operand_stack) < 2:
                    return
                right = operand_stack.pop()
                left = operand_stack.pop()
                result = evaluate_op(op, left, right)
                if result == "error":
                    self.errors.append(
                        f"⚠️ Semantic Error at (line {line}): "
                        f"Type mismatch '{op}' not supported between '{left}' and '{right}'"
                    )
                operand_stack.append(result)

        if self.index >= len(self.tokens) or self.tokens[self.index][1] in {";", ","}:
            if entered_param:
                return "word_literal"
            return "error"

        type_mapping = {
            "num": "num_literal", "deci": "deci_literal",
            "bool": "bool", "single": "single_literal", "word": "word_literal"
        }

        while self.index < len(self.tokens):
            lexeme, token_type, line, column = self.tokens[self.index]

            # ---- in() input ----
            if lexeme == "in":
                self.index += 1  # to '('
                self.index += 1  # to ')'
                self.index += 1  # past ')'
                operand_stack.append("user_input")
                continue

            # ---- identifier ----
            elif token_type == "identifier":
                symbol = self._lookup(lexeme)
                if symbol is None:
                    self.errors.append(
                        f"⚠️ Semantic Error at (line {line}, column {column}): "
                        f"Undeclared identifier '{lexeme}'"
                    )
                    self._skip_to_semi()
                    return "error"

                if self.index + 1 < len(self.tokens) and self.tokens[self.index + 1][0] == "[":
                    if symbol.dimension == 0 and symbol.data_type != "word":
                        self.errors.append(
                            f"⚠️ Semantic Error at (line {line}, column {column}): "
                            f"Variable '{lexeme}' is not an array"
                        )
                        return "error"

                if symbol.dimension > 0 or symbol.data_type == "word":
                    self.index += 1
                    if self.index < len(self.tokens) and self.tokens[self.index][0] == "[":
                        self.index += 1
                        idx_type = self.validate_expression()
                        if idx_type not in ("num_literal", "user_input"):
                            self.errors.append(f"⚠️ Semantic Error at (line {line}, column {column}): Array index must be an integer")
                            return "error"
                        if self.index < len(self.tokens) and self.tokens[self.index][0] == "]":
                            self.index += 1
                        if symbol.dimension > 1 and self.index < len(self.tokens) and self.tokens[self.index][0] == "[":
                            self.index += 1
                            idx_type = self.validate_expression()
                            if idx_type not in ("num_literal", "user_input"):
                                self.errors.append(f"⚠️ Semantic Error at (line {line}, column {column}): Array index must be an integer")
                                return "error"
                            if self.index < len(self.tokens) and self.tokens[self.index][0] == "]":
                                self.index += 1
                        if symbol.data_type == "word":
                            operand_stack.append("single_literal")
                        else:
                            operand_stack.append(type_mapping.get(symbol.data_type, symbol.data_type))
                    else:
                        if symbol.dimension > 0:
                            self.errors.append(f"⚠️ Semantic Error at (line {line}, column {column}): Array variable '{lexeme}' must have index")
                            return "error"
                        operand_stack.append(symbol.data_type)

                elif symbol.symbol_type == "function":
                    self.index += 1
                    if self.tokens[self.index][0] == "(":
                        self.index += 1
                        expected_params = symbol.value
                        received_params = []
                        if self.tokens[self.index][0] == ")":
                            self.index += 1
                            operand_stack.append(type_mapping.get(symbol.data_type, symbol.data_type))
                        else:
                            while self.index < len(self.tokens):
                                pt = self.validate_expression(entered_param=True)
                                received_params.append(pt)
                                cur = self.tokens[self.index][0]
                                if cur == ")":
                                    self.index += 1
                                    break
                                elif cur == ",":
                                    self.index += 1
                                else:
                                    break
                        self._check_params(lexeme, expected_params, received_params, line, column)
                        operand_stack.append(type_mapping.get(symbol.data_type, symbol.data_type))
                    else:
                        self.errors.append(f"⚠️ Semantic Error at (line {line}, column {column}): Expected '(' after function name '{lexeme}'")
                        return "error"

                elif symbol.symbol_type == "struct_variable":
                    struct_type = symbol.data_type
                    self.index += 1
                    if self.index < len(self.tokens) and self.tokens[self.index][0] != ".":
                        self.errors.append(f"⚠️ Semantic Error at (line {line}, column {column}): Expected '.' after struct variable.")
                        return "error"
                    self.index += 1
                    field_name2, _, fl2, fc2 = self.tokens[self.index]
                    if struct_type not in self.struct_table:
                        self.errors.append(f"⚠️ Semantic Error at (line {line}, column {column}): Struct type '{struct_type}' is not declared.")
                        return "error"
                    ftype2 = None
                    for fn, ft in self.struct_table[struct_type]:
                        if fn == field_name2:
                            ftype2 = ft
                            break
                    if ftype2 is None:
                        self.errors.append(f"⚠️ Semantic Error at (line {fl2}, column {fc2}): Field '{field_name2}' not found in struct '{struct_type}'.")
                        return "error"
                    self.index += 1
                    operand_stack.append(type_mapping.get(ftype2, ftype2))

                else:
                    operand_stack.append(type_mapping.get(symbol.data_type, symbol.data_type))
                    self.index += 1

            elif token_type in {"num_literal", "deci_literal", "single_literal", "word_literal"}:
                operand_stack.append(token_type)
                self.index += 1

            elif token_type in ("true", "false"):
                operand_stack.append("bool")
                self.index += 1

            elif token_type == "(":
                operator_stack.append("(")
                self.index += 1

            elif token_type == ")":
                while operator_stack and operator_stack[-1] != "(":
                    apply_operator()
                if operator_stack and operator_stack[-1] == "(":
                    operator_stack.pop()
                    self.index += 1
                elif entered_param:
                    break
                else:
                    self.errors.append(f"⚠️ Semantic Error at (line {line}, column {column}): Mismatched parentheses")
                    return "error"

            elif token_type == "]":
                while operator_stack and operator_stack[-1] not in ("(", "["):
                    apply_operator()
                if not entered_param:
                    break

            elif lexeme in operators_set:
                if lexeme == "!" and (
                    self.index == start_index or
                    self.tokens[self.index - 1][1] in operators_set or
                    self.tokens[self.index - 1][1] == "("
                ):
                    while operator_stack and operator_stack[-1] != "(" and \
                            precedence.get(operator_stack[-1], 999) <= precedence[lexeme]:
                        apply_operator()
                    operator_stack.append(lexeme)
                else:
                    while (operator_stack and operator_stack[-1] != "(" and
                           precedence.get(operator_stack[-1], 999) <= precedence.get(lexeme, 999)):
                        apply_operator()
                    operator_stack.append(lexeme)
                self.index += 1

            elif token_type in {";", ",", "{"}:
                break

            else:
                self.index += 1

        while operator_stack:
            op = operator_stack[-1]
            if op == "(":
                operator_stack.pop()
                continue
            apply_operator()

        if not operand_stack:
            self.errors.append("⚠️ Expression evaluation error occurred")
            return "error"

        return operand_stack[-1]

    # ------------------------------------------------------------------ #
    #  Print helpers
    # ------------------------------------------------------------------ #
    def print_symbol_table(self):
        print("\n========== Symbol Table ==========")
        for scope, symbols in self.symbol_table.items():
            print(f"\nScope: {scope}")
            for name, symbol in symbols.items():
                print(f"  {symbol}")
        print("\n========== Struct Table ==========")
        for sname, fields in self.struct_table.items():
            print(f"\nStruct: {sname}")
            for fname, ftype in fields:
                print(f"  - {fname}: {ftype}")

    def print_errors(self):
        if not self.errors:
            print("\n✅ No Semantic Errors Found.")
        else:
            print("\n⚠️ Semantic Errors:")
            for error in self.errors:
                print(error)