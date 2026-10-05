"""Semantic port of BIPRTU.ASM, the PRINT USING formatter.

The original PRINUS routine scans a USING string one character at a time,
classifies string/numeric fields, formats FAC and outputs through OUTDO.
This pure Python function follows that same conceptual pipeline.

Supported educational subset
----------------------------
* ``#`` digit positions
* decimal point and comma grouping
* leading ``+`` or trailing ``-`` signs
* ``$$`` currency marker
* ``^^^^`` scientific notation
* ``&`` whole-string field
* ``!`` first-character field
* ``\\   \\`` fixed-width string field

This covers the structure of PRINUS without reproducing every historical edge
case of Microsoft Binary Format numeric output.
"""
from __future__ import annotations
import re
from app.asm_ports.bistrs import format_number


def format_using(pattern: str, values: list[object]) -> str:
    out=[]; vi=0; i=0
    while i < len(pattern):
        c=pattern[i]
        if c=='!' and vi < len(values):
            out.append(str(values[vi])[:1]); vi+=1; i+=1; continue
        if c=='&' and vi < len(values):
            out.append(str(values[vi])); vi+=1; i+=1; continue
        if c=='\\':
            j=pattern.find('\\',i+1)
            if j>i and vi < len(values):
                width=j-i+1; s=str(values[vi]); vi+=1
                out.append(s[:width].ljust(width)); i=j+1; continue
        if c in '#+$*' or (c=='.' and i+1<len(pattern) and pattern[i+1]=='#'):
            m=re.match(r'([+]?)([$*]{0,2})([#,.]+)([-]?)(\^{4})?',pattern[i:])
            if m and vi < len(values):
                field=m.group(0); value=values[vi]; vi+=1
                out.append(_format_numeric(field,value)); i+=len(field); continue
        out.append(c); i+=1
    # GW-BASIC cycles the USING format when values remain. For readability we
    # append unmatched values rather than silently discarding them.
    if vi < len(values):
        out.append(' '.join(format_number(v) if not isinstance(v,str) else v for v in values[vi:]))
    return ''.join(out)


def _format_numeric(field: str, value: object) -> str:
    x=float(value)
    scientific='^^^^' in field
    currency='$$' in field
    show_plus=field.startswith('+')
    trailing_minus='-' in field and field.rstrip().endswith('-')
    core=field.replace('^^^^','').replace('$$','').replace('*','').replace('+','').replace('-','')
    decimals=len(core.split('.',1)[1].replace(',','')) if '.' in core else 0
    width=len(field)
    if scientific:
        s=f"{abs(x):.{max(0,decimals)}E}"
    else:
        grouping=',' in core
        s=f"{abs(x):,.{decimals}f}" if grouping else f"{abs(x):.{decimals}f}"
    if currency: s='$'+s
    if x<0:
        s = s+'-' if trailing_minus else '-'+s
    elif show_plus:
        s='+'+s
    fill='*' if '**' in field else ' '
    return s.rjust(width,fill)[-width:]
