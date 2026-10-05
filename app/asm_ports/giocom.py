"""Academic semantic port notes for GIOCOM.ASM.

Original title: GIOCOM - Communications Machine Independent Device Driver Code

Purpose
-------
Serial communications driver. Hardware UART polling is not emulated; the port isolates communications behind a replaceable device adapter.

Translation rule
----------------
This module intentionally does not emulate 8086 registers instruction by
instruction. Register state, flags, segment offsets and jump-table addresses are
translated into Python values, exceptions, dataclasses and method dispatch.
The original file remains under ``reference/asm/GIOCOM.ASM`` for side-by-side study.
"""

ORIGINAL_FILE = 'GIOCOM.ASM'
ORIGINAL_TITLE = 'GIOCOM - Communications Machine Independent Device Driver Code'
PUBLIC_ROUTINES = ['COMDSP', 'COMINI', 'COMTRM', 'COMINI', 'COMTRM', 'POLCOM']
SUBSECTIONS = ['Communications Generalized I/O Routines', 'COM OPEN']
PORT_NOTE = 'Serial communications driver. Hardware UART polling is not emulated; the port isolates communications behind a replaceable device adapter.'
