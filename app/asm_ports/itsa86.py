"""Academic semantic port notes for ITSA86.ASM.

Original title: ITSA86 - Resident Initialization for I8086

Purpose
-------
8086 resident initialization and segment mapping. Not required on Python; semantic initialization is handled in create_app/runtime constructors.

Translation rule
----------------
This module intentionally does not emulate 8086 registers instruction by
instruction. Register state, flags, segment offsets and jump-table addresses are
translated into Python values, exceptions, dataclasses and method dispatch.
The original file remains under ``reference/asm/ITSA86.ASM`` for side-by-side study.
"""

ORIGINAL_FILE = 'ITSA86.ASM'
ORIGINAL_TITLE = 'ITSA86 - Resident Initialization for I8086'
PUBLIC_ROUTINES = ['WORDS', 'INITSA', 'BASVAR', 'MAPCLC', 'MAPINI', 'SEGOFF']
SUBSECTIONS = ['INITSA', 'Initialization Support Routines', 'End of the New CS:']
PORT_NOTE = '8086 resident initialization and segment mapping. Not required on Python; semantic initialization is handled in create_app/runtime constructors.'
