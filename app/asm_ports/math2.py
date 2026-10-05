"""Semantic port of MATH2.ASM.

MATH2.ASM contains number input, exponent handling, precision promotion and
integer/single/double conversion support.  In the Python port those low-level
steps are centralized here as safe textual number parsing.
"""
from __future__ import annotations
import re

_NUMBER = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?[!#%&]?$", re.I)


def parse_basic_number(text: str):
    s = text.strip()
    if s.upper().startswith("&H"):
        return int(s[2:], 16)
    if s.upper().startswith("&O"):
        return int(s[2:], 8)
    if not _NUMBER.match(s):
        raise ValueError(f"not a BASIC numeric literal: {text}")
    suffix = s[-1:] if s[-1:] in "!#%&" else ""
    if suffix:
        s = s[:-1]
    s = s.replace("D", "E").replace("d", "e")
    if suffix in ("%", "&") or ("." not in s and "E" not in s.upper()):
        return int(s)
    return float(s)
