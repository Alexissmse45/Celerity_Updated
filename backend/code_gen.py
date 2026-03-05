# =============================================================================
#  code_gen.py  —  Code Generator for the Celerity Language
# =============================================================================

class TACStructDef:
    def __init__(self, name, fields):
        self.name   = name
        self.fields = fields
    def __repr__(self):
        return f"struct_def {self.name}"

class TACDeclare:
    def __init__(self, c_type, name, init=None, is_const=False):
        self.c_type   = c_type
        self.name     = name
        self.init     = init
        self.is_const = is_const
    def __repr__(self):
        prefix = "const " if self.is_const else ""
        tail   = f" = {self.init}" if self.init is not None else ""
        return f"declare {prefix}{self.c_type} {self.name}{tail}"

class TACArrayDeclare:
    def __init__(self, c_type, name, dims, init=None):
        self.c_type = c_type
        self.name   = name
        self.dims   = dims
        self.init   = init
    def __repr__(self):
        return f"array_declare {self.c_type} {self.name}{''.join(f'[{d}]' for d in self.dims)}"

class TACBinOp:
    def __init__(self, result, left, op, right):
        self.result = result
        self.left   = left
        self.op     = op
        self.right  = right
    def __repr__(self):
        return f"{self.result} = {self.left} {self.op} {self.right}"

class TACUnary:
    def __init__(self, result, op, operand, post=False):
        self.result  = result
        self.op      = op
        self.operand = operand
        self.post    = post
    def __repr__(self):
        if self.post:
            return f"{self.result}{self.op}"
        return f"{self.result} = {self.op}{self.operand}"

class TACAssign:
    def __init__(self, result, operand):
        self.result  = result
        self.operand = operand
    def __repr__(self):
        return f"{self.result} = {self.operand}"

class TACCall:
    def __init__(self, result, func, args):
        self.result = result
        self.func   = func
        self.args   = args
    def __repr__(self):
        a   = ", ".join(self.args)
        lhs = f"{self.result} = " if self.result else ""
        return f"{lhs}call {self.func}({a})"

class TACPrint:
    def __init__(self, value, fmt, newline=True):
        self.value   = value
        self.fmt     = fmt
        self.newline = newline
    def __repr__(self):
        nl = "" if self.newline else " (no_nl)"
        return f"print[{self.fmt}]{nl} {self.value}"

class TACReturn:
    def __init__(self, value=None):
        self.value = value
    def __repr__(self):
        return f"return {self.value}" if self.value else "return"

class TACLabel:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"{self.name}:"

class TACGoto:
    def __init__(self, label):
        self.label = label
    def __repr__(self):
        return f"goto {self.label}"

class TACIfFalse:
    def __init__(self, cond, label):
        self.cond  = cond
        self.label = label
    def __repr__(self):
        return f"if_false {self.cond} goto {self.label}"

class TACFuncBegin:
    def __init__(self, ret_type, name, params):
        self.ret_type = ret_type
        self.name     = name
        self.params   = params
    def __repr__(self):
        return f"func_begin {self.ret_type} {self.name}({', '.join(self.params)})"

class TACFuncEnd:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"func_end {self.name}"


class CodeGenerator:

    PRECEDENCE = {
        "||":    1,
        "&&":    2,
        "is":    3, "isnot": 3, "==": 3, "!=": 3,
        "<":     4, ">":     4, "<=": 4, ">=": 4,
        "+":     5, "-":     5,
        "*":     6, "/":     6, "%":  6,
        "**":    7,
    }

    TYPE_MAP = {
        "num":    "int",
        "deci":   "double",
        "word":   "char*",
        "single": "char",
        "bool":   "bool",
        "vacant": "void",
    }

    def __init__(self):
        self.tac          = []
        self.tokens       = []
        self.pos          = 0
        self.var_types    = {"global": {}}
        self.scope        = "global"
        self.struct_defs  = {}
        self._temp_n      = 0
        self._label_n     = 0

    def generate(self, tokens):
        self.tokens    = tokens
        self.pos       = 0
        self.tac       = []
        self.var_types = {"global": {}}
        self.scope     = "global"
        self._temp_n   = 0
        self._label_n  = 0
        self._parse_program()
        user_lines   = self._emit_c()
        helper_lines = self._helpers()
        full_c = "\n".join(helper_lines) + "\n\n" + "\n".join(user_lines)
        user_c = "\n".join(user_lines).strip()
        return full_c, user_c

    def _tmp(self):
        n = f"_t{self._temp_n}"; self._temp_n += 1; return n

    def _lbl(self, hint="L"):
        n = f"_{hint}{self._label_n}"; self._label_n += 1; return n

    def _reg(self, name, lang_type):
        if self.scope not in self.var_types:
            self.var_types[self.scope] = {}
        self.var_types[self.scope][name] = lang_type

    def _type_of(self, name):
        local = self.var_types.get(self.scope, {})
        if name in local: return local[name]
        return self.var_types.get("global", {}).get(name)

    def _tok(self, offset=0):
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else (None, None, 0, 0)

    def _lex(self, offset=0): return self._tok(offset)[0]
    def _typ(self, offset=0): return self._tok(offset)[1]

    def _eat(self):
        t = self._tok(); self.pos += 1; return t

    def _expect(self, value): return self._eat()

    def _ctype(self, lang):
        return self.TYPE_MAP.get(lang, lang)

    def _default(self, lang):
        return {"num":"0","deci":"0.0","word":'""',"single":"' '","bool":"false"}.get(lang,"0")

    def _fmt(self, lang):
        return {"num":"%d","deci":"%f","single":"%c","word":"%s","bool":"bool"}.get(lang,"%s")

    def _read_fn(self, lang):
        return {"num":"read_int","deci":"read_double","single":"read_char",
                "word":"read_word","bool":"read_bool"}.get(lang,"read_word")

    def _fix_neg(self, lex):
        if lex and lex.startswith("~"): return "-" + lex[1:]
        return lex

    def _parse_program(self):
        while self.pos < len(self.tokens):
            t = self._typ()
            if t == "struct":
                if self._lex(2) == "{": self._parse_struct_def()
                else:                   self._parse_struct_var()
            elif t == "const":                           self._parse_const()
            elif t in ("num","deci","word","single","bool"): self._parse_var_decl()
            elif t in ("function","vacant","main"):          self._parse_function()
            else: self._eat()

    def _parse_struct_def(self):
        self._eat()
        name = self._eat()[0]
        self._eat()
        fields = []
        self.struct_defs[name] = {}
        while self._lex() != "}":
            lang  = self._eat()[0]
            fname = self._eat()[0]
            self.struct_defs[name][fname] = lang
            fields.append((self._ctype(lang), fname))
            if self._lex() == ";": self._eat()
        self._eat()
        self.tac.append(TACStructDef(name, fields))

    def _parse_struct_var(self):
        self._eat()
        struct_name = self._eat()[0]
        var_name    = self._eat()[0]
        self._reg(var_name, f"struct_{struct_name}")
        if self._lex() == "=":
            self._eat()
            init_vals = self._parse_brace_list()
            init_str  = f"(struct {struct_name}){{{', '.join(init_vals)}}}"
            self.tac.append(TACDeclare(f"struct {struct_name}", var_name, init_str))
        else:
            self.tac.append(TACDeclare(f"struct {struct_name}", var_name))
        if self._lex() == ";": self._eat()

    def _parse_const(self):
        self._eat()
        lang  = self._eat()[0]
        ctype = self._ctype(lang)
        while True:
            name = self._eat()[0]
            self._reg(name, lang)
            self._eat()
            val  = self._fix_neg(self._eat()[0])
            self.tac.append(TACDeclare(ctype, name, val, is_const=True))
            if self._lex() == ";": self._eat(); break
            elif self._lex() == ",": self._eat()

    def _parse_var_decl(self):
        lang  = self._eat()[0]
        ctype = self._ctype(lang)
        while True:
            name = self._eat()[0]
            self._reg(name, lang)
            if self._lex() == "[":
                self._parse_array_decl(lang, ctype, name)
                break  # _parse_array_decl consumes everything including ";"
            elif self._lex() == "=":
                self._eat()
                if self._typ() == "in":
                    self._eat(); self._eat(); self._eat()
                    tmp = self._tmp()
                    self.tac.append(TACCall(tmp, self._read_fn(lang), []))
                    self.tac.append(TACDeclare(ctype, name, tmp))
                else:
                    val = self._parse_expr()
                    self.tac.append(TACDeclare(ctype, name, val))
            else:
                self.tac.append(TACDeclare(ctype, name, self._default(lang)))
            if self._lex() == ";": self._eat(); break
            elif self._lex() == ",": self._eat()

    def _parse_array_decl(self, lang, ctype, name):
        dims = []
        while self._lex() == "[":
            self._eat()
            size = ""
            while self._lex() != "]": size += self._eat()[0]
            self._eat()
            dims.append(size)
        init = None
        if self._lex() == "=":          # <-- fixed: no extra check for "{"
            self._eat()
            if self._lex() == "{": init = self._parse_array_init(dims)
        if init is None:
            dv = self._default(lang)
            if len(dims)==1 and dims[0].isdigit():
                init = [dv]*int(dims[0])
            elif len(dims)==2 and dims[0].isdigit() and dims[1].isdigit():
                init = [[dv]*int(dims[1]) for _ in range(int(dims[0]))]
            else:
                init = [dv]
        self.tac.append(TACArrayDeclare(ctype, name, dims, init))
        if self._lex() == ";": self._eat()

    def _parse_array_init(self, dims):
        self._eat()
        result, row, depth, is_2d = [], [], 1, False
        while self.pos < len(self.tokens) and depth > 0:
            lex = self._lex()
            if lex == "{":
                is_2d = True; depth += 1; row = []; self._eat()
            elif lex == "}":
                depth -= 1
                if depth == 1 and is_2d: result.append(row)
                elif depth == 0: self._eat(); break
                self._eat()
            elif lex == ",": self._eat()
            else:
                val = self._fix_neg(self._eat()[0])
                if is_2d and depth == 2: row.append(val)
                else: result.append(val)
        return result

    def _parse_brace_list(self):
        self._eat()
        vals = []
        while self._lex() != "}":
            if self._lex() == ",": self._eat(); continue
            vals.append(self._fix_neg(self._eat()[0]))
        self._eat()
        return vals

    def _parse_function(self):
        kw = self._eat()[0]
        if kw == "main":
            func_name, ret_type = "main", "int"
        elif kw == "vacant":
            func_name = self._eat()[0]; ret_type = "void"
        else:
            func_name = self._eat()[0]; ret_type = "int"

        prev_scope  = self.scope
        self.scope  = func_name
        if func_name not in self.var_types:
            self.var_types[func_name] = {}

        self._eat()
        params = []
        while self._lex() != ")":
            if self._lex() == ",": self._eat(); continue
            p_lang  = self._eat()[0]
            p_name  = self._eat()[0]
            params.append(f"{self._ctype(p_lang)} {p_name}")
            self._reg(p_name, p_lang)
        self._eat()

        self.tac.append(TACFuncBegin(ret_type, func_name, params))

        while self._lex() != "{": self._eat()
        self._eat()

        depth = 1
        while self.pos < len(self.tokens) and depth > 0:
            if self._lex() == "{": depth += 1
            elif self._lex() == "}":
                depth -= 1
                if depth == 0: break
            self._parse_stmt()

        self._eat()

        if func_name == "main": self.tac.append(TACReturn("0"))
        self.tac.append(TACFuncEnd(func_name))
        self.scope = prev_scope

    def _parse_stmt(self):
        t, l = self._typ(), self._lex()
        if t is None: return
        if t in ("num","deci","word","single","bool"): self._parse_var_decl()
        elif t == "const":   self._parse_const()
        elif t == "struct":
            if self._lex(2) == "{": self._parse_struct_def()
            else:                   self._parse_struct_var()
        elif t == "out":     self._parse_out()
        elif t == "if":      self._parse_if()
        elif t == "match":   self._parse_match()
        elif t == "while":   self._parse_while()
        elif t == "for":     self._parse_for()
        elif t == "do":      self._parse_do_while()
        elif t == "return":  self._parse_return()
        elif l in ("++","--"):
            op  = self._eat()[0]; var = self._eat()[0]
            self.tac.append(TACUnary(var, op, var))
            if self._lex() == ";": self._eat()
        elif t == "identifier": self._parse_id_stmt()
        else: self._eat()

    def _parse_id_stmt(self):
        name = self._eat()[0]
        ASSIGN_OPS = {"=","+=","-=","*=","/=","%=","**="}

        if self._lex() in ("++","--"):
            op = self._eat()[0]
            self.tac.append(TACUnary(name, op, None, post=True))
            if self._lex() == ";": self._eat()
            return

        if self._lex() == "(":
            self._eat()
            args = self._parse_arg_list()
            self._eat()
            self.tac.append(TACCall(None, name, args))
            if self._lex() == ";": self._eat()
            return

        if self._lex() == "[":
            indices = []
            while self._lex() == "[":
                self._eat(); idx = self._parse_expr(); indices.append(idx); self._eat()
            op   = self._eat()[0]
            lhs  = name + "".join(f"[{i}]" for i in indices)
            lang = self._type_of(name) or "num"
            if self._typ() == "in":
                self._eat(); self._eat(); self._eat()
                tmp = self._tmp()
                self.tac.append(TACCall(tmp, self._read_fn(lang), []))
                self.tac.append(TACAssign(lhs, tmp))
            else:
                rhs = self._parse_expr()
                self._emit_assign(lhs, op, rhs, lang)
            if self._lex() == ";": self._eat()
            return

        if self._lex() == ".":
            self._eat(); field = self._eat()[0]; op = self._eat()[0]
            var_lang    = self._type_of(name) or ""
            struct_name = var_lang.replace("struct_", "")
            field_lang  = (self.struct_defs.get(struct_name) or {}).get(field, "word")
            lhs         = f"{name}.{field}"
            if self._typ() == "in":
                self._eat(); self._eat(); self._eat()
                tmp = self._tmp()
                self.tac.append(TACCall(tmp, self._read_fn(field_lang), []))
                self.tac.append(TACAssign(lhs, tmp))
            else:
                rhs = self._parse_expr()
                self._emit_assign(lhs, op, rhs, field_lang)
            if self._lex() == ";": self._eat()
            return

        if self._lex() in ASSIGN_OPS:
            op   = self._eat()[0]
            lang = self._type_of(name) or "num"
            if self._typ() == "in":
                self._eat(); self._eat(); self._eat()
                tmp = self._tmp()
                self.tac.append(TACCall(tmp, self._read_fn(lang), []))
                self.tac.append(TACAssign(name, tmp))
            else:
                rhs = self._parse_expr()
                self._emit_assign(name, op, rhs, lang)
            if self._lex() == ";": self._eat()
            return

        while self._lex() not in (";", None): self._eat()
        if self._lex() == ";": self._eat()

    def _emit_assign(self, lhs, op, rhs, lang):
        if op == "=":
            self.tac.append(TACAssign(lhs, rhs))
        elif op == "**=":
            tmp = self._tmp()
            self.tac.append(TACBinOp(tmp, lhs, "**", rhs))
            self.tac.append(TACAssign(lhs, tmp))
        else:
            base = op[:-1]; tmp = self._tmp()
            self.tac.append(TACBinOp(tmp, lhs, base, rhs))
            self.tac.append(TACAssign(lhs, tmp))

    def _parse_expr(self, min_prec=0):
        left = self._parse_unary()
        while True:
            op   = self._lex()
            prec = self.PRECEDENCE.get(op, -1)
            if prec <= min_prec:
                break
            self._eat()
            c_op  = {"is": "==", "isnot": "!="}.get(op, op)
            right = self._parse_expr(prec - 1 if op != "**" else prec)
            tmp   = self._tmp()
            self.tac.append(TACBinOp(tmp, left, c_op, right))
            left  = tmp
        return left

    def _parse_unary(self):
        if self._lex() == "!":
            self._eat()
            self._eat()
            inner = self._parse_expr()
            self._eat()
            tmp = self._tmp()
            self.tac.append(TACUnary(tmp, "!", inner))
            return tmp
        return self._parse_primary()

    def _parse_primary(self):
        l, t = self._lex(), self._typ()
        if l is None: return "0"

        if l == "(":
            self._eat(); val = self._parse_expr(); self._eat(); return val

        if l and l.startswith("~") and len(l) > 1:
            self._eat(); return "-" + l[1:]

        if l == "~":
            self._eat(); operand = self._parse_primary()
            tmp = self._tmp()
            self.tac.append(TACUnary(tmp, "-", operand))
            return tmp

        if t in ("num_literal","deci_literal","word_literal",
                  "single_literal","true","false"):
            self._eat(); return self._fix_neg(l)

        if t == "identifier":
            name = self._eat()[0]
            if self._lex() == "(":
                self._eat()
                args = self._parse_arg_list()
                self._eat()
                tmp = self._tmp()
                self.tac.append(TACCall(tmp, name, args))
                return tmp
            if self._lex() == "[":
                indices = []
                while self._lex() == "[":
                    self._eat(); idx = self._parse_expr(); indices.append(idx); self._eat()
                return name + "".join(f"[{i}]" for i in indices)
            if self._lex() == ".":
                self._eat(); field = self._eat()[0]
                return f"{name}.{field}"
            return name

        self._eat(); return "0"

    def _parse_arg_list(self):
        args = []
        while self._lex() != ")" and self._lex() is not None:
            args.append(self._parse_expr())
            if self._lex() == ",": self._eat()
        return args

    def _parse_out(self):
        self._eat()
        self._eat()

        raw = []
        depth = 0
        while self.pos < len(self.tokens):
            l, t, _, _ = self._tok()
            if l == "(":   depth += 1; raw.append(self._eat())
            elif l == ")":
                if depth == 0: break
                depth -= 1; raw.append(self._eat())
            else: raw.append(self._eat())

        self._eat()
        if self._lex() == ";": self._eat()

        segments, current, seg_depth = [], [], 0
        for tok in raw:
            lex = tok[0]
            if lex == "(":   seg_depth += 1; current.append(tok)
            elif lex == ")": seg_depth -= 1; current.append(tok)
            elif lex == "+" and seg_depth == 0:
                segments.append(current); current = []
            else: current.append(tok)
        if current: segments.append(current)

        for i, seg in enumerate(segments):
            is_last = (i == len(segments) - 1)
            self._emit_out_segment(seg, newline=is_last)

    def _emit_out_segment(self, seg_tokens, newline=True):
        if not seg_tokens: return
        saved_tokens, saved_pos = self.tokens, self.pos
        self.tokens = seg_tokens; self.pos = 0
        val = self._parse_expr()
        self.tokens, self.pos = saved_tokens, saved_pos
        fmt = self._infer_fmt(seg_tokens, val)
        self.tac.append(TACPrint(val, fmt, newline=newline))

    def _infer_fmt(self, seg_tokens, val):
        if not seg_tokens: return "%s"
        first_lex, first_typ = seg_tokens[0][0], seg_tokens[0][1]
        if first_typ == "word_literal":   return "%s"
        if first_typ == "single_literal": return "%c"
        if first_typ in ("true","false"): return "bool"
        if first_typ == "deci_literal":   return "%f"
        if first_typ == "num_literal":    return "%d"
        if first_typ == "identifier":
            lang = self._type_of(first_lex)
            if len(seg_tokens) >= 3 and seg_tokens[1][0] == ".":
                field      = seg_tokens[2][0]
                struct_nm  = (lang or "").replace("struct_", "")
                field_lang = (self.struct_defs.get(struct_nm) or {}).get(field, "word")
                return self._fmt(field_lang)
            if lang: return self._fmt(lang)
        return "%s"

    def _parse_if(self):
        end_lbl = self._lbl("if_end")

        def one_branch(keyword):
            self._eat()
            self._eat()
            cond = self._parse_expr()
            self._eat()
            next_lbl = self._lbl("else")
            self.tac.append(TACIfFalse(cond, next_lbl))
            self._consume_body()
            self.tac.append(TACGoto(end_lbl))
            self.tac.append(TACLabel(next_lbl))

        one_branch("if")
        while self._typ() == "elseif": one_branch("elseif")
        if self._typ() == "else":
            self._eat(); self._consume_body()
        self.tac.append(TACLabel(end_lbl))

    def _consume_body(self):
        while self._lex() != "{": self._eat()
        self._eat()
        depth = 1
        while self.pos < len(self.tokens) and depth > 0:
            if self._lex() == "{": depth += 1
            elif self._lex() == "}":
                depth -= 1
                if depth == 0: break
            self._parse_stmt()
        self._eat()

    def _parse_match(self):
        self._eat()
        self._eat()
        match_val = self._parse_expr()
        self._eat()
        while self._lex() != "{": self._eat()
        self._eat()
        end_lbl = self._lbl("sw_end")
        while self._lex() != "}":
            if self._typ() == "pick":
                self._eat()
                pattern  = self._parse_expr()
                self._eat()
                cmp_tmp  = self._tmp()
                skip_lbl = self._lbl("sw_skip")
                self.tac.append(TACBinOp(cmp_tmp, match_val, "==", pattern))
                self.tac.append(TACIfFalse(cmp_tmp, skip_lbl))
                self.tac.append(TACLabel(self._lbl("sw_case")))
                while self._typ() not in ("split","pick","def") and self._lex() != "}":
                    self._parse_stmt()
                self.tac.append(TACGoto(end_lbl))
                if self._typ() == "split": self._eat()
                if self._lex() == ";": self._eat()
                self.tac.append(TACLabel(skip_lbl))
            elif self._typ() == "def":
                self._eat(); self._eat()
                self.tac.append(TACLabel(self._lbl("sw_def")))
                while self._typ() != "split" and self._lex() != "}":
                    self._parse_stmt()
                self.tac.append(TACGoto(end_lbl))
                if self._typ() == "split": self._eat()
                if self._lex() == ";": self._eat()
            else: self._eat()
        self._eat()
        self.tac.append(TACLabel(end_lbl))

    def _parse_while(self):
        self._eat()
        start_lbl = self._lbl("wh_st"); end_lbl = self._lbl("wh_end")
        self.tac.append(TACLabel(start_lbl))
        self._eat()
        cond = self._parse_expr()
        self._eat()
        self.tac.append(TACIfFalse(cond, end_lbl))
        self._consume_body()
        self.tac.append(TACGoto(start_lbl))
        self.tac.append(TACLabel(end_lbl))

    def _parse_for(self):
        self._eat()
        self._eat()
        init_var = self._eat()[0]
        self._eat()
        init_val = self._parse_expr()
        self.tac.append(TACAssign(init_var, init_val))
        self._eat()
        start_lbl = self._lbl("for_st"); end_lbl = self._lbl("for_end")
        self.tac.append(TACLabel(start_lbl))
        cond = self._parse_expr()
        self.tac.append(TACIfFalse(cond, end_lbl))
        self._eat()
        incr_toks, depth = [], 0
        while self.pos < len(self.tokens):
            l = self._lex()
            if l == "(": depth += 1
            elif l == ")":
                if depth == 0: self._eat(); break
                depth -= 1
            incr_toks.append(self._eat())
        self._consume_body()
        self._emit_for_incr(incr_toks)
        self.tac.append(TACGoto(start_lbl))
        self.tac.append(TACLabel(end_lbl))

    def _emit_for_incr(self, toks):
        if not toks: return
        lexemes = [t[0] for t in toks]
        if len(lexemes) >= 2:
            if lexemes[1] in ("++","--"):
                self.tac.append(TACUnary(lexemes[0], lexemes[1], None, post=True))
            elif lexemes[0] in ("++","--"):
                self.tac.append(TACUnary(lexemes[1], lexemes[0], lexemes[1]))

    def _parse_do_while(self):
        self._eat()
        start_lbl = self._lbl("do_st"); end_lbl = self._lbl("do_end")
        self.tac.append(TACLabel(start_lbl))
        self._consume_body()
        while self._typ() != "while": self._eat()
        self._eat()
        self._eat()
        cond = self._parse_expr()
        self._eat()
        self.tac.append(TACIfFalse(cond, end_lbl))
        self.tac.append(TACGoto(start_lbl))
        self.tac.append(TACLabel(end_lbl))
        if self._lex() == ";": self._eat()

    def _parse_return(self):
        self._eat()
        if self._lex() == ";":
            self.tac.append(TACReturn()); self._eat(); return
        val = self._parse_expr()
        self.tac.append(TACReturn(val))
        if self._lex() == ";": self._eat()

    def _emit_c(self):
        lines  = []
        indent = 0
        TAB    = "    "

        def line(s): lines.append(TAB * indent + s)

        for instr in self.tac:
            if isinstance(instr, TACStructDef):
                line(f"struct {instr.name} {{")
                for ctype, fname in instr.fields:
                    line(f"{TAB}{ctype} {fname};")
                line("};"); line("")

            elif isinstance(instr, TACDeclare):
                prefix = "const " if instr.is_const else ""
                if instr.init is not None:
                    line(f"{prefix}{instr.c_type} {instr.name} = {instr.init};")
                else:
                    line(f"{prefix}{instr.c_type} {instr.name};")

            elif isinstance(instr, TACArrayDeclare):
                dims_str = "".join(f"[{d}]" for d in instr.dims)
                if instr.init is not None:
                    line(f"{instr.c_type} {instr.name}{dims_str} = {self._fmt_array_init(instr.init)};")
                else:
                    line(f"{instr.c_type} {instr.name}{dims_str};")

            elif isinstance(instr, TACBinOp):
                if instr.op == "**":
                    line(f"int {instr.result} = (int)pow((double){instr.left}, (double){instr.right});")
                else:
                    prefix = "int " if instr.result.startswith("_t") else ""
                    line(f"{prefix}{instr.result} = {instr.left} {instr.op} {instr.right};")

            elif isinstance(instr, TACUnary):
                if instr.post:   line(f"{instr.result}{instr.op};")
                elif instr.op in ("++","--"): line(f"{instr.op}{instr.result};")
                else:
                    prefix = "int " if instr.result.startswith("_t") else ""
                    line(f"{prefix}{instr.result} = {instr.op}{instr.operand};")

            elif isinstance(instr, TACAssign):
                line(f"{instr.result} = {instr.operand};")

            elif isinstance(instr, TACCall):
                args_str = ", ".join(instr.args)
                if instr.result:
                    prefix = "int " if instr.result.startswith("_t") else ""
                    line(f"{prefix}{instr.result} = {instr.func}({args_str});")
                else:
                    line(f"{instr.func}({args_str});")

            elif isinstance(instr, TACPrint):
                if instr.fmt == "bool":
                    line(f'printf("%s", ({instr.value}) ? "true" : "false");')
                else:
                    line(f'printf("{instr.fmt}\\n", {instr.value});')

            elif isinstance(instr, TACReturn):
                line(f"return {instr.value};" if instr.value is not None else "return;")

            elif isinstance(instr, TACLabel):
                lines.append(f"{instr.name}:")

            elif isinstance(instr, TACGoto):
                line(f"goto {instr.label};")

            elif isinstance(instr, TACIfFalse):
                line(f"if (!({instr.cond})) goto {instr.label};")

            elif isinstance(instr, TACFuncBegin):
                params_str = ", ".join(instr.params) if instr.params else ""
                line(f"{instr.ret_type} {instr.name}({params_str}) {{")
                indent += 1

            elif isinstance(instr, TACFuncEnd):
                indent -= 1; line("}"); line("")

        return lines

    def _fmt_array_init(self, init):
        if not init: return "{}"
        if isinstance(init[0], list):
            rows = ", ".join("{" + ", ".join(str(v) for v in row) + "}" for row in init)
            return "{" + rows + "}"
        return "{" + ", ".join(str(v) for v in init) + "}"

    def _helpers(self):
        L = []
        def add(s): L.append(s)

        add("#include <stdio.h>")
        add("#include <stdlib.h>")
        add("#include <string.h>")
        add("#include <stdbool.h>")
        add("#include <math.h>")
        add("#ifdef _WIN32")
        add("#include <windows.h>")
        add("#else")
        add("#include <unistd.h>")
        add("#endif")
        add("#include <ctype.h>")
        add("")

        add("int read_int() {")
        add("    int value = 0; int valid = 0; char buf[1024];")
        add("    while (!valid) {")
        add('        printf("_waiting_for_input|\\n"); fflush(stdout);')
        add("        if (fgets(buf, sizeof(buf), stdin) == NULL) { printf(\"...\\n\"); continue; }")
        add("        if (buf[0] == '~') buf[0] = '-';")
        add("        char *end; value = (int)strtol(buf, &end, 10);")
        add("        if (*end != '\\n' && *end != '\\0') { printf(\"Invalid input.\\n\"); fflush(stdout); }")
        add("        else { valid = 1; }")
        add("    } return value;")
        add("}")
        add("")

        add("double read_double() {")
        add("    double value = 0.0; int valid = 0; char buf[1024];")
        add("    while (!valid) {")
        add('        printf("_waiting_for_input|\\n"); fflush(stdout);')
        add("        if (fgets(buf, sizeof(buf), stdin) == NULL) { printf(\"...\\n\"); continue; }")
        add("        if (buf[0] == '~') buf[0] = '-';")
        add("        char *end; value = strtod(buf, &end);")
        add("        if (*end != '\\n' && *end != '\\0') { printf(\"Invalid input.\\n\"); fflush(stdout); }")
        add("        else { valid = 1; }")
        add("    } return value;")
        add("}")
        add("")

        add("char read_char() {")
        add("    char value = '\\0'; int valid = 0; char buf[1024];")
        add("    while (!valid) {")
        add('        printf("_waiting_for_input|\\n"); fflush(stdout);')
        add("        if (fgets(buf, sizeof(buf), stdin) == NULL) { printf(\"...\\n\"); continue; }")
        add("        size_t len = strlen(buf); int cnt = 0;")
        add("        for (size_t i=0;i<len;i++) if(buf[i]!=' '&&buf[i]!='\\t'&&buf[i]!='\\n'){value=buf[i];cnt++;}")
        add("        if (cnt!=1){printf(\"Invalid input.\\n\");fflush(stdout);}else{valid=1;}")
        add("    } return value;")
        add("}")
        add("")

        add("char* read_word() {")
        add("    char buf[1024]; int valid = 0;")
        add("    while (!valid) {")
        add('        printf("_waiting_for_input|\\n"); fflush(stdout);')
        add("        if (fgets(buf, sizeof(buf), stdin) == NULL) { printf(\"...\\n\"); continue; }")
        add("        size_t len = strlen(buf);")
        add("        if (len>0 && buf[len-1]=='\\n') buf[len-1]='\\0';")
        add("        int empty=1; for(size_t i=0;i<strlen(buf);i++) if(buf[i]!=' '&&buf[i]!='\\t'){empty=0;break;}")
        add("        if(empty){printf(\"Input cannot be empty.\\n\");fflush(stdout);}else{valid=1;}")
        add("    } return strdup(buf);")
        add("}")
        add("")

        add("bool read_bool() {")
        add("    char buf[1024]; int valid=0; bool value=false;")
        add("    while (!valid) {")
        add('        printf("_waiting_for_input|Enter a boolean (true/false, 1/0): \\n"); fflush(stdout);')
        add("        if (fgets(buf,sizeof(buf),stdin)==NULL){printf(\"...\\n\");continue;}")
        add("        size_t len=strlen(buf); if(len>0&&buf[len-1]=='\\n')buf[len-1]='\\0';")
        add("        for(size_t i=0;i<strlen(buf);i++) buf[i]=tolower(buf[i]);")
        add('        if(!strcmp(buf,"true")||!strcmp(buf,"1")||!strcmp(buf,"yes")||!strcmp(buf,"y")){value=true;valid=1;}')
        add('        else if(!strcmp(buf,"false")||!strcmp(buf,"0")||!strcmp(buf,"no")||!strcmp(buf,"n")){value=false;valid=1;}')
        add('        else{printf("Invalid.\\n");fflush(stdout);}')
        add("    } return value;")
        add("}")
        add("")

        return L