"""Academic semantic port notes for GIOLPT.ASM.

Original title: GIOLPT - Line Printer Machine Independent Device Driver Code

Purpose
-------
Line-printer driver. LPRINT/LLIST append to an in-memory printer spool that can later be exported.

Translation rule
----------------
This module intentionally does not emulate 8086 registers instruction by
instruction. Register state, flags, segment offsets and jump-table addresses are
translated into Python values, exceptions, dataclasses and method dispatch.
The original file remains under ``reference/asm/GIOLPT.ASM`` for side-by-side study.
"""

ORIGINAL_FILE = 'GIOLPT.ASM'
ORIGINAL_TITLE = 'GIOLPT - Line Printer Machine Independent Device Driver Code'
PUBLIC_ROUTINES = ['LPTDSP', 'LPTINI', 'LPTTRM', 'LPOS']
SUBSECTIONS = ['Line Printer Primitive I/O Routines']
PORT_NOTE = 'Line-printer driver. LPRINT/LLIST append to an in-memory printer spool that can later be exported.'
