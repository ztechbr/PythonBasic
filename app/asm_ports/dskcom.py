"""Academic semantic port notes for DSKCOM.ASM.

Original title: DSKCOM - - COMMON ROUTINES FOR DISK BASICS

Purpose
-------
Common disk BASIC operations and numeric/string conversion helpers. Mapped to sandboxed pathlib/file objects.

Translation rule
----------------
This module intentionally does not emulate 8086 registers instruction by
instruction. Register state, flags, segment offsets and jump-table addresses are
translated into Python values, exceptions, dataclasses and method dispatch.
The original file remains under ``reference/asm/DSKCOM.ASM`` for side-by-side study.
"""

ORIGINAL_FILE = 'DSKCOM.ASM'
ORIGINAL_TITLE = 'DSKCOM - - COMMON ROUTINES FOR DISK BASICS'
PUBLIC_ROUTINES = ['FIELD', 'PRGFLI', 'FILIND', 'MKI$', 'MKS$', 'MKD$', 'CVI', 'CVS', 'CVD', 'DLINE', 'PRGFL2', 'LRUN', 'LOAD', 'PRGFIN', 'MERGE', 'SAVE', 'OKGETM', 'RSET', 'LSET', 'CHNENT', 'OUTLOD', 'OKGET2', 'FIXINP']
SUBSECTIONS = ['FILINP AND FILGET -- SCAN A FILE NUMBER AND SETUP PTRFIL', 'FILSCN, FILFRM, AND FILIDX', 'Conversion Routines', 'Read Items From A Sequential File', 'LOAD and RUN routines', 'DISPATCH FOR DIRECT STATEMENT', 'SAVE COMMAND -- ASCII OR BINARY', 'DRIVER CODE FOR CLOSE', '"FIELD" STATEMENT FOR SETTING UP I/O STRINGS', 'Random Non-I/O -- LSET/RSET/FIELD', 'Program I/O -- Fixed Length INPUT']
PORT_NOTE = 'Common disk BASIC operations and numeric/string conversion helpers. Mapped to sandboxed pathlib/file objects.'
