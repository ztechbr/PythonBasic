"""Academic semantic port notes for GWLIST.ASM.

Original title: GWLIST Copied from BINTRP.MAC

Purpose
-------
LIST/LLIST/DELETE and program-line listing support. Implemented against the program dictionary.

Translation rule
----------------
This module intentionally does not emulate 8086 registers instruction by
instruction. Register state, flags, segment offsets and jump-table addresses are
translated into Python values, exceptions, dataclasses and method dispatch.
The original file remains under ``reference/asm/GWLIST.ASM`` for side-by-side study.
"""

ORIGINAL_FILE = 'GWLIST.ASM'
ORIGINAL_TITLE = 'GWLIST Copied from BINTRP.MAC'
PUBLIC_ROUTINES = ['LLIST', 'LIST', 'LISPRT', 'BUFLIN', 'PLOOP2', 'TSTANM', 'DELETE', 'DEL']
SUBSECTIONS = ['ROM VERSION INITALIZATION, AND CONSTANTS', 'EXTENDED LIST, DELETE, LLIST']
PORT_NOTE = 'LIST/LLIST/DELETE and program-line listing support. Implemented against the program dictionary.'
