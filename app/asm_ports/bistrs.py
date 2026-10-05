"""Semantic port of BISTRS.ASM, GW-BASIC string services.

The ASM source maintains string descriptors and a compacting garbage collector.
Python strings are managed objects, therefore GETSPA/GARBAG/FRESTR disappear as
manual memory operations.  Their externally visible string functions remain.
"""
from __future__ import annotations


def len_(s): return len(str(s))
def left(s, n): return str(s)[:max(0, int(n))]
def right(s, n): return str(s)[-max(0, int(n)):] if int(n) else ""
def mid(s, start, length=None):
    s = str(s); i = max(0, int(start)-1)
    return s[i:] if length is None else s[i:i+max(0, int(length))]
def chr_(n): return chr(int(n) & 0xFF)
def asc(s):
    s = str(s)
    if not s: raise ValueError("Illegal function call")
    return ord(s[0])
def str_(n):
    return (" " if float(n) >= 0 else "") + format_number(n)
def val(s):
    s = str(s).lstrip()
    out=[]
    for c in s:
        if c in "+-0123456789.eEdD": out.append(c)
        else: break
    if not out: return 0
    t=''.join(out).replace('D','E').replace('d','e')
    try: return float(t) if any(c in t for c in '.Ee') else int(t)
    except ValueError: return 0

def string_(n, value):
    n=max(0,int(n))
    if isinstance(value,(int,float)): return chr_(int(value))*n
    s=str(value)
    return (s[:1] if s else "")*n

def space_(n): return " "*max(0,int(n))
def hex_(n): return format(int(n) & 0xFFFF, "X")
def oct_(n): return format(int(n) & 0xFFFF, "o").upper()
def instr(start, haystack=None, needle=None):
    if needle is None:
        needle=haystack; haystack=start; start=1
    idx=str(haystack).find(str(needle), max(0,int(start)-1))
    return 0 if idx < 0 else idx+1

def format_number(n):
    x=float(n)
    if x.is_integer(): return str(int(x))
    return f"{x:.12g}"
