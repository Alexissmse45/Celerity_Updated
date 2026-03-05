# class Token:
#     def __init__(self, type, value, line, column):
#         self.type = type
#         self.value = value
#         self.line = line
#         self.column = column
    
#     def __repr__(self):
#         return f'Token({self.type}, {repr(self.value)}, line {self.line}, col {self.column})'
    
class Lexer: 
    def __init__(self): 
        self.errors = [] 
        self.space = {' '} 
        self.newln = {'\n', '\r'}
        self.whitespace = {' ','\n', '\t'}
        self.semicolon = {';'}
        self.colon = {':'}
        self.comma = {','}
        self.period = {'.'}
        self.zero = {'0'}
        self.number = set("123456789") 
        self.negative = {'~'}
        self.digit = set("0123456789")
        self.alphalow = set("abcdefghijklmnopqrstuvwxyz") 
        self.alphaup = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ") 
        self.alphabet = self.alphalow|self.alphaup
        self.alphadigit = self.alphabet|self.digit 
        self.bool = {'true', 'false'}
        self.oparith = {'+', '-', '*', '/', '%', '**'}
        self.opassign = {'=', '+=', '-=', '*=', '/=', '%=', '**='}
        self.oprelation = {'==', '!=', '<', '<=', '>', '>='}
        self.opunary = {'++', '--'}
        self.oplogical = {'&&', '||', '!'}
        self.delimop = {'+', '-', '*', '/', '%', '!', '&', '|', '<', '>', '=', ' '}
        self.escapeseq = {'\n', '\t'}

        self.asciicom = {chr(i) for i in range(32, 127) if chr(i) not in {'#', '*'}}
        self.ascii= {chr(i) for i in range(32, 127) if chr(i)}
        self.asciiword = {chr(i) for i in range(32, 127) if chr(i) != '"'}   # string: everything except double quote
        self.asciisingle = {chr(i) for i in range(32, 127) if chr(i) not in {'#', "'"}} # char: everything except single quote
        
        self.delimword = {')', '}', '+'} | self.comma | self.semicolon | self.space | self.colon
        self.delimsingle = {'}', ')'} | self.comma | self.semicolon | self.space | self.colon
        self.delimdigit = {'}', ')', ']'} | self.space | self.delimop | self.semicolon | self.colon | self.comma  #remove period
        self.delimiden = {'(', ')', '{', '}', '[', ']', '.'} | self.space | self.delimop | self.semicolon | self.colon | self.comma | self.newln #kulang sa delimiden "{,[" nag add rin ng newln here.
        self.parspace = {'('} | self.space
        self.curspace = {'{', '}'} | self.space | self.newln
        self.semispace = self.semicolon | self.space
        self.delim1 = self.space | self.colon
        self.delim2 = {')'} | self.comma | self.space | self.semicolon
        self.delim3 = {')'} | self.alphadigit | self.semicolon | self.space  #nagdagdag aq whitespace same sa delim4&5 
        self.delim4 = {';', '('} | self.alphadigit | self.space 
        self.delim5 = {'~', '(', '+' , '-'} | self.digit | self.space
        self.delim6 = {'('} | self.alphadigit 
        self.delim7 = {'~', '"', "'", '('} | self.alphadigit | self.space
        self.delim8 = {'~', '"', '(' , '{'} | self.alphadigit | self.space
        self.delim9 = {'(', ')', '!', "'", '"'} | self.alphadigit | self.space
        self.delim10 = {'{', ')', '<', '>', '=', '|', '&', '+', '-', '/', '*', '%', '"'} | self.semicolon | self.space | self.newln | self.colon | self.comma
        self.delim11 = {']'} | self.space | self.digit
        self.delim12 = {'=', '[', ')'} | self.space | self.newln | self.semicolon
        self.delim13 = {'{', "'", '"', '~'} | self.alphadigit | self.space | self.newln

        self.delim14 = {'}'} | self.semicolon | self.comma | self.alphabet | self.space | self.newln    
        self.delim15 = {'}', ')', ']'} | self.space | self.semicolon | self.comma | self.colon    
        self.delim16 = self.asciisingle | self.escapeseq | self.space
        self.delim17 = self.asciisingle | self.escapeseq | self.space
        
      
    def fetch_next_char(self):
        if self.position < len(self.source_code):
            char = self.source_code[self.position]
            print(f"Fetching char at pos {self.position}: {repr(char)}")  # debug print
            self.position += 1 # Move to next position
            return char
        return None # End of file reached

    def peek(self): # Looks at the next character without consuming it.
        if self.position < len(self.source_code): 
            return self.source_code[self.position]
        return None

    def step_back(self):
        """
        Moves the position pointer back by one character.
        Used when a delimiter is encountered that belongs to the next token.
        """
        if self.position > 0:
            self.position -= 1
                # For simplicity, we won't update line and column on rewind in this example.

    def lexeme(self, code):
        self.source_code = code  # Store the source code to analyze
        tokens = []  # List to store generated tokens
        self.position = 0  # Current position in source code
        state = 0  # Current state in the finite state machine
        lexeme = ""  # Current lexeme being built
        line = 1  # Current line number (for error reporting)
        column = 0  # Current column number (for error reporting)
        print("Lexing started...") 

        # Main tokenization loop - continues until end of source code
        while True: 
            char = self.fetch_next_char()  # Get next character
            column += 1  # Increment column counter

            # Check if we've reached end of file in initial state
            if char is None and state == 0:
                break # Exit main loop
            

            match state: 
                case 0: # Initial/reset state - starting point for each new token
                    lexeme = ""  # Clear the current lexeme

                    #spaces 
                    if char in self.whitespace: 
                        if char == '\n': 
                            line += 1 
                            column = 0 # Reset column counter
                        continue

                    # single-character tokens / galing sa state 0
                    elif char == 'b': # Could be 'bool' keyword
                        state = 1
                        lexeme += char
                    elif char == 'c': # Could be 'const' keyword
                        state = 6
                        lexeme += 'c'
                    elif char == 'd':
                        state = 12
                        lexeme += 'd'
                    elif char == 'e':
                        state = 21
                        lexeme += 'e'
                    elif char == 'f':
                        state = 29
                        lexeme += 'f'
                    elif char == 'i':
                        state = 46
                        lexeme += 'i'
                    elif char == 'm':
                        state = 57
                        lexeme += 'm'
                    elif char == 'n':
                        state = 66
                        lexeme += 'n'
                    elif char == 'o':
                        state = 70
                        lexeme += 'o'
                    elif char == 'p':
                        state = 74
                        lexeme += 'p'
                    elif char == 'r':
                        state = 79
                        lexeme += 'r'
                    elif char == 's':
                        state = 91
                        lexeme += 's'
                    elif char == 't':
                        state = 109
                        lexeme += 't'
                    elif char == 'v':
                        state = 114
                        lexeme += 'v'
                    elif char == 'w':
                        state = 121
                        lexeme += 'w'

                     # operators / punctuators | Reserved Symbols 
                    elif char == '+':
                        state = 131
                        lexeme += char
                    elif char == '-':
                        state = 137
                        lexeme += char
                    elif char == '*':
                        state = 143
                        lexeme += char
                    elif char == '/':
                        state = 151
                        lexeme += char
                    elif char == '%':
                        state = 155
                        lexeme += char
                    elif char == '>':
                        state = 159
                        lexeme += char
                    elif char == '<':
                        state = 163
                        lexeme += char
                    elif char == '!':
                        state = 167
                        lexeme += char
                    elif char == '&':
                        state = 171
                        lexeme += char
                    elif char == '|':
                        state = 174
                        lexeme += char
                    elif char == ',':
                        state = 177
                        lexeme += char
                    elif char == ':':
                        state = 179
                        lexeme += char
                    elif char == ';':
                        state = 181
                        lexeme += char
                                            # elif char == "'":
                                            #     state = 183
                                            #     lexeme += char
                                            # elif char == "'":
                                            #     state = 185
                                            #     lexeme += char
                                            # elif char == '"':
                                            #     state = 187
                                            #     lexeme += char
                                            # elif char == '"':
                                            #     state = 189
                                            #     lexeme += char
                    elif char == '(':
                        state = 183
                        lexeme += char
                    elif char == ')':
                        state = 185
                        lexeme += char
                    elif char == '[':
                        state = 187
                        lexeme += char
                    elif char == ']':
                        state = 189
                        lexeme += char
                    elif char == '{':
                        state = 191
                        lexeme += char
                    elif char == '}':
                        state = 193
                        lexeme += char
                    elif char == '=':
                        state = 195
                        lexeme += char
                    elif char == '.':
                        state = 199
                        lexeme += char
                    elif char == '#':
                        state = 201
                        lexeme += char

                    #num and deci Literals 
                    elif char == '0':
                        state = 203
                        lexeme += char

                    elif char.isdigit() and char != '0':
                        state = 206
                        lexeme += char

                    elif char == '~' : #tilde or lambda po yan
                        state = 205
                        lexeme += char

                    #single literals
                    elif char == "'":
                        state = 243
                        lexeme += "'"
                    #word literals
                    elif char == '"':
                        state = 247
                        lexeme += '"'
                    
                    elif char.isalpha():
                        state = 250
                        lexeme += char
                    
                    #error handling 
                    else: 
                        self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Character ( {repr(char)} ).") 

                 #keywords
                 # BOOL keyword recognition: states 1-5
                case 1:  # 'b'
                    if char == 'o': 
                        state = 2
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        # Not 'bool', treat as identifier
                        state = 252
                        lexeme += char
                    else:# Invalid delimiter after 'b'
                        if char in self.delimiden:
                            state = 253 # Finalize as identifier
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0 
                case 2:  # 'bo'
                    if char == 'o': 
                        state = 3
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0
                case 3:  # 'boo'
                    if char == 'l': 
                        state = 4
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0
                case 4:  # 'bool'
                    if char in self.space or char == '\t':
                        # Move to case 5 to finalize token
                        state = 5
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 5:  # Finalize 'bool' token
                    column -= 2
                    tokens.append((lexeme, "bool", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 6:  # 'c'
                    if char == 'o': 
                        state = 7
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0 

                case 7:  # 'co'
                    if char == 'n': 
                        state = 8
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0 
                
                case 8:  # 'con'
                    if char == 's': 
                        state = 9
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0 

                case 9:  # 'cons'
                    if char == 't': 
                        state = 10
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0 
                    
                case 10:  # 'const'
                    if char in self.space or char == '\t':
                        state = 11
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 11:  # Finalize 'const' token
                    column -= 2 
                    tokens.append((lexeme, "const", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 12:  # 'd' deci or do
                    if char == 'e': 
                        state = 13
                        lexeme += char
                    elif char == 'o': 
                        state = 19
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0 
                    
                case 13:  # 'de' decimal or def
                    if char == 'c': 
                        state = 14
                        lexeme += char
                    elif char == 'f' : 
                        state = 17
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0 
                    
                case 14:  # 'dec'
                    if char == 'i': 
                        state = 15
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0 
                        
                case 15:  # 'deci'
                    if char in self.space or char == '\t':
                        state = 16
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                
                case 16:  # Finalize 'deci' token
                    column -= 2
                    tokens.append((lexeme, "deci", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                
                case 17:  # 'def'
                    if char in self.delim1:
                        state = 18
                        if char is not None:
                            self.step_back()    
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                
                case 18:  # Finalize 'def' token
                    column -= 2 
                    tokens.append((lexeme, "def", line, column))
                    if char is not None:
                        self.step_back()    
                    state = 0

                case 19:  # 'do'
                    if char in self.curspace:
                        state = 20
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                
                case 20:  # Finalize 'do' token
                    column -= 2
                    tokens.append((lexeme, "do", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 21:  # 'e'
                    if char == 'l': 
                        state = 22
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0 
                        
                case 22:  # 'el'
                    if char == 's': 
                        state = 23
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0 
                    
                case 23:  # 'els'
                    if char == 'e': 
                        state = 24
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0 

                case 24:  # 'else'
                    if char in self.curspace:
                        state = 25
                        if char is not None:
                            self.step_back()

                    elif char == 'i' :  # to handle 'elseif' keyword
                        state = 26
                        lexeme += char

                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char  
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 25:  # Finalize 'else' token
                    column -= 2
                    tokens.append((lexeme, "else", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 26:  # 'elseif' continuation
                    if char == 'f': 
                        state = 27
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:   
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 27:  # 'elseif'
                    if char in self.parspace:
                        state = 28
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 28:  # Finalize 'elseif' token
                    column -= 2
                    tokens.append((lexeme, "elseif", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                
                case 29:  # 'f'
                    if char == 'a': 
                        state = 30
                        lexeme += char
                    elif char == 'o': 
                        state = 35
                        lexeme += char
                    elif char == 'u': 
                        state = 38
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 30:  # 'fa'
                    if char == 'l':
                        state = 31
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 31:  # 'fal'
                    if char == 's':
                        state = 32
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 32:  # 'fals'
                    if char == 'e':
                        state = 33
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 33:  # 'false'
                    if char in self.delim2:
                        state = 34
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 34:  # Finalize 'false' token
                    column -= 2 
                    tokens.append((lexeme, "false", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 35:  # 'fo'
                    if char == 'r': 
                        state = 36
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 36:  # 'for'
                    if char in self.parspace:
                        state = 37
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 37:  # Finalize 'for' token
                    column -= 2 
                    tokens.append((lexeme, "for", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 38:  # 'fu'
                    if char == 'n': 
                        state = 39
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 39:  # 'fun'
                    if char == 'c': 
                        state = 40
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0
                        
                case 40:  # 'func'
                    if char == 't': 
                        state = 41
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 41:  # 'funct'
                    if char == 'i':
                        state = 42
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 42:  # 'functi'
                    if char == 'o':
                        state = 43
                        lexeme += char 
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0
                        
                case 43:  # 'functio'
                    if char == 'n':
                        state = 44
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 44:  # 'function'
                    if char in self.space or char == '\t':
                        state = 45
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 45:  # Finalize 'function' token
                    column -= 2
                    tokens.append((lexeme, "function", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 46: # 'i'
                    if char == 'f': 
                        state = 47
                        lexeme += char

                    elif char =='n' :
                        state = 49  # to handle 'in' keyword
                        lexeme += char

                    elif char == 's': 
                        state = 51  # to handle 'is' keyword
                        lexeme += char

                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 47:  # 'if'
                    if char in self.parspace:
                        state = 48
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 48:  # Finalize 'if' token
                    column -= 2 
                    tokens.append((lexeme, "if", line, column))
                    if char is not None:
                        self.step_back()    
                    state = 0   

                case 49:  # 'in'
                    if char in self.parspace:
                        state = 50
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 50:  # Finalize 'in' token
                    column -= 2
                    tokens.append((lexeme, "in", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 51:  # 'is'
                    if char in self.space or char == '\t':
                        state = 52
                        if char is not None:
                            self.step_back()
                    elif char == 'n':  # to handle 'isnot' keyword
                        state = 53
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 52:  # Finalize 'is' token
                    column -= 2     
                    tokens.append((lexeme, "is", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 53:  # 'isn'
                    if char == 'o':
                        state = 54
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 54:  # 'isno'
                    if char == 't':
                        state = 55
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 55:  # 'isnot'
                    if char in self.space or char == '\t':
                        state = 56
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 56:  # Finalize 'isnot' token
                    column -= 2
                    tokens.append((lexeme, "isnot", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0   
                
                case 57: #'m'
                    if char == 'a':
                        state = 58
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 58:  # 'ma'
                    if char == 'i':
                        state = 59
                        lexeme += char
                    
                    elif char == 't': # to handle 'match' keyword
                        state = 62
                        lexeme += char

                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 59:  # 'mai'
                    if char == 'n':
                        state = 60
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 60:  # 'main'
                    if char is None or char in self.parspace:
                        state = 61
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 61:  # Finalize 'main' token
                    column -= 2 
                    tokens.append((lexeme, "main", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 62:  # 'mat'
                    if char == 'c':
                        state = 63
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 63:  # 'matc'
                    if char == 'h':
                        state = 64
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 64:  # 'match'
                    if char in self.parspace:
                        state = 65
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 65:  # Finalize 'match' token
                    column -= 2
                    tokens.append((lexeme, "match", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 66: #'n'
                    if char == 'u':
                        state = 67
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 67: #'nu'
                    if char == 'm':
                        state = 68
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 68: #'num'
                    if char in self.space or char == '\t':
                        state = 69
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                    
                case 69: # Finalize num token
                    column -= 2
                    tokens.append((lexeme, "num", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 70: #'o'
                    if char == 'u':
                        state = 71
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 71: #'ou'
                    if char == 't':
                        state = 72
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 72: #'out'
                    if char in self.parspace:
                        state = 73
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                    
                case 73: # Finalize out token
                    column -= 2
                    tokens.append((lexeme, "out", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 74: # p
                    if char == 'i': 
                        state = 75
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0 
                case 75:  # 'pi'
                    if char == 'c': 
                        state = 76
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0
                case 76:  # 'pic'
                    if char == 'k': 
                        state = 77
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0
                case 77:  # 'pick'
                    if char in self.space or char == '\t':
                        state = 78
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 78:  # Finalize 'pickl' token
                    column -= 2
                    tokens.append((lexeme, "pick", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 79: # 'r'
                    if char == 'e': 
                        state = 80
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 80:  # 're'
                    if char == 's': 
                        state = 81
                        lexeme += char
                    
                    elif char == 't':
                        state = 86
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 81:  # 'res'
                    if char == 'u': 
                        state = 82
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 82:  # 'resu'
                    if char == 'm': 
                        state = 83
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 83:  # 'resum'
                    if char == 'e': 
                        state = 84
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0
                    
                case 84: # 'resume'
                    if char in self.semispace:
                        state = 85
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 85:  # Finalize 'reusme' token
                    column -= 2
                    tokens.append((lexeme, "resume", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 86: # 'ret'
                    if char == 'u': 
                        state = 87
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0 

                case 87: # 'retu'
                    if char == 'r': 
                        state = 88
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0 
                        
                case 88: # 'retur'
                    if char == 'n': 
                        state = 89
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0 
                    
                case 89: # 'return'
                    if char in self.space or char == '\t':
                        state = 90
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 90:  # Finalize 'return' token
                    column -= 2
                    tokens.append((lexeme, "return", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 91: # 's'
                    if char == 'i': 
                        state = 92
                        lexeme += char

                    elif char == 'p':
                        state = 98
                        lexeme += char

                    elif char == 't':
                        state = 103
                        lexeme += char
                        
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 92: # 'si'
                    if char == 'n': 
                        state = 93
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 93: # 'sin'
                    if char == 'g': 
                        state = 94
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0
                
                case 94: # 'sing'
                    if char == 'l': 
                        state = 95
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 95: # 'singl'
                    if char == 'e': 
                        state = 96
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 96: # 'single'
                    if char in self.space or char == '\t':
                        state = 97
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 97:# Finalize 'single' token
                    column -= 2
                    tokens.append((lexeme, "single", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 98:  # 'sp'
                    if char == 'l': 
                        state = 99
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 99:  # 'spl'
                    if char == 'i': 
                        state = 100
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0
                
                case 100:  # 'spli'
                    if char == 't': 
                        state = 101
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 101: # 'split'
                    if char in self.semispace:
                        state = 102
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 102:  # Finalize 'split' token
                    column -= 2
                    tokens.append((lexeme, "split", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 103: # 'st'
                    if char == 'r': 
                        state = 104
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 104: # 'str'
                    if char == 'u': 
                        state = 105
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 105: # 'stru'
                    if char == 'c': 
                        state = 106
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 106: # 'struc'
                    if char == 't': 
                        state = 107
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 107: # 'struct'
                    if char in self.space or char == '\t':
                        state = 108
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 108: # Finalize 'struct' token
                    column -= 2
                    tokens.append((lexeme, "struct", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 109: # 't'
                    if char == 'r': 
                        state = 110
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0 
                        
                case 110: # 'tr'
                    if char == 'u': 
                        state = 111
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0 

                case 111: # 'tru'
                    if char == 'e': 
                        state = 112
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0 

                case 112: # 'true'
                    if char in self.delim2:
                        state = 113
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 113: # Finalize 'true' token
                    column -= 2
                    tokens.append((lexeme, "true", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 114: # 'v'
                    if char == 'a': 
                        state = 115
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0 
                
                case 115: # 'va'
                    if char == 'c': 
                        state = 116
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0 

                case 116: # 'vac'
                    if char == 'a': 
                        state = 117
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0 

                case 117: # 'vaca'
                    if char == 'n': 
                        state = 118
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0

                case 118: # 'vacan'
                    if char == 't': 
                        state = 119
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0  

                case 119: # 'vacant'
                    if char in self.space or char == '\t':
                        state = 120
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 120: # Finalize 'vacant' token
                    column -= 2
                    tokens.append((lexeme, "vacant", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 121: # 'w'
                    if char == 'h': 
                        state = 122
                        lexeme += char
                    elif char == 'o':
                        state = 127
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0
                case 122: # 'wh'
                    if char == 'i': 
                        state = 123
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0                 
                case 123: # 'whi'
                    if char == 'l': 
                        state = 124
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0
                case 124: # 'whil'
                    if char == 'e': 
                        state = 125
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0
                case 125: # 'while'
                    if char in self.parspace:
                        state = 126
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 126: # Finalize 'while' token
                    column -= 2
                    tokens.append((lexeme, "while", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 127: #wo
                    if char == 'r': 
                        state = 128
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0
                case 128: #wor
                    if char == 'd': 
                        state = 129
                        lexeme += char
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        if char in self.delimiden:
                            state = 253
                            if char is not None:
                                self.step_back()
                        else:
                            column -= 1
                            if char is None:

                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                            else:
                                self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                                if char == '\n':
                                    column = 0
                                if char is not None:
                                    self.step_back()
                            state = 0
                case 129: #word
                    if char in self.space or char == '\t':
                        state = 130
                        if char is not None:
                            self.step_back()
                    elif char is not None and (char.isalpha() or char.isdigit() or char == '_'):
                        state = 252
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 130: # Finalize 'word' token
                    column -= 2
                    tokens.append((lexeme, "word", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                #Operators
                case 131:# '+'
                    if char is  None or char in self.delim7:
                        state = 132
                        if char is not None:
                            self.step_back()
                    elif char == '+':
                        state = 133
                        lexeme += char
                    elif char == '=':
                        state = 135
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 132: # Finalize 'PLUS' token
                    column -= 2
                    tokens.append((lexeme, "+", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 133: # '++'
                    if char in self.delim4:
                        state = 134
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 134: # Finalize 'INCREMENT' token
                    column -= 2
                    tokens.append((lexeme, "++", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 135: # '+='
                    if char is  None or char in self.delim4:
                        state = 136
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 136: # Finalize 'PLUS ASSIGN' token
                    column -= 2
                    tokens.append((lexeme, "+=", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 137: # '-'
                    if char is  None or char in self.delim4:
                        state = 138
                        if char is not None:
                            self.step_back()
                    elif char == '-':
                        state = 139
                        lexeme += char

                    elif char == '=':
                        state = 141
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 138: # Finalize 'MINUS' token
                    column -= 2
                    tokens.append((lexeme, "-", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 139: # '--'
                    if char in self.delim3:
                        state = 140
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 140: # Finalize '--' token
                    column -= 2
                    tokens.append((lexeme, "--", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 141:  # -=
                    if char in self.delim4:
                        state = 142
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 142: # Finalize '-=' token
                    column -= 2
                    tokens.append((lexeme, "-=", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                
                case 143: # '*'
                    if char in self.delim4:
                        state = 144
                        if char is not None:
                            self.step_back()
                    elif char == '=':
                        state = 145
                        lexeme += char

                    elif char == '*':
                        state = 147
                        lexeme += char

                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 144: # Finalize '*' token
                    column -= 2
                    tokens.append((lexeme, "*", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 145: # '*='
                    if char in self.delim4:
                        state = 146
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 146: # Finalize '*=' token
                    column -= 2
                    tokens.append((lexeme, "*=", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 147: # '**'
                    if char in self.delim4:
                        state = 148
                        if char is not None:
                            self.step_back()
                    elif char == '=':
                        state = 149
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0

                case 148: #Finalize '**' token
                    column -= 2
                    tokens.append((lexeme, "**", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 149: # '**='
                    if char in self.delim4:
                        state = 150
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 150: #Finalize '**=' token
                    column -= 2
                    tokens.append((lexeme, "**=", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 151: # /
                    if char in self.delim4:
                        state = 152
                        if char is not None:
                            self.step_back()
                    elif char == '=':
                        state = 153
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 152: # Finalize '/' token
                    column -= 2
                    tokens.append((lexeme, "/", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 153:# /=
                    if char in self.delim4:
                        state = 154
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 154:# Finalize '/=' token
                    column -= 2
                    tokens.append((lexeme, "/=", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 155: # %
                    if char in self.delim4:
                        state = 156
                        if char is not None:
                            self.step_back()
                    elif char == '=':
                        state = 157
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 156: # Finalize '%' token
                    column -= 2
                    tokens.append((lexeme, "%", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 157:# %=
                    if char in self.delim4:
                        state = 158
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 158:# Finalize '%=' token
                    column -= 2
                    tokens.append((lexeme, "%=", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

                case 159: # >
                    if char in self.delim4:
                        state = 160
                        if char is not None:
                            self.step_back()
                    elif char == '=':
                        state = 161
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 160: # Finalize '>' token
                    column -= 2
                    tokens.append((lexeme, ">", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 161:# >=
                    if char in self.delim4:
                        state = 162
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 162:# Finalize '>=' token
                    column -= 2
                    tokens.append((lexeme, ">=", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 163: # <
                    if char in self.delim4:
                        state = 164
                        if char is not None:
                            self.step_back()
                    elif char == '=':
                        state = 165
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 164: # Finalize '<' token
                    column -= 2
                    tokens.append((lexeme, "<", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 165:# <=
                    if char in self.delim4:
                        state = 166
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 166:# Finalize '<=' token
                    column -= 2
                    tokens.append((lexeme, "<=", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 167: # !
                    if char in self.delim6:
                        state = 168
                        if char is not None:
                            self.step_back()
                    elif char == '=':
                        state = 169
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 168: # Finalize '!' token
                    column -= 2
                    tokens.append((lexeme, "!", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 169:# !=
                    if char in self.delim7:
                        state = 170
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 170:# Finalize '!=' token
                    column -= 2
                    tokens.append((lexeme, "!=", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 171:# &
                    if char == '&':
                        state = 172
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 172:# &&
                    if char in self.delim4:
                        state = 173
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 173: #Finalize '&&' token
                    column -= 2
                    tokens.append((lexeme, "&&", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 174:# |
                    if char == '|':
                        state = 175
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 175:# ||
                    if char in self.delim4:
                        state = 176
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 176: #Finalize '||' token
                    column -= 2
                    tokens.append((lexeme, "||", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 177:# ,
                    if char in self.delim8:
                        state = 178
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 178: #Finalize ',' token
                    column -= 2
                    tokens.append((lexeme, ",", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 179: 
                    if char in self.whitespace:
                        state = 180
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 180:  # Finalize ':' token
                    column -= 2
                    tokens.append((lexeme, ":", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 181: 
                    if char is None or char in self.whitespace:
                        state = 182
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 182:  # Finalize ';' token
                    column -= 2
                    tokens.append((lexeme, ";", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 183: #(
                    if char in self.delim9:
                        state = 184
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 184:# Finalize '(' token
                    column -= 2
                    tokens.append((lexeme, "(", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 185:#)
                    if char in self.delim10:
                        state = 186
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 186:# Finalize ')' token
                    column -= 2
                    tokens.append((lexeme, ")", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 187:#[
                    if char in self.delim11:
                        state = 188
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 188:# Finalize '[' token
                    column -= 2
                    tokens.append((lexeme, "[", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 189:#]
                    if char in self.delim12:
                        state = 190
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 190:# Finalize ']' token
                    column -= 2
                    tokens.append((lexeme, "]", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 191:#{
                    if char in self.delim13:
                        state = 192
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 192:# Finalize '{ token
                    column -= 2
                    tokens.append((lexeme, "{", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 193:#}
                    if char in self.delim14:
                        state = 194
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0 #mag babato ng error if di ka nag lagay ng space after }
                        
                case 194:# Finalize '}' token
                    column -= 2
                    tokens.append((lexeme, "}", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 195:#=
                    if char in self.delim8:
                        state = 196
                        if char is not None:
                            self.step_back()
                    elif char == '=':
                        state = 197
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 196:# Finalize '=' token
                    column -= 2
                    tokens.append((lexeme, "=", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 197:#==
                    if char in self.delim7:
                        state = 198
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 198:# Finalize '==' token
                    column -= 2
                    tokens.append((lexeme, "==", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 199:# .
                    if char in self.alphadigit:
                        state = 200
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 200:#Finalize '.' token
                    column -= 2
                    tokens.append((lexeme, ".", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 201:# #
                    if char in self.ascii:
                        state = 201
                    elif char == '\n':
                        line += 1
                        state = 255
                    elif char == '#':
                        state = 254
                    elif char == '*':
                        state = 256
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Symbol'{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 202:#Finalize '#' token
                    if char is not None:
                        self.step_back()
                    state = 0

            #int and decimal Literals
                case 203:# zero
                    if char in self.delimdigit:
                        state = 204
                        if char is not None:
                            self.step_back()
                    elif char == '.':
                            state = 224
                            lexeme += char
                    elif char and char.isdigit():
                        lexeme += char
                        self.errors.append(f"(Line {line}, Column {column}): Num Literal '{lexeme}' leading zero is not allowed.")
                        state = 0
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                        state = 0
                case 204:# Finalize 'Int-Literal' token
                    column -= 2
                    tokens.append((lexeme, "num_literal", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 205:
                    if char in self.digit and char != 0:
                        state = 206
                        lexeme += char
                    elif char == '0':
                        state = 261
                        lexeme += char
                    elif char == '.':
                        state = 224
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                        state = 0
                case 206:
                    if char in self.delimdigit:
                        state = 207
                        if char is not None:
                            self.step_back()
                    elif char and char.isdigit():
                        state = 208
                        lexeme += char
                    elif char == '.':
                        state = 224
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                        state = 0
                case 207:
                    column -= 2
                    tokens.append((lexeme, "num_literal", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 208: 
                    if char in self.delimdigit:
                        state = 209
                        if char is not None:
                            self.step_back()
                    elif char and char.isdigit():
                        state = 210
                        lexeme += char
                    elif char == '.':
                        state = 224
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                        state = 0
                case 209:
                    column -= 2
                    tokens.append((lexeme, "num_literal", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 210: 
                    if char in self.delimdigit:
                        state = 211
                        if char is not None:
                            self.step_back()
                    elif char and char.isdigit():
                        state = 212
                        lexeme += char
                    elif char == '.':
                        state = 224
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                        state = 0
                case 211:
                    column -= 2
                    tokens.append((lexeme, "num_literal", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 212:
                    if char in self.delimdigit:
                        state = 213
                        if char is not None:
                            self.step_back()
                    elif char and char.isdigit():
                        state = 214
                        lexeme += char
                    elif char == '.':
                        state = 224
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                        state = 0
                case 213:
                    column -= 2
                    tokens.append((lexeme, "num_literal", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 214: 
                    if char in self.delimdigit:
                        state = 215
                        if char is not None:
                            self.step_back()
                    elif char and char.isdigit():
                        state = 216
                        lexeme += char
                    elif char == '.':
                        state = 224
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                        state = 0
                case 215:
                    column -= 2
                    tokens.append((lexeme, "num_literal", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 216:
                    if char in self.delimdigit:
                        state = 217
                        if char is not None:
                            self.step_back()
                    elif char and char.isdigit():
                        state = 218
                        lexeme += char
                    elif char == '.':
                        state = 224
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                        state = 0
                case 217:
                    column -= 2
                    tokens.append((lexeme, "num_literal", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 218:
                    if char in self.delimdigit:
                        state = 219
                        if char is not None:
                            self.step_back()
                    elif char and char.isdigit():
                        state = 220
                        lexeme += char
                    elif char == '.':
                        state = 224
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                        state = 0
                case 219:
                    column -= 2
                    tokens.append((lexeme, "num_literal", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 220:
                    if char in self.delimdigit:
                        state = 221
                        if char is not None:
                            self.step_back()
                    elif char and char.isdigit():
                        state = 222
                        lexeme += char
                    elif char == '.':
                        state = 224
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                        state = 0
                case 221:
                    column -= 2
                    tokens.append((lexeme, "num_literal", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 222:
                    if char in self.delimdigit:
                        state = 223
                        if char is not None:
                            self.step_back()
                    elif char and char.isdigit():
                        # DON'T append char to lexeme — error is on the 9 digits only
                        self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' exceeds 9 digit limit.'")
                        # Step back so the 10th digit starts a NEW token
                        self.step_back()
                        state = 0
                    elif char == '.':
                        state = 239
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Num Literal '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                        state = 0
                case 223: 
                    column -= 2
                    tokens.append((lexeme, "num_literal", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 224:
                    if char and char.isdigit():
                        state = 225
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Decimal Literal '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Decimal Literal '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                        state = 0
                case 225:
                    if char in self.delimdigit:
                        state = 226
                        if char is not None:
                            self.step_back()
                    elif char and char.isdigit():
                        state = 227
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Decimal Literal '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Decimal Literal '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                        state = 0
                case 226:
                    column -= 2
                    tokens.append((lexeme, "deci_literal", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 227:
                    if char in self.delimdigit:
                        state = 228
                        if char is not None:
                            self.step_back()
                    elif char and char.isdigit():
                        state = 229
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Decimal Literal '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Decimal Literal '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                        state = 0
                case 228:
                    column -= 2
                    tokens.append((lexeme, "deci_literal", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 229:
                    if char in self.delimdigit:
                        state = 230
                        if char is not None:
                            self.step_back()
                    elif char and char.isdigit():
                        state = 231
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Decimal Literal '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Decimal Literal '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                        state = 0
                case 230:
                    column -= 2
                    tokens.append((lexeme, "deci_literal", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 231:
                    if char in self.delimdigit:
                        state = 232
                        if char is not None:
                            self.step_back()
                    elif char and char.isdigit():
                        state = 233
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Decimal Literal '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Decimal Literal '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                        state = 0
                case 232:
                    column -= 2
                    tokens.append((lexeme, "deci_literal", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 233:
                    if char in self.delimdigit:
                        state = 234
                        if char is not None:
                            self.step_back()
                    elif char and char.isdigit():
                        state = 235
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Decimal Literal '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Decimal Literal '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                        state = 0
                case 234:
                    column -= 2
                    tokens.append((lexeme, "deci_literal", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 235:
                    if char in self.delimdigit:
                        state = 236
                        if char is not None:
                            self.step_back()
                    elif char and char.isdigit():
                        state = 237
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Decimal Literal '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Decimal Literal '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                        state = 0
                case 236:
                    column -= 2
                    tokens.append((lexeme, "deci_literal", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 237:
                    if char in self.delimdigit:
                        state = 238
                        if char is not None:
                            self.step_back()
                    elif char and char.isdigit():
                        state = 239
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Decimal Literal '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Decimal Literal '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                        state = 0
                case 238:
                    column -= 2
                    tokens.append((lexeme, "deci_literal", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 239:
                    if char in self.delimdigit:
                        state = 240
                        if char is not None:
                            self.step_back()
                    elif char and char.isdigit():
                        state = 241
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Decimal Literal '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Decimal Literal '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                        state = 0
                case 240:
                    column -= 2
                    tokens.append((lexeme, "deci_literal", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 241:
                    if char in self.delimdigit:
                        state = 242
                        if char is not None:
                            self.step_back()
                    elif char and char.isdigit():
                        lexeme += char
                        self.errors.append(f"(Line {line}, Column {column}): decimal '{lexeme}' exceeds 9 digit limit.'")
                        state = 0
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Decimal Literal '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Decimal Literal '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                        state = 0
                case 242:
                    column -= 2
                    tokens.append((lexeme, "deci_literal", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0

            #single Literal: 
                case 243:
                    if char in self.asciisingle:
                        state = 244
                        lexeme += char
                    elif char == '#':
                        state = 262
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 244:
                    if char == "'":
                        state = 245
                        lexeme += char
                    else:
                        self.errors.append(f"(Line {line}, Column {column}): {lexeme} Expected (').")
                        if char is not None:
                            self.step_back()
                        state = 0
                case 245:
                    if char in self.delimsingle:
                        state = 246
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}):  '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 246: 
                    column -= 2
                    tokens.append((lexeme, "single_literal", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0   
                case 247:
                    if char in self.asciiword:
                        state = 247
                        lexeme += char
                    elif char == '"':  # Empty string case
                        state = 248
                        lexeme += char
                    else:
                        self.errors.append(f"(at Line {line}, Column {column}): {lexeme} Expected character ( \" ).")
                        if char is not None:
                            self.step_back()
                        state = 0
                case 248:
                    if char in self.delimword:
                        state = 249
                        if char is not None:
                            self.step_back()
                    else: 
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}):  '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Invalid Delimiter ( {repr(char)} ).")
                            if char is not None:
                                self.step_back()
                        state = 0
                case 249: 
                    column -= 2
                    tokens.append((lexeme, "word_literal", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0 

                # Identifier (State 250 - 254) first stage sa pag build
                case 250: 
                    if char and (char.isalpha() or char.isdigit() or char == '_'):
                        lexeme += char
                        state = 252
                    elif char in self.delimiden:
                        state = 251
                        if char is not None:
                            self.step_back()
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 251:
                    column -= 2
                    tokens.append((lexeme, "identifier", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
                case 252:
                    if char and (char.isalpha() or char.isdigit() or char == '_'):
                        lexeme += char
                        if len(lexeme) > 25:  # Identifier limit
                            self.errors.append(f"(Line {line}, Column {column}): Identifier '{lexeme}' exceeds 25 characters.")
                            state = 0
                    elif char in self.delimiden:
                        state = 253
                        if char is not None:
                            self.step_back()   
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0
                case 253:
                    column -= 2
                    tokens.append((lexeme, "identifier", line, column))
                    if char is not None:
                        self.step_back()
                    state = 0
             #comment
                case 254:
                    if char in self.ascii:
                        state = 254
                    elif char == '\n':
                        line += 1
                        state = 255
                    else:
                        if char is not None:
                            self.step_back()
                        state = 0
                case 255:
                    if char is not None:
                        self.step_back()
                    state = 0
                case 256:
                    if char in self.asciicom:
                        state = 257
                    elif char == '\n':
                        line += 1
                        state = 257
                    elif char == '*':
                        state = 258
                    else:
                        if char is not None:
                            self.step_back()
                        state = 0
                case 257:
                    if char in self.asciicom:
                        state = 257
                    elif char == '\n':
                        line += 1
                        state = 257
                    elif char == '*' and self.peek() == '#':
                        state = 258
                    else:
                        column -= 1
                        state = 257
                case 258:
                    if char == '#':
                        state = 259
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Comment '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Comment '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                        state = 0
                case 259:
                    if char == '\n':
                        line += 1
                        state = 260
                    else:
                        if char is not None:
                            self.step_back()
                        state = 0
                case 260:
                    if char is not None:
                        self.step_back()
                    state = 0
            #Redundancy
                case 261:
                    if char == '.':
                        state = 224
                        lexeme += char
                    elif char and char.isdigit():
                        lexeme += char
                        self.errors.append(f"(Line {line}, Column {column}): '{lexeme}' leading zero is not allowed.")
                        state = 0
                    else: 
                        self.errors.append(f"(Line {line}, Column {column}): Negative zero can only be followed by a period.")
                        state = 0
                case 262:
                    if char == '0':
                        state = 244
                        lexeme += char
                    else:
                        column -= 1
                        if char is None:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Missing Delimiter.")
                        else:
                            self.errors.append(f"(at Line {line}, Column {column}): Identifier '{lexeme}' Invalid Delimiter ( {repr(char)} ).")
                            if char == '\n':
                                column = 0
                            if char is not None:
                                self.step_back()
                        state = 0             
                        
        return tokens, self.errors
  
