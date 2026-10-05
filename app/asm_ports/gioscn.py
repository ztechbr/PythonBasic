"""Academic semantic port notes for GIOSCN.ASM.

Original title: GIOSCN - Screen Machine Independent Device Driver Code

Purpose
-------
Screen device bridge. Physical CRT calls become ScreenBuffer operations.

Translation rule
----------------
This module intentionally does not emulate 8086 registers instruction by
instruction. Register state, flags, segment offsets and jump-table addresses are
translated into Python values, exceptions, dataclasses and method dispatch.
The original file remains under ``reference/asm/GIOSCN.ASM`` for side-by-side study.
"""

ORIGINAL_FILE = 'GIOSCN.ASM'
ORIGINAL_TITLE = 'GIOSCN - Screen Machine Independent Device Driver Code'
PUBLIC_ROUTINES = ['SCNDSP', 'SCNINI', 'SCNTRM', 'SCNSWD', 'SCNSOT', 'SCNGPS', 'SCNGWD', 'SCNSCW', 'SCNGCW', 'CALTTY', '$CATTY', 'POS']
SUBSECTIONS = ['CRT Primitive I/O Routines']
PORT_NOTE = 'Screen device bridge. Physical CRT calls become ScreenBuffer operations.'
