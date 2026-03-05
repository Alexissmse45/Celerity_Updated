import math
from code_gen import (
    TACFuncBegin, TACFuncEnd, TACDeclare, TACArrayDeclare,
    TACAssign, TACBinOp, TACUnary, TACLabel, TACGoto, TACIfFalse,
    TACPrint, TACReturn, TACCall, TACStructDef,
)


def count_inputs(tac_list):
    READ_FNS = {"read_int","read_double","read_char","read_word","read_bool"}
    return sum(1 for i in tac_list if isinstance(i, TACCall) and i.func in READ_FNS)


def get_input_types(tac_list):
    READ_TYPE = {"read_int":"num","read_double":"deci","read_char":"single",
                 "read_word":"word","read_bool":"bool"}
    return [READ_TYPE.get(i.func,"word") for i in tac_list
            if isinstance(i, TACCall) and i.func in READ_TYPE]


class TACInterpreter:
    MAX_ITER = 200_000

    def __init__(self):
        self.output_lines = []
        self.events       = []
        self._iter        = 0
        self._input_queue = []
        self._input_types = []
        self._input_index = 0
        self._buf         = ""   # buffer for no-newline print segments

    def run(self, tac_list, user_inputs=None):
        """
        Execute TAC. Returns (plain_string, events).
        events = list of:
          { type:'output', text:'...' }
          { type:'input_prompt', text:'enter grade ', userValue:'65.4',
            inputIndex:0, inputType:'deci' }

        When in() is hit, the LAST output event is absorbed as the inline
        prompt so the input box appears on the same line.
        """
        self.output_lines = []
        self.events       = []
        self._iter        = 0
        self._input_queue = list(user_inputs or [])
        self._input_types = get_input_types(tac_list)
        self._input_index = 0
        self._buf         = ""

        label_map = {ins.name: i for i, ins in enumerate(tac_list)
                     if isinstance(ins, TACLabel)}
        func_map  = {ins.name: i for i, ins in enumerate(tac_list)
                     if isinstance(ins, TACFuncBegin)}
        main_start = next((i+1 for i, ins in enumerate(tac_list)
                           if isinstance(ins, TACFuncBegin) and ins.name == "main"), None)
        if main_start is None:
            return "(no main found)", []

        env = {}
        try:
            self._exec(tac_list, main_start, env, label_map, func_map, 0)
        except (_ProgramDone, _ReturnSignal):
            pass
        except _IterLimit:
            self._out("[stopped: iteration limit]")
        except Exception as e:
            self._out(f"[runtime error: {e}]")

        self._flush_buf()  # flush any remaining buffered output
        plain = "\n".join(self.output_lines) if self.output_lines else "(no output)"
        return plain, self.events

    # ── helpers ───────────────────────────────────────────────────────────────

    def _out(self, text):
        """Emit a plain output event (flushing any buffered no-newline text first)."""
        combined = self._buf + text
        self._buf = ""
        self.output_lines.append(combined)
        self.events.append({"type": "output", "text": combined})

    def _flush_buf(self):
        """Flush any remaining buffered text as a final output line."""
        if self._buf:
            self.output_lines.append(self._buf)
            self.events.append({"type": "output", "text": self._buf})
            self._buf = ""

    def _absorb_prompt(self):
        """
        Absorb the prompt text for an inline in() display.
        Priority 1: buffered no-newline text (from no_nl segments).
        Priority 2: the last completed output event — this covers the common
                    pattern  out("enter: "); x = in();  where the prompt is
                    a standalone out() call immediately before in().
        """
        if self._buf:
            prompt = self._buf
            self._buf = ""
            return prompt
        if self.events and self.events[-1]["type"] == "output":
            text = self.events[-1]["text"]
            self.events.pop()
            if self.output_lines:
                self.output_lines.pop()
            return text
        return ""

    # ── executor ──────────────────────────────────────────────────────────────

    def _exec(self, tac, start, env, lmap, fmap, depth):
        if depth > 200: raise RecursionError("call depth exceeded")
        pc = start
        while pc < len(tac):
            self._iter += 1
            if self._iter > self.MAX_ITER: raise _IterLimit()

            ins = tac[pc]

            if isinstance(ins, TACFuncEnd):   return
            if isinstance(ins, (TACStructDef, TACFuncBegin)): pc+=1; continue

            if isinstance(ins, TACDeclare):
                env[ins.name] = self._ev(ins.init, env) if ins.init is not None else self._zero(ins.c_type)
                pc+=1; continue

            if isinstance(ins, TACArrayDeclare):
                if ins.init:
                    if isinstance(ins.init[0], list):
                        env[ins.name] = [[self._ev(v,env) for v in row] for row in ins.init]
                    else:
                        env[ins.name] = [self._ev(v,env) for v in ins.init]
                else:
                    env[ins.name] = []
                pc+=1; continue

            if isinstance(ins, TACAssign):
                if "[" in ins.result: self._astore(ins.result, self._ev(ins.operand,env), env)
                else: env[ins.result] = self._ev(ins.operand, env)
                pc+=1; continue

            if isinstance(ins, TACBinOp):
                env[ins.result] = self._binop(ins.op, self._ev(ins.left,env), self._ev(ins.right,env))
                pc+=1; continue

            if isinstance(ins, TACUnary):
                if ins.post:
                    cur = self._ev(ins.result, env)
                    env[ins.result] = cur + (1 if ins.op=="++" else -1)
                elif ins.op in ("++","--"):
                    cur = self._ev(ins.result, env)
                    env[ins.result] = cur + (1 if ins.op=="++" else -1)
                elif ins.op == "!":   env[ins.result] = not self._ev(ins.operand, env)
                elif ins.op == "-":   env[ins.result] = -self._ev(ins.operand, env)
                else:                 env[ins.result] = self._ev(ins.operand, env)
                pc+=1; continue

            if isinstance(ins, TACLabel): pc+=1; continue

            if isinstance(ins, TACGoto):
                t = lmap.get(ins.label); pc = (t+1) if t is not None else pc+1; continue

            if isinstance(ins, TACIfFalse):
                if not self._ev(ins.cond, env):
                    t = lmap.get(ins.label); pc = (t+1) if t is not None else pc+1
                else: pc+=1
                continue

            if isinstance(ins, TACPrint):
                self._print(ins, env)
                pc+=1; continue

            if isinstance(ins, TACReturn):
                raise _ReturnSignal(self._ev(ins.value,env) if ins.value else None)

            if isinstance(ins, TACCall):
                res = self._call(ins, tac, env, lmap, fmap, depth)
                if ins.result is not None: env[ins.result] = res if res is not None else 0
                pc+=1; continue

            pc+=1

    def _call(self, ins, tac, cenv, lmap, fmap, depth):
        func = ins.func
        args = [self._ev(a, cenv) for a in ins.args]

        if func in ("read_int","read_double","read_char","read_word","read_bool"):
            # absorb the preceding out() line as the inline prompt
            prompt = self._absorb_prompt()
            idx    = self._input_index
            itype  = self._input_types[idx] if idx < len(self._input_types) else "word"
            self._input_index += 1

            raw = self._input_queue.pop(0).strip() if self._input_queue else ""

            self.events.append({
                "type": "input_prompt", "text": prompt,
                "userValue": raw, "inputIndex": idx, "inputType": itype,
            })
            self.output_lines.append(f"{prompt}{raw}")

            if func == "read_int":
                try: return int(float(raw)) if raw else 0
                except: return 0
            if func == "read_double":
                try: return float(raw) if raw else 0.0
                except: return 0.0
            if func == "read_char":   return raw[0] if raw else " "
            if func == "read_word":   return raw
            if func == "read_bool":   return raw.lower() in ("true","1","yes","y")

        if func in fmap:
            fb = tac[fmap[func]]
            lenv = dict(cenv)
            for p, v in zip(fb.params, args): lenv[p.split()[-1]] = v
            try: self._exec(tac, fmap[func]+1, lenv, lmap, fmap, depth+1)
            except _ReturnSignal as r: return r.value
        return None

    def _print(self, ins, env):
        val = self._ev(ins.value, env)
        fmt = ins.fmt
        if fmt == "bool":  text = "true" if val else "false"
        elif fmt == "%d":
            try: text = str(int(val))
            except: text = str(val)
        elif fmt == "%f":
            try: text = f"{float(val):.6f}"
            except: text = str(val)
        elif fmt == "%c":  text = str(val)
        else:
            s = str(val) if val is not None else ""
            text = s[1:-1] if len(s) >= 2 and s[0]=='"' and s[-1]=='"' else s

        # Buffer everything. Only flush when \n is encountered.
        # This means out("*") accumulates in _buf until out("\n") flushes it,
        # giving correct behaviour for loops that print without newlines.
        if '\\n' in text or '\n' in text:
            parts = text.replace('\\n', '\n').split('\n')
            self._buf += parts[0]
            self._flush_buf()          # flush the completed line
            for part in parts[1:-1]:   # middle pieces each flush
                self._buf += part
                self._flush_buf()
            self._buf += parts[-1]     # last piece stays buffered
        else:
            self._buf += text          # no newline — keep buffering

    def _ev(self, expr, env):
        if expr is None: return 0
        expr = str(expr).strip()
        try: return int(expr)
        except ValueError: pass
        try: return float(expr)
        except ValueError: pass
        if expr == "true":  return True
        if expr == "false": return False
        if expr.startswith('"') and expr.endswith('"'): return expr
        if expr.startswith("'") and expr.endswith("'") and len(expr)==3: return expr[1]
        if "[" in expr:
            base = expr[:expr.index("[")]
            rest = expr[expr.index("["):]
            indices = []
            while rest.startswith("["):
                c = rest.index("]")
                indices.append(int(self._ev(rest[1:c], env)))
                rest = rest[c+1:]
            obj = env.get(base, [])
            for i in indices:
                obj = obj[i] if isinstance(obj,list) and 0<=i<len(obj) else 0
            return obj
        if "." in expr:
            p = expr.split(".", 1)
            obj = env.get(p[0], {})
            return obj.get(p[1], 0) if isinstance(obj, dict) else 0
        return env.get(expr, 0)

    def _zero(self, c_type):
        if c_type in ("int","bool"): return 0
        if c_type == "double":       return 0.0
        if c_type == "char":         return " "
        if c_type == "char*":        return ""
        return 0

    def _astore(self, lhs, val, env):
        base = lhs[:lhs.index("[")]
        rest = lhs[lhs.index("["):]
        indices = []
        while rest.startswith("["):
            c = rest.index("]")
            indices.append(int(self._ev(rest[1:c], env)))
            rest = rest[c+1:]
        obj = env.get(base, [])
        if len(indices)==1:
            while len(obj)<=indices[0]: obj.append(0)
            obj[indices[0]] = val
        elif len(indices)==2:
            while len(obj)<=indices[0]: obj.append([])
            while len(obj[indices[0]])<=indices[1]: obj[indices[0]].append(0)
            obj[indices[0]][indices[1]] = val
        env[base] = obj   # <-- ADD THIS LINE if missing

    def _binop(self, op, l, r):
        try:
            if op=="+":  return l+r
            if op=="-":  return l-r
            if op=="*":  return l*r
            if op=="/":  return 0 if r==0 else ((l//r) if isinstance(l,int) and isinstance(r,int) else l/r)
            if op=="%":  return l%r if r!=0 else 0
            if op=="**": return math.pow(l,r)
            if op=="==": return l==r
            if op=="!=": return l!=r
            if op=="<":  return l<r
            if op==">":  return l>r
            if op=="<=": return l<=r
            if op==">=": return l>=r
            if op=="&&": return bool(l) and bool(r)
            if op=="||": return bool(l) or bool(r)
        except: pass
        return 0


class _ReturnSignal(Exception):
    def __init__(self, v): self.value = v
class _IterLimit(Exception): pass
class _ProgramDone(Exception): pass