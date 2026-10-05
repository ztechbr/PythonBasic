"""Unicode-oriented semantic port of KANJ86.ASM.

The 1980s routines reason about Kanji byte sequences. Python 3 strings are
Unicode code-point sequences, so the educational equivalent works at character
boundaries while exposing similarly named operations.
"""
from __future__ import annotations


def klen(value: str) -> int:
    return len(str(value))


def kpos(value: str, position: int) -> str:
    s=str(value); i=int(position)-1
    return s[i] if 0 <= i < len(s) else ''


def jis(value: str) -> bytes:
    return str(value).encode('iso2022_jp',errors='replace')


def ktn(value: bytes | str) -> str:
    if isinstance(value,bytes):
        return value.decode('iso2022_jp',errors='replace')
    return str(value)
