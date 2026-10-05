"""Academic semantic port notes for GIO86.ASM.

Original title: GIO86   - BASIC-86 Interpreter Device Independent I/O Module

Purpose
-------
Device-independent I/O facade. Python dispatches to file, screen, keyboard and printer abstractions rather than DOS devices.

Translation rule
----------------
This module intentionally does not emulate 8086 registers instruction by
instruction. Register state, flags, segment offsets and jump-table addresses are
translated into Python values, exceptions, dataclasses and method dispatch.
The original file remains under ``reference/asm/GIO86.ASM`` for side-by-side study.
"""

ORIGINAL_FILE = 'GIO86.ASM'
ORIGINAL_TITLE = 'GIO86   - BASIC-86 Interpreter Device Independent I/O Module'
PUBLIC_ROUTINES = ['OPEN', 'CLOSE', 'WIDTHS', 'BLOAD', 'BSAVE', 'LPRINT', 'PRINT', 'EOF', 'LOC', 'LOF', 'DPUTG', 'FILINP', 'FILGET', 'GETPTR', 'FILSET', 'FILSCN', 'DIRDO', 'ADRGET', 'PRGFIL', 'NULOPM', 'CLSALL', 'CLSFIL', 'INCHR', 'INDSKC', 'INCHSI', 'CRFIN', 'CRDONZ', 'FININL', 'CRDO', 'OUTDO', 'FILOU3', 'BAKCHR', 'BCHRSI', 'BINSAV', 'BINPSV', 'DEVBIN', 'DEVBOT', 'FSTLOD', 'PTRGPS', 'PTRWID', 'XTABCR', 'EXPTAB', 'CRIFEL', 'UPDPOS', 'PTRDSP', 'NAMSCN', 'INIFDB', 'SCDASC', 'SCDBIN', 'PDCBAX', 'PCBAX', 'PBAX', 'INITQ', 'PUTQ', 'GETQ', 'NUMQ', 'LFTQ', 'GIOINI', 'GIOTRM', 'FINPRT', 'FINLPT', 'SAVVEC', 'SETVEC']
SUBSECTIONS = ['OPEN statement', 'CLOSE, WIDTH Statements', 'BSAVE, BLOAD Statements', 'LPRINT, PRINT Statements', 'EOF, LOC, LOF  Functions', 'GET/PUT - Random disk I/O Statements', 'Misc. Parsing Routines', 'Major I/O Routines', 'General routines useful to low-level device drivers', 'File Dispatch Routines', 'NAMSCN, PARDEV - Device/Filename scanning routines', 'File Data Block Management Routines', 'General Queue support routines', 'I/O Initialization Called by INIT', 'MSDOS   Abort/Initialization/Termination Processing']
PORT_NOTE = 'Device-independent I/O facade. Python dispatches to file, screen, keyboard and printer abstractions rather than DOS devices.'
