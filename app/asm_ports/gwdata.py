"""Semantic replacement for GWDATA.ASM.

GWDATA.ASM mixes immutable token/error tables with interpreter globals that
historically lived in a data segment. Python separates those concerns: constants
live here and mutable values live in ``RuntimeState``.
"""
ERRORS = {
    'NF': 'NEXT without FOR', 'SN': 'Syntax error', 'RG': 'RETURN without GOSUB',
    'OD': 'Out of DATA', 'FC': 'Illegal function call', 'OV': 'Overflow',
    'OM': 'Out of memory', 'UL': 'Undefined line number', 'BS': 'Subscript out of range',
    'DD': 'Duplicate Definition', 'DZ': 'Division by zero', 'ID': 'Illegal direct',
    'TM': 'Type mismatch', 'OS': 'Out of string space', 'LS': 'String too long',
    'ST': 'String formula too complex', 'CN': "Can't continue", 'UF': 'Undefined user function',
}
TRUE=-1
FALSE=0
