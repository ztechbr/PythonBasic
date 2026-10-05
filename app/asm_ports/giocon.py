"""Academic semantic port notes for GIOCON.ASM.

Original title: GIOCON - Machine Independent CONS: Device Support

Purpose
-------
CONS device support. Console output maps to the web terminal ScreenBuffer.

Translation rule
----------------
This module intentionally does not emulate 8086 registers instruction by
instruction. Register state, flags, segment offsets and jump-table addresses are
translated into Python values, exceptions, dataclasses and method dispatch.
The original file remains under ``reference/asm/GIOCON.ASM`` for side-by-side study.
"""

ORIGINAL_FILE = 'GIOCON.ASM'
ORIGINAL_TITLE = 'GIOCON - Machine Independent CONS: Device Support'
PUBLIC_ROUTINES = ['CONDSP', '_RET', 'CONSOT']
SUBSECTIONS = ['CONS (Raw-CRT output Dispatch Table and Routines)']
PORT_NOTE = 'CONS device support. Console output maps to the web terminal ScreenBuffer.'
