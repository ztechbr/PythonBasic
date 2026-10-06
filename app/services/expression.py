"""Expression evaluator corresponding primarily to GWEVAL.ASM.

Academic translation notes
---------------------------
GWEVAL.ASM uses CHRGTR to scan tokenized source, FRMEVL/FRMCHK to evaluate
formulae and FAC/ARG memory as implicit operands.  This implementation makes
all of those hidden machine concepts explicit:

* Lexer = CHRGTR/token stream equivalent.
* Pratt parser = precedence dispatch tables from the interpreter.
* Python return values = FAC.
* RuntimeState variable lookup = PTRGET/BIPTRG.ASM.
* Function table = MATH1/MATH2/BISTRS services.

No Python ``eval`` is used.  This matters both for pedagogy and safety.
"""
from __future__ import annotations
from dataclasses import dataclass
import re, math
from typing import Any

from app.models.runtime import BasicError, RuntimeState
from app.asm_ports import math1, bistrs
from app.asm_ports.math2 import parse_basic_number


@dataclass(frozen=True)
class Token:
    kind: str
    value: str


TOKEN_RE = re.compile(r'''\s*(?:
(?P<HEX>&[Hh][0-9A-Fa-f]+)|(?P<OCT>&[Oo][0-7]+)|
(?P<NUMBER>(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?[!#%&]?)|
(?P<STRING>"(?:[^"]|"")*")|
(?P<IDENT>[A-Za-z][A-Za-z0-9_.]*[$%!#&]?)|
(?P<OP><>|<=|>=|[+\-*/\\^=<>(),;]))''', re.X)


def tokenize(expr: str) -> list[Token]:
    pos=0; out=[]
    while pos < len(expr):
        if expr[pos:].strip() == "": break
        m=TOKEN_RE.match(expr,pos)
        if not m: raise BasicError(f"Syntax error near {expr[pos:pos+12]!r}")
        kind=m.lastgroup; value=m.group(kind); pos=m.end()
        if kind == 'IDENT' and value.upper() in {'AND','OR','XOR','EQV','IMP','MOD','NOT'}:
            kind='OP'; value=value.upper()
        out.append(Token(kind,value))
    out.append(Token('EOF',''))
    return out


class ExpressionParser:
    PRECEDENCE = {
        'IMP': 1, 'EQV': 2, 'XOR': 3, 'OR': 4, 'AND': 5,
        '=': 6, '<>': 6, '<': 6, '>': 6, '<=': 6, '>=': 6,
        '+': 7, '-': 7,
        'MOD': 8, '\\': 8, '*': 9, '/': 9,
        '^': 10,
    }
    FUNCTIONS = {
        'ABS': math1.abs_value, 'ATN': math1.atn, 'COS': math1.cos,
        'EXP': math1.exp, 'LOG': math1.log, 'SIN': math1.sin,
        'SQR': math1.sqr, 'TAN': math1.tan, 'SGN': math1.sgn,
        'INT': math1.int_floor, 'FIX': math1.fix, 'CINT': math1.cint,
        'CSNG': math1.csng, 'CDBL': math1.cdbl, 'RND': math1.rnd,
        'LEN': bistrs.len_, 'LEFT$': bistrs.left, 'RIGHT$': bistrs.right,
        'MID$': bistrs.mid, 'CHR$': bistrs.chr_, 'ASC': bistrs.asc,
        'STR$': bistrs.str_, 'VAL': bistrs.val, 'STRING$': bistrs.string_,
        'SPACE$': bistrs.space_, 'HEX$': bistrs.hex_, 'OCT$': bistrs.oct_,
        'INSTR': bistrs.instr,
    }

    def __init__(self, state: RuntimeState):
        self.state=state; self.tokens=[]; self.i=0

    def evaluate(self, expr: str) -> Any:
        self.tokens=tokenize(expr); self.i=0
        value=self.parse_expr(0)
        if self.peek().kind != 'EOF': raise BasicError('Syntax error')
        return value

    def peek(self): return self.tokens[self.i]
    def take(self):
        t=self.tokens[self.i]; self.i+=1; return t
    def accept(self, value):
        if self.peek().value.upper()==value.upper(): self.i+=1; return True
        return False
    def expect(self, value):
        if not self.accept(value): raise BasicError(f"Expected {value}")

    def parse_expr(self, min_prec=0):
        left=self.parse_prefix()
        while True:
            t=self.peek(); op=t.value.upper()
            prec=self.PRECEDENCE.get(op,-1)
            if prec < min_prec: break
            self.take()
            # BASIC exponentiation is right associative.
            rhs=self.parse_expr(prec if op=='^' else prec+1)
            left=self.apply_binary(op,left,rhs)
        return left

    def parse_prefix(self):
        t=self.take()
        if t.kind in ('NUMBER','HEX','OCT'):
            return parse_basic_number(t.value)
        if t.kind=='STRING': return t.value[1:-1].replace('""','"')
        if t.value=='(':
            v=self.parse_expr(); self.expect(')'); return v
        if t.kind=='OP' and t.value.upper() in ('+','-','NOT'):
            v=self.parse_expr(11)
            if t.value=='+': return +float(v)
            if t.value=='-': return -float(v)
            return ~int(v)
        if t.kind=='IDENT':
            name=t.value.upper()
            if self.accept('('):
                args=[]
                if not self.accept(')'):
                    while True:
                        args.append(self.parse_expr())
                        if self.accept(')'): break
                        self.expect(',')
                if name in self.FUNCTIONS:
                    try: return self.FUNCTIONS[name](*args)
                    except (ValueError,TypeError,OverflowError,ZeroDivisionError) as e:
                        raise BasicError(str(e)) from e
                # Machine-facing functions become lookups in explicit runtime maps.
                if name == 'PEEK' and len(args) == 1:
                    return self.state.memory.get(self.state.linear_address(int(args[0])), 0)
                if name == 'INP' and len(args) == 1:
                    return self.state.io_ports.get(int(args[0]), 0)
                if name == 'POS':
                    return self.state.screen.cursor_col
                if name == 'CSRLIN':
                    return self.state.screen.cursor_row
                if name in {'EOF','LOF','LOC'} and len(args) == 1:
                    fh=self.state.file_handles.get(int(args[0]))
                    if fh is None: raise BasicError('Bad file number')
                    if name == 'LOC': return fh.handle.tell()
                    if name == 'LOF':
                        cur=fh.handle.tell(); fh.handle.seek(0,2); size=fh.handle.tell(); fh.handle.seek(cur); return size
                    cur=fh.handle.tell(); one=fh.handle.read(1); fh.handle.seek(cur); return -1 if one == '' else 0
                # Not a known function: GW-BASIC treats NAME(...) as array lookup.
                return self.array_get(name,args)
            if name=='PI': return math.pi
            return self.state.get_var(name)
        raise BasicError('Syntax error')

    def array_get(self,name,args):
        key=self.state.normalize_var(name)
        arr=self.state.arrays.get(key)
        if arr is None: raise BasicError('Subscript out of range')
        idx=tuple(int(float(x)) for x in args)
        return arr.get(idx, self.state.default_value(key))

    @staticmethod
    def apply_binary(op,a,b):
        if op=='+':
            if isinstance(a,str) or isinstance(b,str): return str(a)+str(b)
            return a+b
        if op=='-': return a-b
        if op=='*': return a*b
        if op=='/':
            if b==0: raise BasicError('Division by zero')
            return a/b
        if op=='\\':
            if int(b)==0: raise BasicError('Division by zero')
            return int(a)//int(b)
        if op=='MOD':
            if int(b)==0: raise BasicError('Division by zero')
            return int(a)%int(b)
        if op=='^': return a**b
        if op=='=': return math1.basic_bool(a==b)
        if op=='<>': return math1.basic_bool(a!=b)
        if op=='<': return math1.basic_bool(a<b)
        if op=='>': return math1.basic_bool(a>b)
        if op=='<=': return math1.basic_bool(a<=b)
        if op=='>=': return math1.basic_bool(a>=b)
        ai,bi=int(a),int(b)
        if op=='AND': return ai & bi
        if op=='OR': return ai | bi
        if op=='XOR': return ai ^ bi
        if op=='EQV': return ~(ai ^ bi)
        if op=='IMP': return (~ai) | bi
        raise BasicError(f'Unknown operator {op}')
