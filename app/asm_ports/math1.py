"""Semantic port of MATH1.ASM, the main 8086 math package.

Original MATH1.ASM manipulates Microsoft's internal integer/single/double
representations through the FAC (floating accumulator) and ARG registers in RAM.
Python already provides IEEE-754 floating point and arbitrary precision integers,
so the port preserves the *operations* rather than the byte representation.

Representative mappings:
    ABSFN -> abs_value
    ATN   -> atn
    COS   -> cos
    EXP   -> exp
    INT   -> int_floor
    LOG   -> log
    SQR   -> sqr
    SIN   -> sin
    TAN   -> tan
    RND   -> rnd

The conversion/formatting routines in the original file become normal Python
numeric conversions.  This is an intentional semantic port, not an 8086 emulator.
"""
from __future__ import annotations
import math
import random


def abs_value(x): return abs(x)
def atn(x): return math.atan(float(x))
def cos(x): return math.cos(float(x))
def exp(x): return math.exp(float(x))
def log(x): return math.log(float(x))
def sin(x): return math.sin(float(x))
def sqr(x): return math.sqrt(float(x))
def tan(x): return math.tan(float(x))
def sgn(x): return -1 if x < 0 else (1 if x > 0 else 0)
def int_floor(x): return math.floor(float(x))
def fix(x): return math.trunc(float(x))
def cint(x): return int(round(float(x)))
def csng(x): return float(x)
def cdbl(x): return float(x)
def rnd(_: float | None = None): return random.random()


def basic_bool(value: bool) -> int:
    """GW-BASIC encodes true as -1 (all bits set), false as 0."""
    return -1 if value else 0
