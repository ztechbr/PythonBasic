"""Academic semantic port notes for FIVEO.ASM.

Original title: FIVEO 5.0 Features -WHILE/WEND, CALL, CHAIN, WRITE /P. Allen

Purpose
-------
GW-BASIC 5.0 features including WHILE/WEND, CHAIN, COMMON and WRITE. Mapped to structured interpreter control flow.

Translation rule
----------------
This module intentionally does not emulate 8086 registers instruction by
instruction. Register state, flags, segment offsets and jump-table addresses are
translated into Python values, exceptions, dataclasses and method dispatch.
The original file remains under ``reference/asm/FIVEO.ASM`` for side-by-side study.
"""

ORIGINAL_FILE = 'FIVEO.ASM'
ORIGINAL_TITLE = 'FIVEO 5.0 Features -WHILE/WEND, CALL, CHAIN, WRITE /P. Allen'
PUBLIC_ROUTINES = ['WHILE', 'WEND', 'CHAIN', 'COMMON', 'CHNRET', 'SKPNAM', 'WRITE']
SUBSECTIONS = ['WHILE , WEND', 'CHAIN', 'WRITE']
PORT_NOTE = 'GW-BASIC 5.0 features including WHILE/WEND, CHAIN, COMMON and WRITE. Mapped to structured interpreter control flow.'
