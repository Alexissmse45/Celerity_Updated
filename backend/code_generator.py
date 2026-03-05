class CodeGenerator:
    def __init__(self):
        self.output_code = []           # Stores all generated lines of C code
        self.indentation = 0            # Current indentation level
        self.variable_types = {}        # Tracks variable types per scope: {scope: {name: lang_type}}
        self.struct_definitions = {}    # Tracks struct field types: {struct_name: {field: lang_type}}
        self.current_scope = "global"   # Tracks which function scope we are currently inside
        self.debug_mode = True          # Toggle debug printing on/off

    def add_line(self, line):
        """Append one line with proper indentation to output_code."""
        self.output_code.append('    ' * self.indentation + line)

    def debug(self, message):
        """Print debug message if debug_mode is enabled."""
        if self.debug_mode:
            print(f"CODE_GEN DEBUG: {message}")

    def generate_code(self, tokens):
        """Main entry point. Receives token list, returns generated C code as string."""
        self.output_code = []
        self.variable_types = {"global": {}}    # Always start with global scope

        # Debug: print first 20 tokens to help trace issues
        if self.debug_mode:
            self.debug(f"Processing {len(tokens)} tokens")
            for i, token in enumerate(tokens[:20]):
                self.debug(f"Token {i}: {token}")

        self._process_tokens(tokens)
        return '\n'.join(self.output_code)

    def _process_tokens(self, tokens):
        """
        Top-level token processing loop.
        Emits C headers, helper functions, then processes
        global declarations and function definitions in order.
        """
        # --- Emit required C headers ---
        self.add_line("#include <stdio.h>")
        self.add_line("#include <stdlib.h>")
        self.add_line("#include <string.h>")
        self.add_line("#include <stdbool.h>")   # Needed for bool type
        self.add_line("#include <math.h>")       # Needed for pow() used by **
        self.add_line("#ifdef _WIN32")
        self.add_line("#include <windows.h>")    # Windows sleep support
        self.add_line("#else")
        self.add_line("#include <unistd.h>")
        self.add_line("#endif")
        self.add_line("#include <ctype.h>")
        self.add_line("")

        # --- Emit runtime helper functions ---
        self._add_helper_functions()
        self._add_input_functions()

        # --- Main pass: process global declarations and function definitions ---
        i = 0
        while i < len(tokens):

            # struct type definition:  struct Name { ... }
            if (tokens[i][1] == 'struct'
                    and i + 2 < len(tokens)
                    and tokens[i + 2][0] == '{'):
                self.debug(f"Found struct declaration at index {i}")
                i = self._process_struct_declaration(tokens, i)
                continue

            # Global variable declarations: num, deci, word, single, bool
            if self._is_variable_declaration(tokens, i) and self.current_scope == "global":
                i = self._process_variable_declaration(tokens, i)
                continue

            # Global const declaration: const num X = 5;
            if tokens[i][1] == 'const' and self.current_scope == "global":
                i = self._process_const_declaration(tokens, i)
                continue

            # function / vacant / main definitions
            if self._is_function_declaration(tokens, i):
                i = self._process_function(tokens, i)
                continue

            i += 1

    # ------------------------------------------------------------------ #
    #  Helper function emission
    # ------------------------------------------------------------------ #

    def _add_helper_functions(self):
        """Emit utility C functions used by the generated code."""

        # --- int_to_str: converts integer to heap-allocated C string ---
        self.add_line("// Converts integer to a heap-allocated string")
        self.add_line("char* int_to_str(int value) {")
        self.indentation += 1
        self.add_line("char* buffer = malloc(32);")
        self.add_line("sprintf(buffer, \"%d\", value);")
        self.add_line("return buffer;")
        self.indentation -= 1
        self.add_line("}")
        self.add_line("")

        # --- concat_str: concatenates two C strings into a new allocation ---
        self.add_line("// Concatenates two strings into a new heap-allocated string")
        self.add_line("char* concat_str(const char* str1, const char* str2) {")
        self.indentation += 1
        self.add_line("char* result = malloc(strlen(str1) + strlen(str2) + 1);")
        self.add_line("strcpy(result, str1);")
        self.add_line("strcat(result, str2);")
        self.add_line("return result;")
        self.indentation -= 1
        self.add_line("}")
        self.add_line("")

        # --- concat_str_int: concatenates a string with an integer ---
        self.add_line("// Concatenates a string with an integer value")
        self.add_line("char* concat_str_int(const char* str, int value) {")
        self.indentation += 1
        self.add_line("char* int_str = int_to_str(value);")
        self.add_line("char* result = concat_str(str, int_str);")
        self.add_line("free(int_str);")        # Free temporary int string after use
        self.add_line("return result;")
        self.indentation -= 1
        self.add_line("}")
        self.add_line("")

    def _add_input_functions(self):
        """
        Emit read_* helper functions for in() input.
        Each function waits for input, validates it, and returns the correct C type.
        Language keyword: in()
        Maps to: read_int(), read_double(), read_char(), read_word(), read_bool()
        """

        # --- read_int: reads and validates integer input ---
        # Language type: num  →  C type: int
        self.add_line("// Reads a validated integer from stdin (language type: num)")
        self.add_line("int read_int() {")
        self.indentation += 1
        self.add_line("int value = 0;")
        self.add_line("int valid_input = 0;")
        self.add_line("char buffer[1024];")
        self.add_line("")
        self.add_line("while (!valid_input) {")
        self.indentation += 1
        self.add_line("printf(\"_waiting_for_input|\\n\");")   # Signal GUI that input is needed
        self.add_line("fflush(stdout);")
        self.add_line("")
        self.add_line("if (fgets(buffer, sizeof(buffer), stdin) == NULL) {")
        self.indentation += 1
        self.add_line("printf(\"...\\n\");")
        self.add_line("continue;")
        self.indentation -= 1
        self.add_line("}")
        self.add_line("")
        self.add_line("// Treat leading '~' as negative sign (language uses ~ for negatives)")
        self.add_line("if (buffer[0] == '~') buffer[0] = '-';")
        self.add_line("")
        self.add_line("// Validate that the entire buffer is a proper integer")
        self.add_line("char* endptr;")
        self.add_line("value = (int)strtol(buffer, &endptr, 10);")
        self.add_line("if (*endptr != '\\n' && *endptr != '\\0') {")
        self.indentation += 1
        self.add_line("printf(\"Invalid input. Please enter a valid integer.\\n\");")
        self.add_line("fflush(stdout);")
        self.indentation -= 1
        self.add_line("} else {")
        self.indentation += 1
        self.add_line("valid_input = 1;")
        self.indentation -= 1
        self.add_line("}")
        self.indentation -= 1
        self.add_line("}")
        self.add_line("return value;")
        self.indentation -= 1
        self.add_line("}")
        self.add_line("")

        # --- read_double: reads and validates decimal input ---
        # Language type: deci  →  C type: double
        self.add_line("// Reads a validated decimal from stdin (language type: deci)")
        self.add_line("double read_double() {")
        self.indentation += 1
        self.add_line("double value = 0.0;")
        self.add_line("int valid_input = 0;")
        self.add_line("char buffer[1024];")
        self.add_line("")
        self.add_line("while (!valid_input) {")
        self.indentation += 1
        self.add_line("printf(\"_waiting_for_input|\\n\");")
        self.add_line("fflush(stdout);")
        self.add_line("")
        self.add_line("if (fgets(buffer, sizeof(buffer), stdin) == NULL) {")
        self.indentation += 1
        self.add_line("printf(\"...\\n\");")
        self.add_line("continue;")
        self.indentation -= 1
        self.add_line("}")
        self.add_line("")
        self.add_line("// Treat leading '~' as negative sign")
        self.add_line("if (buffer[0] == '~') buffer[0] = '-';")
        self.add_line("")
        self.add_line("// Validate that the entire buffer is a proper decimal")
        self.add_line("char* endptr;")
        self.add_line("value = strtod(buffer, &endptr);")
        self.add_line("if (*endptr != '\\n' && *endptr != '\\0') {")
        self.indentation += 1
        self.add_line("printf(\"Invalid input. Please enter a valid decimal.\\n\");")
        self.add_line("fflush(stdout);")
        self.indentation -= 1
        self.add_line("} else {")
        self.indentation += 1
        self.add_line("valid_input = 1;")
        self.indentation -= 1
        self.add_line("}")
        self.indentation -= 1
        self.add_line("}")
        self.add_line("return value;")
        self.indentation -= 1
        self.add_line("}")
        self.add_line("")

        # --- read_char: reads a single character ---
        # Language type: single  →  C type: char
        self.add_line("// Reads a single validated character from stdin (language type: single)")
        self.add_line("char read_char() {")
        self.indentation += 1
        self.add_line("char value = '\\0';")
        self.add_line("int valid_input = 0;")
        self.add_line("char buffer[1024];")
        self.add_line("")
        self.add_line("while (!valid_input) {")
        self.indentation += 1
        self.add_line("printf(\"_waiting_for_input|\\n\");")
        self.add_line("fflush(stdout);")
        self.add_line("")
        self.add_line("if (fgets(buffer, sizeof(buffer), stdin) == NULL) {")
        self.indentation += 1
        self.add_line("printf(\"...\\n\");")
        self.add_line("continue;")
        self.indentation -= 1
        self.add_line("}")
        self.add_line("")
        self.add_line("// Count non-whitespace characters; exactly one is valid input")
        self.add_line("size_t len = strlen(buffer);")
        self.add_line("int char_count = 0;")
        self.add_line("for (size_t i = 0; i < len; i++) {")
        self.indentation += 1
        self.add_line("if (buffer[i] != ' ' && buffer[i] != '\\t' && buffer[i] != '\\n') {")
        self.indentation += 1
        self.add_line("value = buffer[i];")
        self.add_line("char_count++;")
        self.indentation -= 1
        self.add_line("}")
        self.indentation -= 1
        self.add_line("}")
        self.add_line("if (char_count != 1) {")
        self.indentation += 1
        self.add_line("printf(\"Invalid input. Please enter a single character.\\n\");")
        self.add_line("fflush(stdout);")
        self.indentation -= 1
        self.add_line("} else {")
        self.indentation += 1
        self.add_line("valid_input = 1;")
        self.indentation -= 1
        self.add_line("}")
        self.indentation -= 1
        self.add_line("}")
        self.add_line("return value;")
        self.indentation -= 1
        self.add_line("}")
        self.add_line("")

        # --- read_word: reads a non-empty string ---
        # Language type: word  →  C type: char*
        self.add_line("// Reads a non-empty string from stdin (language type: word)")
        self.add_line("char* read_word() {")
        self.indentation += 1
        self.add_line("char buffer[1024];")
        self.add_line("int valid_input = 0;")
        self.add_line("")
        self.add_line("while (!valid_input) {")
        self.indentation += 1
        self.add_line("printf(\"_waiting_for_input|\\n\");")
        self.add_line("fflush(stdout);")
        self.add_line("")
        self.add_line("if (fgets(buffer, sizeof(buffer), stdin) == NULL) {")
        self.indentation += 1
        self.add_line("printf(\"...\\n\");")
        self.add_line("continue;")
        self.indentation -= 1
        self.add_line("}")
        self.add_line("")
        self.add_line("// Strip the trailing newline character if present")
        self.add_line("size_t len = strlen(buffer);")
        self.add_line("if (len > 0 && buffer[len-1] == '\\n') buffer[len-1] = '\\0';")
        self.add_line("")
        self.add_line("// Reject blank or whitespace-only input")
        self.add_line("int is_empty = 1;")
        self.add_line("for (size_t i = 0; i < strlen(buffer); i++) {")
        self.indentation += 1
        self.add_line("if (buffer[i] != ' ' && buffer[i] != '\\t') { is_empty = 0; break; }")
        self.indentation -= 1
        self.add_line("}")
        self.add_line("if (is_empty) {")
        self.indentation += 1
        self.add_line("printf(\"Input cannot be empty.\\n\");")
        self.add_line("fflush(stdout);")
        self.indentation -= 1
        self.add_line("} else {")
        self.indentation += 1
        self.add_line("valid_input = 1;")
        self.indentation -= 1
        self.add_line("}")
        self.indentation -= 1
        self.add_line("}")
        self.add_line("return strdup(buffer);")   # Return heap copy; caller owns the memory
        self.indentation -= 1
        self.add_line("}")
        self.add_line("")

        # --- read_bool: reads true/false/yes/no/1/0 ---
        # Language type: bool  →  C type: bool
        self.add_line("// Reads a validated boolean from stdin (language type: bool)")
        self.add_line("bool read_bool() {")
        self.indentation += 1
        self.add_line("char buffer[1024];")
        self.add_line("int valid_input = 0;")
        self.add_line("bool value = false;")
        self.add_line("")
        self.add_line("while (!valid_input) {")
        self.indentation += 1
        self.add_line("printf(\"_waiting_for_input|Enter a boolean (true/false, 1/0): \\n\");")
        self.add_line("fflush(stdout);")
        self.add_line("")
        self.add_line("if (fgets(buffer, sizeof(buffer), stdin) == NULL) {")
        self.indentation += 1
        self.add_line("printf(\"...\\n\");")
        self.add_line("continue;")
        self.indentation -= 1
        self.add_line("}")
        self.add_line("")
        self.add_line("// Strip trailing newline")
        self.add_line("size_t len = strlen(buffer);")
        self.add_line("if (len > 0 && buffer[len-1] == '\\n') buffer[len-1] = '\\0';")
        self.add_line("")
        self.add_line("// Normalise to lowercase for case-insensitive comparison")
        self.add_line("for (size_t i = 0; i < strlen(buffer); i++) buffer[i] = tolower(buffer[i]);")
        self.add_line("")
        self.add_line("// Accept true/1/yes/y as true")
        self.add_line("if (strcmp(buffer,\"true\")==0 || strcmp(buffer,\"1\")==0 ||")
        self.add_line("    strcmp(buffer,\"yes\")==0  || strcmp(buffer,\"y\")==0) {")
        self.indentation += 1
        self.add_line("value = true; valid_input = 1;")
        self.indentation -= 1
        self.add_line("// Accept false/0/no/n as false")
        self.add_line("} else if (strcmp(buffer,\"false\")==0 || strcmp(buffer,\"0\")==0 ||")
        self.add_line("           strcmp(buffer,\"no\")==0    || strcmp(buffer,\"n\")==0) {")
        self.indentation += 1
        self.add_line("value = false; valid_input = 1;")
        self.indentation -= 1
        self.add_line("} else {")
        self.indentation += 1
        self.add_line("printf(\"Invalid. Enter true/false or 1/0.\\n\");")
        self.add_line("fflush(stdout);")
        self.indentation -= 1
        self.add_line("}")
        self.indentation -= 1
        self.add_line("}")
        self.add_line("return value;")
        self.indentation -= 1
        self.add_line("}")
        self.add_line("")

    # ------------------------------------------------------------------ #
    #  Detection helpers  (mirror reference _is_* methods exactly)
    # ------------------------------------------------------------------ #

    def _is_function_declaration(self, tokens, index):
        """
        Check whether tokens at index start a function definition.
        Language keywords:
          function → named function that returns a value   (ref: task)
          vacant   → named function that returns nothing   (ref: empty)
          main     → program entry point
        """
        if index >= len(tokens):
            return False

        tok = tokens[index]

        # 'main' followed by '(' is the entry point
        if tok[1] == 'main':
            if index + 1 < len(tokens) and tokens[index + 1][0] == '(':
                self.debug("Main function detected: main()")
                return True

        # 'function' or 'vacant' followed by identifier then '('
        elif tok[1] in ('function', 'vacant'):
            if (index + 2 < len(tokens)
                    and tokens[index + 1][1] == 'identifier'
                    and tokens[index + 2][0] == '('):
                self.debug(f"Function detected: {tok[0]} {tokens[index+1][0]}()")
                return True

        return False

    def _is_struct_declaration(self, tokens, index):
        """
        Check whether tokens at index start a struct type definition.
        Language keyword: struct Name { ... }
        Maps to C:        struct Name { ... };
        """
        if index + 2 < len(tokens):
            if (tokens[index][1] == 'struct'
                    and tokens[index + 1][1] == 'identifier'
                    and tokens[index + 2][0] == '{'):
                return True
        return False

    def _is_variable_declaration(self, tokens, index):
        """
        Check if tokens at index start a variable declaration.
        Language primitive types: num, deci, word, single, bool
        Also covers struct instance:  struct Name varname
        """
        if index < len(tokens):
            # Primitive type keywords
            if tokens[index][1] in ('num', 'deci', 'word', 'single', 'bool'):
                return True
            # Struct instance: 'struct' followed by an identifier (struct type name)
            if (tokens[index][1] == 'struct'
                    and index + 1 < len(tokens)
                    and tokens[index + 1][1] == 'identifier'):
                return True
        return False

    def _is_increment_decrement(self, tokens, index):
        """
        Detect post-increment/post-decrement (id++ / id--)
        and pre-increment/pre-decrement (++id / --id).
        Language operators: ++ and --  (same as C)
        """
        inc_dec = ['++', '--']
        if index < len(tokens):
            # Post form: identifier followed by ++ or --
            if (tokens[index][1] == 'identifier'
                    and index + 1 < len(tokens)
                    and tokens[index + 1][0] in inc_dec):
                return True
            # Pre form: ++ or -- followed by identifier
            if (tokens[index][0] in inc_dec
                    and index + 1 < len(tokens)
                    and tokens[index + 1][1] == 'identifier'):
                return True
        return False

    def _is_assignment(self, tokens, index):
        """
        Detect assignment and compound-assignment statements.
        Covers: var = expr, var += expr, var[i] = expr, var.field = expr
        Language operators: = += -= *= /= %= **=
        Note: **= (exponentiation assign) has no C equivalent; uses pow().
        """
        assignment_ops = ['=', '+=', '-=', '*=', '/=', '%=', '**=']
        if index + 2 < len(tokens):
            # Simple: identifier directly followed by an assignment operator
            if (tokens[index][1] == 'identifier'
                    and tokens[index + 1][0] in assignment_ops):
                return True
            # Array: identifier then '[', then closing ']', then assignment operator
            if (tokens[index][1] == 'identifier'
                    and tokens[index + 1][0] == '['):
                j = index + 2
                brackets = 1
                while j < len(tokens) and brackets > 0:
                    if tokens[j][0] == '[':
                        brackets += 1
                    elif tokens[j][0] == ']':
                        brackets -= 1
                    j += 1
                if j < len(tokens) and tokens[j][0] in assignment_ops:
                    return True
            # Struct member: identifier then '.' then field name then assignment operator
            if (tokens[index][1] == 'identifier'
                    and tokens[index + 1][0] == '.'
                    and index + 3 < len(tokens)
                    and tokens[index + 3][0] in assignment_ops):
                return True
        return False

    def _is_out_statement(self, tokens, index):
        """
        Detect out(...) output statement.
        Language keyword: out  (ref: display)
        Maps to C: printf(...)
        """
        return index < len(tokens) and tokens[index][1] == 'out'

    def _is_if_statement(self, tokens, index):
        """Detect if statement. Language keyword: if"""
        return index < len(tokens) and tokens[index][1] == 'if'

    def _is_match_statement(self, tokens, index):
        """
        Detect match statement (switch equivalent).
        Language keyword: match  (ref: select)
        Maps to C: switch
        """
        return index < len(tokens) and tokens[index][1] == 'match'

    def _is_loop_statement(self, tokens, index):
        """
        Detect loop statements.
        Language keywords: while, for, do (do-while)
        """
        return index < len(tokens) and tokens[index][1] in ('while', 'for', 'do')

    def _is_function_call(self, tokens, index):
        """Detect a standalone function call statement: identifier(...)"""
        if index + 1 < len(tokens):
            if (tokens[index][1] == 'identifier'
                    and tokens[index + 1][0] == '('):
                self.debug(f"Function call detected: {tokens[index][0]}()")
                return True
        return False

    # ------------------------------------------------------------------ #
    #  Type mapping helpers
    # ------------------------------------------------------------------ #

    def _map_datatype(self, lang_type):
        """
        Map language type names to C type names.
          num    → int
          deci   → double
          word   → char*   (strings use heap-allocated C strings)
          single → char    (single character)
          bool   → bool    (from <stdbool.h>)
          vacant → void    (functions with no return value)
        """
        mapping = {
            'num':    'int',
            'deci':   'double',
            'word':   'char*',
            'single': 'char',
            'bool':   'bool',
            'vacant': 'void',
        }
        return mapping.get(lang_type, lang_type)   # Return as-is if not in mapping

    def _get_default_value(self, lang_type):
        """
        Return a safe default C initialiser for the given language type.
        Used when a variable is declared without an explicit initial value.
        """
        defaults = {
            'num':    '0',
            'deci':   '0.0',
            'word':   '""',
            'single': "' '",
            'bool':   'false',
            # Already-mapped C types (for internal reuse)
            'int':    '0',
            'double': '0.0',
            'char*':  '""',
            'char':   "' '",
        }
        return defaults.get(lang_type, '0')

    def _get_variable_type(self, var_name):
        """
        Look up a variable's language type.
        Checks current function scope first, then falls back to global scope.
        Returns None if the variable is not found in either scope.
        """
        # Check current scope first (local variables shadow globals)
        if var_name in self.variable_types.get(self.current_scope, {}):
            return self.variable_types[self.current_scope][var_name]
        # Fall back to global scope
        if var_name in self.variable_types.get("global", {}):
            return self.variable_types["global"][var_name]
        return None

    def _read_function_for_type(self, lang_type):
        """
        Return the correct read_* helper name for a given language type.
        Used when translating in() input calls to the appropriate C function.
          num    → read_int()
          deci   → read_double()
          single → read_char()
          word   → read_word()
          bool   → read_bool()
        """
        return {
            'num':    'read_int',
            'deci':   'read_double',
            'single': 'read_char',
            'word':   'read_word',
            'bool':   'read_bool',
        }.get(lang_type, 'read_word')   # Default to read_word for unknown types

    # ------------------------------------------------------------------ #
    #  Struct type declaration  →  struct Name { fields }
    # ------------------------------------------------------------------ #

    def _process_struct_declaration(self, tokens, index):
        """
        Translate:  struct Name { type field; ... }
        Into C:     struct Name { c_type field; ... };
        Also stores field types in self.struct_definitions for type-aware output later.
        Language keyword: struct  (same as C)
        """
        struct_name = tokens[index + 1][0]   # Name identifier after 'struct'
        self.debug(f"Processing struct declaration: {struct_name}")

        brace_index = index + 2              # Index of opening '{'
        end_index = self._find_matching_brace(tokens, brace_index)
        if end_index == -1:
            self.debug("Missing closing brace for struct")
            return index + 1

        self.add_line(f"struct {struct_name} {{")
        self.indentation += 1

        # Register this struct so we can look up field types later
        self.struct_definitions[struct_name] = {}

        i = brace_index + 1
        while i < end_index:
            # Each field starts with a language type keyword
            if tokens[i][1] in ('num', 'deci', 'word', 'single', 'bool'):
                field_lang_type = tokens[i][0]                        # e.g. 'num'
                field_c_type    = self._map_datatype(field_lang_type)  # e.g. 'int'

                if i + 1 < end_index and tokens[i + 1][1] == 'identifier':
                    field_name = tokens[i + 1][0]
                    self.add_line(f"{field_c_type} {field_name};")    # Emit C field declaration

                    # Store field type so _process_out and _process_assignment can use it
                    self.struct_definitions[struct_name][field_name] = field_lang_type

                    i += 2   # Past type and name
                    while i < end_index and tokens[i][0] != ';':
                        i += 1
                    i += 1   # Past ';'
                else:
                    i += 1
            else:
                i += 1

        self.indentation -= 1
        self.add_line("};")   # C struct definitions end with ';'
        self.add_line("")

        return end_index + 1

    # ------------------------------------------------------------------ #
    #  const declaration  →  const type id = value;
    # ------------------------------------------------------------------ #

    def _process_const_declaration(self, tokens, index):
        """
        Translate:  const num X = 5;
        Into C:     const int X = 5;
        Language keyword: const  (ref: fixed)
        Supports multiple variables: const num A = 1, B = 2;
        """
        index += 1   # Past 'const'
        lang_type = tokens[index][0]          # Language type keyword, e.g. 'num'
        c_type    = self._map_datatype(lang_type)

        parts = []
        while True:
            index += 1   # Move to variable name
            var_name = tokens[index][0]

            # Register variable in current scope's type table
            if self.current_scope not in self.variable_types:
                self.variable_types[self.current_scope] = {}
            self.variable_types[self.current_scope][var_name] = lang_type

            index += 1   # Past name, now at '='
            index += 1   # Past '=', now at value

            value_tok = tokens[index][0]     # The literal value
            parts.append(f"{var_name} = {value_tok}")

            index += 1   # Past value, now at ',' or ';'
            if tokens[index][0] == ';':
                break    # End of declaration
            elif tokens[index][0] == ',':
                continue # More variables follow

        self.add_line(f"const {c_type} {', '.join(parts)};")
        return index + 1   # Return index after ';'

    # ------------------------------------------------------------------ #
    #  Variable declaration (scalar, array, struct instance)
    # ------------------------------------------------------------------ #

    def _process_variable_declaration(self, tokens, index):
        """
        Translate variable declarations for all language types.
        Handles:
          - Scalar:         num x = 5;
          - Array 1D:       num arr[3] = {1, 2, 3};
          - Array 2D:       num grid[2][3] = {{1,2,3},{4,5,6}};
          - Struct instance: struct Point p = {1, 2};
          - in() input:     num x = in();
          - Uninitialised:  num x;   (auto-fills with default value)

        Language types: num deci word single bool → int double char* char bool
        """
        is_const = False

        # Guard: const modifier is handled by _process_const_declaration,
        # but check here too in case dispatched differently
        if tokens[index][1] == 'const':
            is_const = True
            index += 1

        # --- Struct instance declaration: struct Name varname [= {...}]; ---
        if tokens[index][1] == 'struct' and index + 1 < len(tokens):
            return self._process_struct_variable(tokens, index)

        # --- Primitive type declaration ---
        lang_type    = tokens[index][0]              # e.g. 'num'
        c_type       = self._map_datatype(lang_type) # e.g. 'int'
        self.debug(f"Variable declaration of type: {lang_type} → {c_type}")

        declaration  = f"{'const ' if is_const else ''}{c_type} "
        variables    = []
        i = index + 1

        while i < len(tokens) and tokens[i][0] != ';':
            if tokens[i][1] != 'identifier':
                i += 1
                continue

            var_name = tokens[i][0]

            # Register variable in current scope so type lookups work later
            if self.current_scope not in self.variable_types:
                self.variable_types[self.current_scope] = {}
            self.variable_types[self.current_scope][var_name] = lang_type

            # --- Array declaration: varname[size] or varname[rows][cols] ---
            if i + 1 < len(tokens) and tokens[i + 1][0] == '[':
                dims   = []
                i += 1   # Move to first '['

                while i < len(tokens) and tokens[i][0] == '[':
                    i += 1   # Past '['
                    dim_size = ""
                    while i < len(tokens) and tokens[i][0] != ']':
                        dim_size += tokens[i][0]
                        i += 1
                    if i < len(tokens):
                        i += 1   # Past ']'
                    dims.append(dim_size)

                # Build C array declaration string: varname[d1][d2]
                var_decl = var_name + "".join(f"[{d}]" for d in dims)

                if i < len(tokens) and tokens[i][0] == '=':
                    # Initialised array: varname[n] = { v1, v2, ... }
                    i += 1   # Past '='
                    if tokens[i][0] == '{':
                        i += 1   # Past opening '{'
                        init_values = []
                        nested_level = 1
                        current_group = []

                        while i < len(tokens) and nested_level > 0:
                            if tokens[i][0] == '{':
                                nested_level += 1
                                if nested_level == 2:
                                    current_group = []   # Start collecting inner row
                                i += 1
                            elif tokens[i][0] == '}':
                                nested_level -= 1
                                if nested_level == 1:
                                    # Completed one inner row of a 2D array
                                    init_values.append(f"{{{', '.join(current_group)}}}")
                                elif nested_level == 0:
                                    i += 1
                                    break
                                i += 1
                            elif tokens[i][0] == ',':
                                i += 1   # Skip comma separator
                            else:
                                if nested_level == 2:
                                    current_group.append(tokens[i][0])   # Inner element
                                elif nested_level == 1 and len(dims) == 1:
                                    init_values.append(tokens[i][0])     # 1D element
                                i += 1

                        var_decl += f" = {{{', '.join(init_values)}}}"
                else:
                    # Uninitialised array: auto-fill with default values
                    dv = self._get_default_value(lang_type)
                    if len(dims) == 1 and dims[0].isdigit():
                        n = int(dims[0])
                        var_decl += f" = {{{', '.join([dv] * n)}}}"
                    elif (len(dims) == 2
                            and dims[0].isdigit() and dims[1].isdigit()):
                        rows = int(dims[0])
                        cols = int(dims[1])
                        inner = ', '.join([f"{{{', '.join([dv]*cols)}}}"] * rows)
                        var_decl += f" = {{{inner}}}"
                    else:
                        var_decl += f" = {{{dv}}}"

                variables.append(var_decl)
                if i < len(tokens) and tokens[i][0] == ',':
                    i += 1   # Skip ',' between multiple array declarations

            # --- Initialised scalar: varname = expr  or  varname = in() ---
            elif i + 1 < len(tokens) and tokens[i + 1][0] == '=':
                i += 2   # Past variable name and '='

                # in() input: varname = in();
                if i < len(tokens) and tokens[i][1] == 'in':
                    read_fn = self._read_function_for_type(lang_type)
                    variables.append(f"{var_name} = {read_fn}()")
                    i += 3   # Past 'in', '(', ')'
                else:
                    # Standard expression initialiser
                    expr_tokens = []
                    while i < len(tokens) and tokens[i][0] not in (',', ';'):
                        expr_tokens.append(tokens[i][0])
                        i += 1
                    value = self._format_expression(expr_tokens)
                    variables.append(f"{var_name} = {value}")

                if i < len(tokens) and tokens[i][0] == ',':
                    i += 1   # Skip ',' to next variable in same declaration

            # --- Uninitialised scalar: varname; ---
            else:
                # Auto-initialise with a safe default value
                variables.append(f"{var_name} = {self._get_default_value(lang_type)}")
                i += 1
                if i < len(tokens) and tokens[i][0] == ',':
                    i += 1

        self.add_line(f"{declaration}{', '.join(variables)};")
        return i + 1   # Return index after ';'

    def _process_struct_variable(self, tokens, index):
        """
        Translate:  struct Name var;   or   struct Name var = {v1, v2};
        Into C:     struct Name var;   or   struct Name var = (struct Name){v1, v2};
        The compound literal  (struct Name){...}  is valid C99 and later.
        """
        struct_type = tokens[index + 1][0]   # Struct type name, e.g. 'Point'
        var_name    = tokens[index + 2][0]   # Variable name, e.g. 'p1'
        self.debug(f"Processing struct variable: struct {struct_type} {var_name}")

        # Register variable type prefixed with 'struct_' so lookups know it is a struct
        if self.current_scope not in self.variable_types:
            self.variable_types[self.current_scope] = {}
        self.variable_types[self.current_scope][var_name] = f"struct_{struct_type}"

        i = index + 3   # Position after variable name

        if i < len(tokens) and tokens[i][0] == '=':
            i += 1   # Past '='
            if i < len(tokens) and tokens[i][0] == '{':
                i += 1   # Past '{'
                init_values = []
                brace_level = 1

                while i < len(tokens) and brace_level > 0:
                    if tokens[i][0] == '{':
                        brace_level += 1
                    elif tokens[i][0] == '}':
                        brace_level -= 1
                        if brace_level == 0:
                            break
                    if tokens[i][0] == ',':
                        i += 1
                        continue
                    # Collect the value expression between commas/braces
                    expr_toks = []
                    while i < len(tokens) and tokens[i][0] not in (',', '}'):
                        expr_toks.append(tokens[i][0])
                        i += 1
                    if expr_toks:
                        init_values.append(self._format_expression(expr_toks))

                if i < len(tokens) and tokens[i][0] == '}':
                    i += 1   # Past closing '}'

                # C99 compound literal initialises a struct inline
                init_str = f"(struct {struct_type}){{{', '.join(init_values)}}}"
                self.add_line(f"struct {struct_type} {var_name} = {init_str};")
            else:
                self.add_line(f"struct {struct_type} {var_name};")
        else:
            self.add_line(f"struct {struct_type} {var_name};")

        while i < len(tokens) and tokens[i][0] != ';':
            i += 1
        return i + 1   # Past ';'

    # ------------------------------------------------------------------ #
    #  Function / vacant / main
    # ------------------------------------------------------------------ #

    def _process_function(self, tokens, index):
        """
        Translate function and vacant declarations.
          Language:  function name(params) { body }   → C: int name(params) { body }
          Language:  vacant   name(params) { body }   → C: void name(params) { body }
          Language:  main() { body }                  → C: int main() { body }
        'function' is like reference 'task'; 'vacant' is like reference 'empty'.
        """
        # Determine return type and function name from the leading keyword
        if tokens[index][1] == 'main':
            func_name   = 'main'
            c_ret_type  = 'int'
            param_start = index + 2   # Past 'main' and '('
        elif tokens[index][1] == 'vacant':
            # vacant = no return value (reference equivalent: empty)
            func_name   = tokens[index + 1][0]
            c_ret_type  = 'void'
            param_start = index + 3   # Past 'vacant', name, '('
        else:
            # 'function' = returns a value (reference equivalent: task)
            func_name   = tokens[index + 1][0]
            c_ret_type  = 'int'       # Default; actual type inferred from return statement
            param_start = index + 3

        self.debug(f"Processing function: {c_ret_type} {func_name}()")

        # Create a fresh variable-type scope for this function
        self.current_scope = func_name
        self.variable_types[self.current_scope] = {}

        # --- Parse parameters: type name, type name, ... ---
        param_list = []
        i = param_start
        current_param_tokens = []

        # Advance until opening '{' of the body, collecting param tokens on the way
        while i < len(tokens) and tokens[i][0] != '{':
            if tokens[i][0] == ')':
                if current_param_tokens:
                    param_list.append(" ".join(current_param_tokens))
                    current_param_tokens = []
                i += 1
                continue
            if tokens[i][0] == ',':
                if current_param_tokens:
                    param_list.append(" ".join(current_param_tokens))
                    current_param_tokens = []
                i += 1
                continue
            if tokens[i][0] != '(':
                current_param_tokens.append(tokens[i][0])
            i += 1

        # Convert language-typed parameters to C-typed parameters
        processed_params = []
        for param in param_list:
            parts = param.split()
            if len(parts) >= 2:
                p_lang = parts[0]              # e.g. 'num'
                p_name = parts[1]              # e.g. 'x'
                p_c    = self._map_datatype(p_lang)
                processed_params.append(f"{p_c} {p_name}")
                # Register parameter so the body can resolve its type
                self.variable_types[self.current_scope][p_name] = p_lang

        # Find the opening '{' of the function body
        brace_index = i
        while brace_index < len(tokens) and tokens[brace_index][0] != '{':
            brace_index += 1

        if brace_index >= len(tokens):
            self.debug(f"Missing opening brace for function {func_name}")
            self.current_scope = "global"
            return index + 1

        end_index = self._find_matching_brace(tokens, brace_index)
        if end_index == -1:
            self.debug(f"Missing closing brace for function {func_name}")
            self.current_scope = "global"
            return len(tokens)

        # Emit the function signature
        if func_name == 'main':
            self.add_line("int main() {")
        else:
            self.add_line(f"{c_ret_type} {func_name}({', '.join(processed_params)}) {{")

        self.indentation += 1
        self.debug(f"Function body: tokens {brace_index} to {end_index}")

        # --- Process every statement in the function body ---
        j = brace_index + 1
        while j < end_index:
            old_j = j
            j = self._process_statement(tokens, j, end_index)
            if j == old_j:   # Safety guard: prevent infinite loop on unknown tokens
                self.debug(f"No advance at index {j}, skipping token: {tokens[j]}")
                j += 1

        # main() always returns 0 in C
        if func_name == 'main':
            self.add_line("return 0;")

        self.indentation -= 1
        self.add_line("}")
        self.add_line("")

        self.current_scope = "global"
        self.debug(f"Finished function {func_name}, next index: {end_index + 1}")
        return end_index + 1

    # ------------------------------------------------------------------ #
    #  Brace matching utility
    # ------------------------------------------------------------------ #

    def _find_matching_brace(self, tokens, start_index):
        """
        Given the index of an opening '{', return the index of its matching '}'.
        Tracks depth to handle nested braces correctly.
        Returns -1 if no matching brace is found.
        """
        if start_index >= len(tokens) or tokens[start_index][0] != '{':
            self.debug(f"No opening brace at index {start_index}")
            return -1

        depth = 1
        i = start_index + 1
        while i < len(tokens) and depth > 0:
            if tokens[i][0] == '{':
                depth += 1    # Entered a nested block
            elif tokens[i][0] == '}':
                depth -= 1    # Exited a nested block
            i += 1

        return i - 1 if depth == 0 else -1

    # ------------------------------------------------------------------ #
    #  Statement dispatcher  (mirrors reference _process_statement)
    # ------------------------------------------------------------------ #

    def _process_statement(self, tokens, index, end_index):
        """
        Identify the type of the current statement and dispatch to the correct handler.
        Called for every statement inside a function body or block.
        """
        if index >= end_index:
            return index

        tok_lex  = tokens[index][0]
        tok_type = tokens[index][1]
        self.debug(f"Processing statement at index {index}: '{tok_lex}' ({tok_type})")

        # struct type definition inside function body
        if self._is_struct_declaration(tokens, index):
            self.debug(f"Found struct declaration at index {index}")
            return self._process_struct_declaration(tokens, index)

        # const declaration inside function body
        if tok_type == 'const':
            return self._process_const_declaration(tokens, index)

        # Variable declarations (num, deci, word, single, bool, struct instance)
        if self._is_variable_declaration(tokens, index):
            self.debug(f"Found variable declaration at index {index}")
            return self._process_variable_declaration(tokens, index)

        # Increment / decrement: id++  id--  ++id  --id
        if self._is_increment_decrement(tokens, index):
            self.debug(f"Found increment/decrement at index {index}")
            return self._process_increment_decrement(tokens, index)

        # Assignment statement (simple, compound, array, struct field)
        if self._is_assignment(tokens, index):
            self.debug(f"Found assignment at index {index}")
            return self._process_assignment(tokens, index)

        # out(...) output statement
        if self._is_out_statement(tokens, index):
            self.debug(f"Found out() at index {index}")
            return self._process_out(tokens, index)

        # if / elseif / else
        if self._is_if_statement(tokens, index):
            self.debug(f"Found if statement at index {index}")
            return self._process_if_statement(tokens, index, end_index)

        # match / pick / def / split  (switch-case equivalent)
        if self._is_match_statement(tokens, index):
            self.debug(f"Found match statement at index {index}")
            return self._process_match_statement(tokens, index, end_index)

        # Loop statements: while, for, do
        if self._is_loop_statement(tokens, index):
            self.debug(f"Found loop statement at index {index}")
            return self._process_loop_statement(tokens, index, end_index)

        # return statement
        if tok_type == 'return':
            return self._process_return(tokens, index)

        # Standalone function call
        if self._is_function_call(tokens, index):
            self.debug(f"Found function call at index {index}")
            return self._process_function_call(tokens, index)

        self.debug(f"Unknown statement type at index {index}: '{tok_lex}' ({tok_type})")
        return index + 1

    # ------------------------------------------------------------------ #
    #  Increment / Decrement
    # ------------------------------------------------------------------ #

    def _process_increment_decrement(self, tokens, index):
        """
        Translate post-increment/post-decrement and pre-increment/pre-decrement.
        Language operators: ++  --   (identical to C)
        Post form:  id++  or  id--
        Pre form:   ++id  or  --id
        """
        if tokens[index][1] == 'identifier':
            # Post-increment / post-decrement:  id++  id--
            variable = tokens[index][0]
            operator = tokens[index + 1][0]
            self.debug(f"Post-{operator} on {variable}")
            self.add_line(f"{variable}{operator};")
            i = index + 2
        else:
            # Pre-increment / pre-decrement:  ++id  --id
            operator = tokens[index][0]
            variable = tokens[index + 1][0]
            self.debug(f"Pre-{operator} on {variable}")
            self.add_line(f"{operator}{variable};")
            i = index + 2

        while i < len(tokens) and tokens[i][0] != ';':
            i += 1
        return i + 1   # Past ';'

    # ------------------------------------------------------------------ #
    #  Assignment
    # ------------------------------------------------------------------ #

    def _process_assignment(self, tokens, index):
        """
        Translate all forms of assignment:
          var = expr                simple scalar assignment
          var += expr               compound assignment
          var **= expr              exponent assign → uses pow()
          var[i] = expr             1D array element assignment
          var[r][c] = expr          2D array element assignment
          var.field = expr          struct field assignment
          var = in()                input assignment (reads from stdin)
          var.field = in()          struct field input assignment
        Language operators: = += -= *= /= %= **=
        """
        variable  = tokens[index][0]
        var_type  = self._get_variable_type(variable)   # Look up type for in() dispatch
        array_indices = []
        assignment_op = '='
        i = index + 1

        # --- Struct member assignment:  var.field op expr ---
        if i < len(tokens) and tokens[i][0] == '.':
            struct_member = tokens[i + 1][0]
            i += 2   # Past '.' and member name

            assignment_op = tokens[i][0]
            i += 1   # Past the assignment operator

            # Look up member type to choose the right read_* function for in()
            struct_type = (var_type or "").replace("struct_", "")
            member_type = (self.struct_definitions.get(struct_type) or {}).get(struct_member, 'word')

            if i < len(tokens) and tokens[i][1] == 'in':
                # Struct field input:  var.field = in();
                read_fn = self._read_function_for_type(member_type)
                self.add_line(f"{variable}.{struct_member} = {read_fn}();")
                i += 3   # Past 'in', '(', ')'
                while i < len(tokens) and tokens[i][0] != ';':
                    i += 1
                return i + 1

            # Regular struct field assignment
            expr_tokens = []
            while i < len(tokens) and tokens[i][0] != ';':
                expr_tokens.append(tokens[i][0])
                i += 1

            expr_str = self._format_expression(expr_tokens)
            self.add_line(f"{variable}.{struct_member} {assignment_op} {expr_str};")
            return i + 1

        # --- Array assignment:  var[i] op expr  or  var[r][c] op expr ---
        if i < len(tokens) and tokens[i][0] == '[':
            while i < len(tokens) and tokens[i][0] == '[':
                i += 1   # Past '['
                idx_expr = []
                while i < len(tokens) and tokens[i][0] != ']':
                    idx_expr.append(tokens[i][0])
                    i += 1
                i += 1   # Past ']'
                array_indices.append(self._format_expression(idx_expr))

        # --- Consume the assignment operator ---
        if i < len(tokens):
            assignment_op = tokens[i][0]
            i += 1   # Past the operator

        # --- in() input assignment:  var = in() ---
        if i < len(tokens) and tokens[i][1] == 'in':
            # Build the full array access string for assignment target
            array_access = variable + "".join(f"[{idx}]" for idx in array_indices)
            read_fn = self._read_function_for_type(var_type or 'word')
            self.add_line(f"{array_access} = {read_fn}();")
            i += 3   # Past 'in', '(', ')'
            while i < len(tokens) and tokens[i][0] != ';':
                i += 1
            return i + 1

        # --- Standard expression assignment ---
        expr_tokens = []
        while i < len(tokens) and tokens[i][0] != ';':
            expr_tokens.append(tokens[i][0])
            i += 1

        expr_str = self._format_expression(expr_tokens)

        if array_indices:
            # Build array access: arr[i]  or  grid[r][c]
            array_access = variable + "".join(f"[{idx}]" for idx in array_indices)
            if assignment_op == '**=':
                # No ** operator in C; translate to pow()
                self.add_line(f"{array_access} = (int)pow((double){array_access}, (double){expr_str});")
            else:
                self.add_line(f"{array_access} {assignment_op} {expr_str};")
        else:
            if assignment_op == '**=':
                # No ** operator in C; translate to pow()
                self.add_line(f"{variable} = (int)pow((double){variable}, (double){expr_str});")
            else:
                self.add_line(f"{variable} {assignment_op} {expr_str};")

        return i + 1   # Past ';'

    # ------------------------------------------------------------------ #
    #  Expression formatter
    # ------------------------------------------------------------------ #

    def _format_expression(self, expr_tokens):
        """
        Join token lexemes into a C expression string.
        Translates language-specific operators/literals to C equivalents:
          is      →  ==       (equality comparison)
          isnot   →  !=       (inequality comparison)
          ~       →  -        (unary negation; language uses ~ instead of -)
          ~N      →  -N       (tilde-prefixed numeric literal → negated literal)
          true/false → unchanged (C99 bool from <stdbool.h>)
        """
        if not expr_tokens:
            return ""

        result = []
        i = 0
        while i < len(expr_tokens):
            token = expr_tokens[i]

            if token == 'is':
                result.append('==')      # Language equality operator → C ==
            elif token == 'isnot':
                result.append('!=')      # Language inequality operator → C !=
            elif token == '~':
                result.append('-')       # Standalone tilde → unary negation
            elif token.startswith('~') and len(token) > 1:
                # Tilde-prefixed number literal: ~5 → -5, ~3.14 → -3.14
                result.append('-' + token[1:])
            else:
                result.append(token)     # All other tokens pass through unchanged
            i += 1

        return " ".join(result)

    # ------------------------------------------------------------------ #
    #  out() output  →  printf
    # ------------------------------------------------------------------ #

    def _process_out(self, tokens, index):
        """
        Translate:  out(expr + expr + ...)
        Into C:     one printf(...) call per segment split on '+'

        Language keyword: out  (ref: display)
        Maps to C: printf with the format specifier selected by variable type:
          num    → %d
          deci   → %f
          single → %c
          word   → %s
          bool   → %s with ternary ? "true" : "false"
          string literal → %s
          numeric literal → %d or %f
        """
        self.debug(f"Processing out() at index {index}")

        i = index + 1
        # Find opening '(' of out(...)
        while i < len(tokens) and tokens[i][0] != '(':
            i += 1

        if i >= len(tokens):
            self.debug("No opening parenthesis for out()")
            return index + 1

        i += 1   # Past '('

        # Collect tokens inside out(...), respecting nested parentheses
        expr_tokens = []
        paren_level = 0
        while i < len(tokens):
            if tokens[i][0] == '(':
                paren_level += 1
                expr_tokens.append(tokens[i][0])
            elif tokens[i][0] == ')':
                if paren_level == 0:
                    break   # Closing ')' of out(...)
                paren_level -= 1
                expr_tokens.append(tokens[i][0])
            else:
                expr_tokens.append(tokens[i][0])
            i += 1

        self.debug(f"out() expression tokens: {expr_tokens}")

        # Find all '+' positions to split into separate printf calls
        # out("Name: " + name + "\n")  →  three separate printf calls
        plus_indices = [j for j, t in enumerate(expr_tokens) if t == '+']

        if plus_indices:
            # Build list of token-groups between '+' operators
            segments = []
            start = 0
            for plus_idx in plus_indices:
                segments.append(expr_tokens[start:plus_idx])
                start = plus_idx + 1
            if start < len(expr_tokens):
                segments.append(expr_tokens[start:])

            # Emit one printf per segment with the correct format specifier
            for segment in segments:
                self._emit_printf_segment(segment)
        else:
            # Single expression with no concatenation
            self._emit_printf_segment(expr_tokens)

        # Skip past closing ')' and find ';'
        i += 1
        while i < len(tokens) and tokens[i][0] != ';':
            i += 1
        return i + 1   # Past ';'

    def _emit_printf_segment(self, segment):
        """
        Emit one printf call for a single out() segment.
        Selects the correct printf format specifier based on segment content/type.
        """
        if not segment:
            return

        expr_str = self._format_expression(segment)

        # --- Single-token segment ---
        if len(segment) == 1:
            tok = segment[0]

            # word_literal (string constant in double quotes)
            if tok.startswith('"') and tok.endswith('"'):
                self.add_line(f"printf(\"%s\", {tok});")
                return

            # single_literal (char constant in single quotes, e.g. 'A')
            if tok.startswith("'") and tok.endswith("'") and len(tok) == 3:
                self.add_line(f"printf(\"%c\", {tok});")
                return

            # Boolean literals: true / false
            if tok in ('true', 'false'):
                self.add_line(f"printf(\"%s\", {tok} ? \"true\" : \"false\");")
                return

            # Decimal literal (contains a '.')
            if '.' in tok:
                try:
                    float(tok)
                    self.add_line(f"printf(\"%f\", {tok});")
                    return
                except ValueError:
                    pass

            # Integer literal
            try:
                int(tok)
                self.add_line(f"printf(\"%d\", {tok});")
                return
            except ValueError:
                pass

            # Identifier: look up language type and emit typed printf
            var_type = self._get_variable_type(tok)
            if var_type:
                if var_type.startswith('struct_'):
                    # Cannot printf a whole struct; only individual fields
                    self.add_line(f"// Cannot print struct '{tok}' directly; access a field")
                    return
                self._printf_by_lang_type(var_type, expr_str)
                return

            # Fallback: unknown type, emit as string
            self.add_line(f"printf(\"%s\", {expr_str});")
            return

        # --- Struct member access: var.field ---
        if len(segment) >= 3 and segment[1] == '.':
            base       = segment[0]
            field      = segment[2]
            var_type   = self._get_variable_type(base)
            struct_t   = (var_type or "").replace("struct_", "")
            field_type = (self.struct_definitions.get(struct_t) or {}).get(field, 'word')
            self._printf_by_lang_type(field_type, f"{base}.{field}")
            return

        # --- Array element access: var[idx] or var[r][c] ---
        base = segment[0]
        var_type = self._get_variable_type(base)
        if var_type and len(segment) >= 3 and segment[1] == '[':
            # The whole formatted expression is the array element
            self._printf_by_lang_type(var_type, expr_str)
            return

        # --- Compound expression containing bool literals ---
        if any(t in ('true', 'false') for t in segment):
            self.add_line(f"printf(\"%s\", ({expr_str}) ? \"true\" : \"false\");")
            return

        # --- Generic compound expression: use type of first identifier ---
        first_id_type = self._get_variable_type(base)
        self._printf_by_lang_type(first_id_type, expr_str)

    def _printf_by_lang_type(self, lang_type, expr_str):
        """
        Emit printf with the correct format specifier for a given language type.
          num    → %d   (integer)
          deci   → %f   (floating point)
          single → %c   (character)
          word   → %s   (string)
          bool   → %s   with ternary  ? "true" : "false"
          None   → %s   (fallback for unknowns)
        """
        if lang_type == 'num':
            self.add_line(f"printf(\"%d\", {expr_str});")
        elif lang_type == 'deci':
            self.add_line(f"printf(\"%f\", {expr_str});")
        elif lang_type == 'single':
            self.add_line(f"printf(\"%c\", {expr_str});")
        elif lang_type == 'word':
            self.add_line(f"printf(\"%s\", {expr_str});")
        elif lang_type == 'bool':
            # C has no built-in bool-to-string; use ternary
            self.add_line(f"printf(\"%s\", {expr_str} ? \"true\" : \"false\");")
        else:
            self.add_line(f"printf(\"%s\", {expr_str});")   # Safe fallback

    # ------------------------------------------------------------------ #
    #  return statement
    # ------------------------------------------------------------------ #

    def _process_return(self, tokens, index):
        """
        Translate:  return expr;
        Into C:     return expr;
        Language keyword: return  (same as C)
        """
        i = index + 1   # Past 'return'
        expr_tokens = []
        while i < len(tokens) and tokens[i][0] != ';':
            expr_tokens.append(tokens[i][0])
            i += 1

        if expr_tokens:
            self.add_line(f"return {self._format_expression(expr_tokens)};")
        else:
            self.add_line("return;")

        return i + 1   # Past ';'

    # ------------------------------------------------------------------ #
    #  if / elseif / else
    # ------------------------------------------------------------------ #

    def _process_if_statement(self, tokens, index, end_index):
        """
        Translate:  if (cond) { } elseif (cond) { } else { }
        Into C:     if (cond) { } else if (cond) { } else { }
        Language keywords: if, elseif, else
        Note: language uses one-word 'elseif'; C uses two-word 'else if'.
        """
        self.debug(f"Processing if statement at index {index}")

        i = index + 1   # Past 'if'

        # Find and collect condition inside ( )
        while i < len(tokens) and tokens[i][0] != '(':
            i += 1
        i += 1   # Past '('

        condition_tokens = []
        paren_level = 0
        while i < len(tokens):
            if tokens[i][0] == '(':
                paren_level += 1
                condition_tokens.append(tokens[i][0])
            elif tokens[i][0] == ')':
                if paren_level == 0:
                    break   # Reached closing ')' of condition
                paren_level -= 1
                condition_tokens.append(tokens[i][0])
            else:
                condition_tokens.append(tokens[i][0])
            i += 1

        cond_str = self._format_expression(condition_tokens)
        self.debug(f"If condition: {cond_str}")

        # Find opening '{' of the if-block
        i += 1   # Past ')'
        while i < len(tokens) and tokens[i][0] != '{':
            i += 1

        if_block_start = i
        if_block_end   = self._find_matching_brace(tokens, if_block_start)
        if if_block_end == -1:
            self.debug("Missing closing brace for if block")
            return index + 1

        # Emit if block
        self.add_line(f"if ({cond_str}) {{")
        self.indentation += 1
        j = if_block_start + 1
        while j < if_block_end:
            old = j
            j = self._process_statement(tokens, j, if_block_end)
            if j == old:
                j += 1
        self.indentation -= 1
        self.add_line("}")

        # Handle zero or more elseif blocks
        next_index = if_block_end + 1
        while next_index < len(tokens) and tokens[next_index][1] == 'elseif':
            self.debug(f"Found elseif at index {next_index}")
            ei = next_index + 1   # Past 'elseif'

            while ei < len(tokens) and tokens[ei][0] != '(':
                ei += 1
            ei += 1   # Past '('

            elseif_cond_tokens = []
            paren_level = 0
            while ei < len(tokens):
                if tokens[ei][0] == '(':
                    paren_level += 1
                    elseif_cond_tokens.append(tokens[ei][0])
                elif tokens[ei][0] == ')':
                    if paren_level == 0:
                        break
                    paren_level -= 1
                    elseif_cond_tokens.append(tokens[ei][0])
                else:
                    elseif_cond_tokens.append(tokens[ei][0])
                ei += 1

            elseif_cond = self._format_expression(elseif_cond_tokens)

            ei += 1   # Past ')'
            while ei < len(tokens) and tokens[ei][0] != '{':
                ei += 1

            ei_block_start = ei
            ei_block_end   = self._find_matching_brace(tokens, ei_block_start)
            if ei_block_end == -1:
                self.debug("Missing closing brace for elseif block")
                break

            # Language 'elseif' → C 'else if' (two separate words)
            self.add_line(f"else if ({elseif_cond}) {{")
            self.indentation += 1
            j = ei_block_start + 1
            while j < ei_block_end:
                old = j
                j = self._process_statement(tokens, j, ei_block_end)
                if j == old:
                    j += 1
            self.indentation -= 1
            self.add_line("}")

            next_index = ei_block_end + 1

        # Handle optional else block
        if next_index < len(tokens) and tokens[next_index][1] == 'else':
            self.debug(f"Found else at index {next_index}")
            ei = next_index + 1   # Past 'else'
            while ei < len(tokens) and tokens[ei][0] != '{':
                ei += 1

            else_start = ei
            else_end   = self._find_matching_brace(tokens, else_start)
            if else_end != -1:
                self.add_line("else {")
                self.indentation += 1
                j = else_start + 1
                while j < else_end:
                    old = j
                    j = self._process_statement(tokens, j, else_end)
                    if j == old:
                        j += 1
                self.indentation -= 1
                self.add_line("}")
                return else_end + 1

        return next_index

    # ------------------------------------------------------------------ #
    #  match / pick / def / split  →  switch / case / default / break
    # ------------------------------------------------------------------ #

    def _process_match_statement(self, tokens, index, end_index):
        """
        Translate:
          match (expr) {
              pick value : statements split;
              def        : statements
          }
        Into C:
          switch (expr) {
              case value: statements break;
              default:    statements break;
          }
        Language keywords:
          match  → switch    (control expression dispatch)
          pick   → case      (match a specific value)
          def    → default   (fallback when no pick matches)
          split  → break     (exit the switch block)
        """
        self.debug(f"Processing match statement at index {index}")

        i = index + 1   # Past 'match'

        # Collect switch expression inside ( )
        while i < len(tokens) and tokens[i][0] != '(':
            i += 1
        i += 1   # Past '('

        expr_tokens = []
        paren_level = 0
        while i < len(tokens):
            if tokens[i][0] == '(':
                paren_level += 1
                expr_tokens.append(tokens[i][0])
            elif tokens[i][0] == ')':
                if paren_level == 0:
                    break
                paren_level -= 1
                expr_tokens.append(tokens[i][0])
            else:
                expr_tokens.append(tokens[i][0])
            i += 1

        match_expr = self._format_expression(expr_tokens)
        self.debug(f"Match expression: {match_expr}")

        # Find match block braces
        i += 1   # Past ')'
        while i < len(tokens) and tokens[i][0] != '{':
            i += 1

        block_start = i
        block_end   = self._find_matching_brace(tokens, block_start)
        if block_end == -1:
            self.debug("Missing closing brace for match block")
            return index + 1

        self.add_line(f"switch ({match_expr}) {{")
        self.indentation += 1

        j = block_start + 1
        while j < block_end:

            # pick value : statements split;
            if tokens[j][1] == 'pick':
                self.debug(f"Found pick at index {j}")
                j += 1   # Past 'pick'

                # Collect the case pattern value until ':'
                pattern_tokens = []
                while j < block_end and tokens[j][0] != ':':
                    pattern_tokens.append(tokens[j][0])
                    j += 1
                j += 1   # Past ':'

                pattern_str = self._format_expression(pattern_tokens)
                self.add_line(f"case {pattern_str}:")   # pick → case
                self.indentation += 1

                # Process statements in this case until 'split' keyword
                while j < block_end and tokens[j][1] != 'split':
                    old = j
                    j = self._process_statement(tokens, j, block_end)
                    if j == old:
                        j += 1

                self.add_line("break;")   # split → break
                if j < block_end and tokens[j][1] == 'split':
                    j += 1   # Past 'split'
                if j < block_end and tokens[j][0] == ';':
                    j += 1   # Past ';'

                self.indentation -= 1

            # def : statements  (default case, no split required)
            elif tokens[j][1] == 'def':
                self.debug(f"Found def at index {j}")
                j += 1   # Past 'def'
                if j < block_end and tokens[j][0] == ':':
                    j += 1   # Past ':'

                self.add_line("default:")   # def → default
                self.indentation += 1

                while j < block_end and tokens[j][1] not in ('split', '}'):
                    old = j
                    j = self._process_statement(tokens, j, block_end)
                    if j == old:
                        j += 1

                self.add_line("break;")   # Always emit break for default
                if j < block_end and tokens[j][1] == 'split':
                    j += 1
                if j < block_end and tokens[j][0] == ';':
                    j += 1

                self.indentation -= 1

            else:
                j += 1

        self.indentation -= 1
        self.add_line("}")

        return block_end + 1

    # ------------------------------------------------------------------ #
    #  Loop statements: while, for, do-while
    # ------------------------------------------------------------------ #

    def _process_loop_statement(self, tokens, index, end_index):
        """
        Dispatch to the correct loop handler based on the loop keyword.
        Language keywords: while, for, do
        """
        loop_type = tokens[index][1]
        self.debug(f"Processing {loop_type} loop at index {index}")

        if loop_type == 'while':
            return self._process_while_loop(tokens, index, end_index)
        elif loop_type == 'do':
            return self._process_do_while_loop(tokens, index, end_index)
        elif loop_type == 'for':
            return self._process_for_loop(tokens, index, end_index)

        return index + 1

    def _process_while_loop(self, tokens, index, end_index):
        """
        Translate:  while (cond) { body }
        Into C:     while (cond) { body }
        Language keyword: while  (identical to C)
        """
        i = index + 1   # Past 'while'

        while i < len(tokens) and tokens[i][0] != '(':
            i += 1
        i += 1   # Past '('

        cond_tokens = []
        paren_level = 0
        while i < len(tokens):
            if tokens[i][0] == '(':
                paren_level += 1
                cond_tokens.append(tokens[i][0])
            elif tokens[i][0] == ')':
                if paren_level == 0:
                    break
                paren_level -= 1
                cond_tokens.append(tokens[i][0])
            else:
                cond_tokens.append(tokens[i][0])
            i += 1

        cond_str = self._format_expression(cond_tokens)

        i += 1   # Past ')'
        while i < len(tokens) and tokens[i][0] != '{':
            i += 1

        block_start = i
        block_end   = self._find_matching_brace(tokens, block_start)
        if block_end == -1:
            self.debug("Missing closing brace for while loop")
            return index + 1

        self.add_line(f"while ({cond_str}) {{")
        self.indentation += 1

        j = block_start + 1
        while j < block_end:
            old = j
            j = self._process_statement(tokens, j, block_end)
            if j == old:
                j += 1

        self.indentation -= 1
        self.add_line("}")

        return block_end + 1

    def _process_do_while_loop(self, tokens, index, end_index):
        """
        Translate:  do { body } while (cond);
        Into C:     do { body } while (cond);
        Language keyword: do  (identical structure to C do-while)
        """
        i = index + 1   # Past 'do'

        while i < len(tokens) and tokens[i][0] != '{':
            i += 1

        block_start = i
        block_end   = self._find_matching_brace(tokens, block_start)
        if block_end == -1:
            self.debug("Missing closing brace for do-while loop")
            return index + 1

        self.add_line("do {")
        self.indentation += 1

        j = block_start + 1
        while j < block_end:
            old = j
            j = self._process_statement(tokens, j, block_end)
            if j == old:
                j += 1

        self.indentation -= 1

        # Find 'while' keyword that follows the closing brace
        i = block_end + 1
        while i < len(tokens) and tokens[i][1] != 'while':
            i += 1
        i += 1   # Past 'while'

        while i < len(tokens) and tokens[i][0] != '(':
            i += 1
        i += 1   # Past '('

        cond_tokens = []
        paren_level = 0
        while i < len(tokens):
            if tokens[i][0] == '(':
                paren_level += 1
                cond_tokens.append(tokens[i][0])
            elif tokens[i][0] == ')':
                if paren_level == 0:
                    break
                paren_level -= 1
                cond_tokens.append(tokens[i][0])
            else:
                cond_tokens.append(tokens[i][0])
            i += 1

        cond_str = self._format_expression(cond_tokens)
        self.add_line(f"}} while ({cond_str});")   # Closing brace merged with while condition

        # Skip past closing ')' and ';'
        i += 1
        while i < len(tokens) and tokens[i][0] != ';':
            i += 1
        return i + 1

    def _process_for_loop(self, tokens, index, end_index):
        """
        Translate:  for (id = init; cond; id++/--) { body }
        Into C:     for (id = init; cond; id++/--) { body }
        Language keyword: for  (identical structure to C for-loop)
        The increment part uses language ++ / -- which are identical to C.
        fflush(stdout) is added after the body to ensure GUI output is timely.
        """
        i = index + 1   # Past 'for'

        while i < len(tokens) and tokens[i][0] != '(':
            i += 1
        i += 1   # Past '('

        # Collect initialiser: everything before first ';'
        init_tokens = []
        while i < len(tokens) and tokens[i][0] != ';':
            init_tokens.append(tokens[i][0])
            i += 1
        init_str = " ".join(init_tokens)
        i += 1   # Past first ';'

        # Collect condition: everything before second ';'
        cond_tokens = []
        while i < len(tokens) and tokens[i][0] != ';':
            cond_tokens.append(tokens[i][0])
            i += 1
        cond_str = self._format_expression(cond_tokens)
        i += 1   # Past second ';'

        # Collect increment: everything before closing ')'
        incr_tokens = []
        paren_level = 0
        while i < len(tokens):
            if tokens[i][0] == '(':
                paren_level += 1
                incr_tokens.append(tokens[i][0])
            elif tokens[i][0] == ')':
                if paren_level == 0:
                    i += 1   # Past ')'
                    break
                paren_level -= 1
                incr_tokens.append(tokens[i][0])
            else:
                incr_tokens.append(tokens[i][0])
            i += 1

        # Join increment tightly so 'i ++' becomes 'i++' not 'i ++'
        incr_str = "".join(incr_tokens)

        while i < len(tokens) and tokens[i][0] != '{':
            i += 1

        block_start = i
        block_end   = self._find_matching_brace(tokens, block_start)
        if block_end == -1:
            self.debug("Missing closing brace for for loop")
            return index + 1

        self.add_line(f"for ({init_str}; {cond_str}; {incr_str}) {{")
        self.indentation += 1

        j = block_start + 1
        while j < block_end:
            old = j
            j = self._process_statement(tokens, j, block_end)
            if j == old:
                j += 1

        self.indentation -= 1
        self.add_line("fflush(stdout);")   # Flush after each iteration for real-time GUI output
        self.add_line("}")

        return block_end + 1

    # ------------------------------------------------------------------ #
    #  Standalone function call
    # ------------------------------------------------------------------ #

    def _process_function_call(self, tokens, index):
        """
        Translate a standalone function call statement: funcName(args);
        Collects all arguments respecting nested parentheses,
        formats each argument expression, and emits the C call.
        """
        func_name = tokens[index][0]
        self.debug(f"Processing function call: {func_name}()")

        i = index + 2   # Past function name and opening '('

        params        = []
        current_param = []
        paren_level   = 1   # We have consumed the opening '('

        while i < len(tokens) and paren_level > 0:
            if tokens[i][0] == '(':
                paren_level += 1
                current_param.append(tokens[i][0])
            elif tokens[i][0] == ')':
                paren_level -= 1
                if paren_level > 0:
                    current_param.append(tokens[i][0])
                else:
                    # Closing ')' of the call: save last argument
                    if current_param:
                        params.append(self._format_expression(current_param))
            elif tokens[i][0] == ',' and paren_level == 1:
                # Top-level comma: argument separator
                params.append(self._format_expression(current_param))
                current_param = []
            else:
                current_param.append(tokens[i][0])
            i += 1

        param_str = ", ".join(params)
        self.add_line(f"{func_name}({param_str});")

        # Skip any remaining tokens until ';'
        while i < len(tokens) and tokens[i][0] != ';':
            i += 1
        return i + 1   # Past ';'