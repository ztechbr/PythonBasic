"""Academic semantic port notes for BIBOOT.ASM.

Original title: BIBOOT - Initialization File for ASM86 BASICs

Purpose
-------
8086/DOS bootstrap. Segment copying and EXE control-block relocation have no Python equivalent; startup becomes object construction.

Translation rule
----------------
This module intentionally does not emulate 8086 registers instruction by
instruction. Register state, flags, segment offsets and jump-table addresses are
translated into Python values, exceptions, dataclasses and method dispatch.
The original file remains under ``reference/asm/BIBOOT.ASM`` for side-by-side study.
"""

ORIGINAL_FILE = 'BIBOOT.ASM'
ORIGINAL_TITLE = 'BIBOOT - Initialization File for ASM86 BASICs'
PUBLIC_ROUTINES = ['LSTVAR']
SUBSECTIONS = ['ASM86 Version']
PORT_NOTE = '8086/DOS bootstrap. Segment copying and EXE control-block relocation have no Python equivalent; startup becomes object construction.'
