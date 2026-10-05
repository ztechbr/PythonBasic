"""Academic semantic port notes for GIODSK.ASM.

Original title: GIODSK - BASIC-86 Generalized I/O Disk Driver

Purpose
-------
Disk driver and directory operations. DOS FCB/handle semantics become sandboxed host filesystem operations.

Translation rule
----------------
This module intentionally does not emulate 8086 registers instruction by
instruction. Register state, flags, segment offsets and jump-table addresses are
translated into Python values, exceptions, dataclasses and method dispatch.
The original file remains under ``reference/asm/GIODSK.ASM`` for side-by-side study.
"""

ORIGINAL_FILE = 'GIODSK.ASM'
ORIGINAL_TITLE = 'GIODSK - BASIC-86 Generalized I/O Disk Driver'
PUBLIC_ROUTINES = ['DSKDSP', 'DFSTLD', 'PROSAV', 'CMPFBC', 'PENCOD', 'PROLOD', 'PROCHK', 'PRODIR', 'FILES', 'KILL', 'NAME', 'RESET', 'SYSTEM', 'SYSTME']
SUBSECTIONS = ['GLOBAL TEMPS and DEFS', 'Misc. Disk Routines', 'OPEN hook for Disk and all Directory handling', 'CLOSE (CLSFIL) hook for Disk files', 'Disk Sequential Input', 'Disk Sequential Output', 'GET and PUT for Disk Files', 'Primitive Disk sector I/O routines', 'CHKFOP - Check for file already OPEN', 'DFSTLD - Fast Binary Program Load (from DISK)', 'PROSAV - Protected SAVE', 'KILL, FILES, NAME commands', 'RESET and SYSTEM statements']
PORT_NOTE = 'Disk driver and directory operations. DOS FCB/handle semantics become sandboxed host filesystem operations.'
