cfg = {
    "<program>": [["<global_dec>", "<function_set>", "main", "(", ")", "{", "<local_dec>", "<statement_set>", "}"]],

    "<global_dec>": [["<global_dec_after>", "<global_dec>"],
                     ["λ"]],

    "<global_dec_after>": [["<data_type>", "identifier", "<declaration_after>"], # identifier or single literal
                        ["const", "<data_type>", "identifier", "=", "<literal>", "<const_after>"],
                        ["struct", "identifier", "<struct_after>"]],

    "<data_type>": [
        ["num"],
        ["deci"],
        ["word"],
        ["single"],
        ["bool"]],

    "<literal>": [
        ["<number_literal>"],
        ["word_literal"],
        ["single_literal"],
        ["<bool_literal>"]],

    "<number_literal>": [
        ["num_literal"],
        ["deci_literal"]],

    "<bool_literal>": [
        ["true"],
        ["false"]],

    "<const_after>": [
        [";"],
        [",", "identifier", "=", "<literal>", "<const_after>"]],

    "<declaration_after>": [
        ["<variable_after>"],
        ["[", "<array_form>"]],

    "<variable_after>": [
        [";"],
        [",", "identifier", "<variable_after>"],
        ["=", "<expression>", "<initialize_after>"]],

    "<initialize_after>": [
        [";"],
        [",", "identifier", "<variable_after>"]],

    "<array_form>": [
        ["]", "=", "{", "<array_value>", "}", ";"],
        ["<size>", "]", "<array_after>"]],

    "<array_value>": [
        ["<literal>", "<array_lit_after>"],
        ["λ"]],

    "<size>": [
        ["num_literal"]],

    "<array_after>": [
        [";"],
        ["=", "{", "<array_value>", "}", ";"],
        ["[", "<size>", "]", "<array2d_after>"]],

    "<array2d_after>": [
        [";"],
        ["=", "{", "{", "<array_value>", "}", "<row_group>", "}", ";"]],

    "<array_lit_after>": [
        [",", "<literal>", "<array_lit_after>"],
        ["λ"]],

    "<row_group>": [
        [",", "{", "<array_value>", "}", "<row_group>"],
        ["λ"]],

    "<struct_after>": [
        ["{", "<member_dec>", "}"],
        ["identifier", "<struct_initialize>"]
    ],

    "<struct_initialize>": [
        [";"],
        ["=", "{", "<struct_value>", "}", ";"]],

    "<member_dec>": [
        ["<data_type>", "identifier", ";", "<member_dec>"],
        ["λ"]],

    "<struct_value>": [
        ["<literal>", "<struct_value_after>"],
        ["λ"]],

    "<struct_value_after>": [
        [",","<literal>", "<struct_value_after>"],
        ["λ"]],

    "<function_set>": [
        ["<function_dec>", "<function_set>"],
        ["λ"]],

    "<function_dec>": [
        ["function", "identifier", "(", "<parameter>", ")", "{", "<local_dec>", "<statement_set>", "<return_statement>", "}"],
        ["vacant", "identifier", "(", "<parameter>", ")", "{", "<local_dec>", "<statement_set>", "}"]],

    "<parameter>": [
        ["<parameter_set>"],
        ["λ"]],

    "<parameter_set>": [
        ["<data_type>", "identifier", "<parameter_after>"]],

    "<parameter_after>": [
        [",", "<data_type>", "identifier", "<parameter_after>"],
        ["λ"]],

    "<local_dec>": [
        ["<local_dec_after>", "<local_dec>"],
        ["λ"]],


    "<local_dec_after>": [
        ["<data_type>", "identifier", "<declaration_after>"],
        ["const", "<data_type>", "identifier", "=", "<literal>", "<const_after>"],
        ["struct", "identifier", "<struct_after>"]],

    "<statement_set>": [
        ["<statement_after>", "<statement_set>"],
        ["λ"]],

    
    "<statement_after>": [
        ["identifier", "<statement_id_after>"],
        ["<incre_decre_op>", "identifier", ";"],
        ["<conditional_statement>"],
        ["<loop_statement>"],
        ["out", "(", "<out_scope>", ")", ";"]],
        

    "<statement_id_after>": [
        ["(", "<argument_set>", ")",";"],
        ["<assignment_op>", "<assign_value>", ";"],
        ["[", "<arithmetic_expression>", "]", "<array_index_after>", "<assignment_op>", "<assign_value>", ";"],
        [".", "identifier", "<assignment_op>", "<assign_value>", ";"],
        ["<incre_decre_op>", ";"]],

    "<array_index_after>": [
        ["[", "<arithmetic_expression>", "]"],
        ["λ"]],

    "<incre_decre_op>": [
        ["++"],
        ["--"]],

    "<argument_set>": [
        ["<arithmetic_expression>", "<argument_after>"],
        ["λ"]],

    "<argument_after>": [
        [",", "<arithmetic_expression>", "<argument_after>"],
        ["λ"]],

    "<assignment_op>": [
        ["="],
        ["+="],
        ["-="],
        ["*="],
        ["%="],
        ["/="],
        ["**="]],

    "<assign_value>": [
        ["<expression>"],
        ["in", "(", ")"]],

    "<expression>": [
        ["<expression_operand>", "<expression_after>"]],

    "<expression_after>": [
        ["<expression_op>", "<expression_operand>", "<expression_after>"],
        ["λ"]],

    "<expression_operand>": [["<value>"],
                             ["(", "<expression>", ")"],
                             ["!", "(", "<expression>", ")"]],

    "<expression_op>": [
        ["+"],
        ["-"],
        ["*"],
        ["/"],
        ["%"],
        ["**"],
        ["=="],
        ["!="],
        ["<"],
        [">"],
        ["<="],
        [">="],
        ["&&"],
        ["||"],
        ["is"],
        ["isnot"]],

    "<value>": [
        ["<literal>"],
        ["identifier", "<value_iden_after>"]],

    "<value_iden_after>": [
        ["(", "<argument_set>", ")"],
        ["[", "<arithmetic_expression>", "]", "<array_index_after>"],
        [".", "identifier"],
        ["λ"]],

    "<arithmetic_expression>": [
        ["<arithmetic_operand>", "<arithmetic_after>"]],

    "<arithmetic_after>": [
        ["<arithmetic_op>", "<arithmetic_operand>", "<arithmetic_after>"],
        ["λ"]],

    "<arithmetic_operand>": [
        ["<value>"],
        ["(", "<arithmetic_expression>", ")"]],

    "<arithmetic_op>": [
        ["+"], 
        ["-"], 
        ["*"], 
        ["/"], 
        ["%"], 
        ["**"]],

    "<conditional_statement>": [
        ["<if_statement>", "<elseif_statement>", "<else_statement>"],
        ["<match_statement>"]],

    "<if_statement>": [
        ["if", "(", "<condition>", ")", "{", "<statement_set>", "}"]],

    "<elseif_statement>": [
        ["elseif", "(", "<condition>", ")", "{", "<statement_set>", "}", "<elseif_statement>"],
        ["λ"]],

    "<else_statement>": [
        ["else", "{", "<statement_set>", "}"],
        ["λ"]],

    "<match_statement>": [
        ["match", "(", "identifier", ")", "{", "<pick>", "def", ":", "<statement_set>", "}"]],

    "<pick>": [
        ["pick", "<pattern>", ":", "<pick_statement_set>", "split", ";", "<pick>"],
        ["λ"]],

    "<pick_statement_set>": [
        ["<statement_after>", "<pick_statement_set>"],
        ["λ"]],

    "<pattern>": [
        ["identifier"],
        ["<literal>"]],

    "<loop_statement>": [
        ["for", "(", "identifier", "=", "<arithmetic_expression>", ";", "<condition>", ";", "<incre_decre_option>", ")", "{", "<statement_set>", "}"],
        ["while", "(", "<condition>", ")", "{", "<statement_set>", "}"],
        ["do", "{", "<statement_set>", "}", "while", "(", "<condition>", ")", ";"]],

    "<incre_decre_option>": [
        ["identifier", "<incre_decre_op>"],
        ["<incre_decre_op>", "identifier"]],

    "<condition>": [
        ["<condition_operand>", "<condition_after>"]],

    "<condition_after>": [
        ["<condition_op>", "<condition_operand>", "<condition_after>"],
        ["λ"]],
        
    "<condition_operand>": [
        ["<arithmetic_expression>"],
        ["!", "(", "<expression>", ")"]],

    "<condition_op>": [
        ["=="],
        ["!="],
        ["<"],
        [">"],
        ["<="],
        [">="],
        ["&&"],
        ["||"],
        ["is"],
        ["isnot"]],

    "<out_scope>": [
        ["<out_value>", "<out_after>"],
        ["λ"]],

    "<out_after>": [
        ["+", "<out_value>", "<out_after>"], 
        ["λ"]],

    "<out_value>": [
        ["word_literal"],
        ["identifier", "<value_iden_after>"]],

    "<return_statement>": [
        ["return", "<return_value>", ";"]],

    "<return_value>": [
        ["<arithmetic_expression>"],
        ["λ"]],

}

def compute_first_set(cfg):
    first_set = {non_terminal: set() for non_terminal in cfg.keys()}

    def first_of(symbol):
        if symbol not in cfg:
            return {symbol} 

        if symbol in first_set and first_set[symbol]:
            return first_set[symbol]

        result = set()
        
        for production in cfg[symbol]:
            for sub_symbol in production:
                if sub_symbol not in cfg: # terminal
                    result.add(sub_symbol)
                    break  
                else: # non-terminal
                    sub_first = first_of(sub_symbol)
                    result.update(sub_first - {"λ"})  
                    if "λ" not in sub_first:
                        break  
            
            else: # all symbols in the production derive λ
                result.add("λ")

        first_set[symbol] = result
        return result

    for non_terminal in cfg:
        first_of(non_terminal)

    return first_set

def compute_follow_set(cfg, start_symbol, first_set):
    follow_set = {non_terminal: set() for non_terminal in cfg.keys()}
    follow_set[start_symbol].add("$")  

    changed = True  

    while changed:
        changed = False 
    
        for non_terminal, productions in cfg.items():
            for production in productions:
                for i, item in enumerate(production):
                    if item in cfg:  # nt only
                        follow_before = follow_set[item].copy()

                        if i + 1 < len(production):  # A -> <alpha>B<beta>
                            beta = production[i + 1]
                            if beta in cfg:  # if <beta> is a non-terminal
                                follow_set[item].update(first_set[beta] - {"λ"})
                                if "λ" in first_set[beta]:
                                    follow_set[item].update(follow_set[beta])
                            else:  # if <beta> is a terminal
                                follow_set[item].add(beta)
                        else:  # nothing follows B
                            follow_set[item].update(follow_set[non_terminal])

                        if follow_set[item] != follow_before:
                            changed = True  

    return follow_set

def compute_predict_set(cfg, first_set, follow_set):
    predict_set = {}  

    for non_terminal, productions in cfg.items():
        for production in productions:
            production_key = (non_terminal, tuple(production))  # A = (A,(prod))
            predict_set[production_key] = set()

            first_alpha = set()
            for symbol in production:
                if symbol in first_set:  # non-terminal
                    first_alpha.update(first_set[symbol] - {"λ"})
                    if "λ" not in first_set[symbol]:
                        break
                else:  # terminal
                    first_alpha.add(symbol)
                    break
            else:  
                first_alpha.add("λ")

            predict_set[production_key].update(first_alpha - {"λ"})

            # if λ in first_alpha, add follow set of lhs to predict set
            if "λ" in first_alpha:
                predict_set[production_key].update(follow_set[non_terminal])

    return predict_set

def gen_parse_table():
    parse_table = {}
    for (non_terminal, production), predict in predict_set.items():
        if non_terminal not in parse_table:
            parse_table[non_terminal] = {}
        for terminal in predict:
            if terminal in parse_table[non_terminal]:
                raise ValueError(f"Grammar is not LL(1): Conflict in parse table for {non_terminal} and {terminal}")
            parse_table[non_terminal][terminal] = production

    return parse_table  

first_set = compute_first_set(cfg)
follow_set = compute_follow_set(cfg, "<program>", first_set)
predict_set = compute_predict_set(cfg, first_set, follow_set)
parse_table = gen_parse_table()

class LL1Parser:
    def __init__(self, cfg, parse_table, follow_set):
        self.cfg = cfg
        self.parse_table = parse_table
        self.follow_set = follow_set
        self.symbol_stack = []  # Stack for grammar symbols
        self.input_tokens = []
        self.index = 0
        self.errors = []

    def parse(self, tokens):
        # Initialize stack
        self.symbol_stack = ["$", "<program>"]  # Start with end marker and start symbol
        self.input_tokens = tokens + [("$", "$", -1, 0)]  # Append EOF
        self.index = 0
        self.errors = []
        
        while self.symbol_stack:
            top_symbol = self.symbol_stack.pop()
            
            current_lexeme = self.input_tokens[self.index][0]
            current_token = self.input_tokens[self.index][1]  # Token type
            current_line = self.input_tokens[self.index][2]   # Line number
            current_column = self.input_tokens[self.index][3] # Column position

            # Skip null productions
            if top_symbol == "λ":
                continue

            # Terminal match
            if top_symbol not in self.cfg:  # a terminal
                if top_symbol == current_token:
                    self.index += 1
                else:
                    # Terminal mismatch = syntax error
                    self.syntax_error(current_line, current_lexeme, {top_symbol}, current_column, top_symbol)
                    return False, self.errors
            
            # Non-terminal processing
            elif top_symbol in self.cfg:  # It's a non-terminal
                if current_token in self.parse_table.get(top_symbol, {}):
                    production = self.parse_table[top_symbol][current_token]
                    
                    # Push reversed symbols to stack
                    for symbol in reversed(production):
                        if symbol != "λ":  # Skip null
                            self.symbol_stack.append(symbol)
                else:
                    # No production 
                    expected_tokens = set(self.parse_table.get(top_symbol, {}).keys())
                    self.syntax_error(current_line, current_lexeme, expected_tokens, current_column, top_symbol)
                    return False, self.errors
            
            # End marker
            elif top_symbol == "$":
                if current_token == "$":
                    break
                else:
                    self.syntax_error(current_line, current_lexeme, {"$"}, current_column, "$")
                    return False, self.errors
        
        # Check if we processed all input
        if self.index < len(self.input_tokens) - 1:
            remaining_token = self.input_tokens[self.index]
            self.syntax_error(remaining_token[2], remaining_token[0], {"EOF"}, remaining_token[3], None)
            return False, self.errors

        return True, []

    def syntax_error(self, line, found, expected, column, context_symbol):
        if line == -1 and column == 0:  # Use last valid line number if not set
            line = self.input_tokens[self.index - 1][2] if self.index > 0 else 1
            column = self.input_tokens[self.index - 1][3] if self.index > 0 else 1
        
        # Special case: declarations after statements
        # Check if we're expecting statements but found a declaration keyword
        declaration_keywords = {"num", "deci", "word", "single", "bool", "const", "struct"}
        statement_expected = {"identifier", "++", "--", "if", "while", "for", "do", "match", "out"}
        
        if (expected & statement_expected) and found in declaration_keywords:
            error_message = f"❌ Syntax Error at (line {line}, column {column}): All variable declarations must be at the top of the function body before any statements. Found '{found}' but declarations are not allowed here."
        # Build the error message
        elif not self.symbol_stack:  
            # Empty stack only report unexpected token
            error_message = f"❌ Syntax Error at (line {line}, column {column}): Unexpected '{found}'"
        elif found == '$':  
            # Special case: No unexpected token, just missing expected ones
            error_message = f"❌ Syntax Error at (line {line}, column {column}): Missing expected token(s): {', '.join(sorted(expected))}"
        else:
            # unexpected token and expected tokens
            error_message = f"❌ Syntax Error at (line {line}, column {column}): Unexpected '{found}'. Expected: {', '.join(sorted(expected))}"

        self.errors.append(error_message)

    def print_errors(self):
        if not self.errors:
            print("\n✅ No Syntax Errors Found.")
        else:
            print("\n⚠️ Syntax Errors:")
            for error in self.errors:
                print(error)