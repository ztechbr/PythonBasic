"""Academic semantic port notes for CALL86.ASM.

Original title: CALL86  8086 CALL Statement

Purpose
-------
CALL into native 8086 addresses. Raw address calls are deliberately replaced with a named Python callback registry.

Translation rule
----------------
This module intentionally does not emulate 8086 registers instruction by
instruction. Register state, flags, segment offsets and jump-table addresses are
translated into Python values, exceptions, dataclasses and method dispatch.
The original file remains under ``reference/asm/CALL86.ASM`` for side-by-side study.
"""

ORIGINAL_FILE = 'CALL86.ASM'
ORIGINAL_TITLE = 'CALL86  8086 CALL Statement'
PUBLIC_ROUTINES = ['CALLS', 'CALLSL']
SUBSECTIONS = []
PORT_NOTE = 'CALL into native 8086 addresses. Raw address calls are deliberately replaced with a named Python callback registry.'
