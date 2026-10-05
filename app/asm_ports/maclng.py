"""Academic semantic port notes for MACLNG.ASM.

Original title: MACLNG - MACRO LANGUAGE DRIVER

Purpose
-------
Graphics macro-language driver, mainly DRAW support. The port preserves the macro as source commands for a higher-level graphics adapter.

Translation rule
----------------
This module intentionally does not emulate 8086 registers instruction by
instruction. Register state, flags, segment offsets and jump-table addresses are
translated into Python values, exceptions, dataclasses and method dispatch.
The original file remains under ``reference/asm/MACLNG.ASM`` for side-by-side study.
"""

ORIGINAL_FILE = 'MACLNG.ASM'
ORIGINAL_TITLE = 'MACLNG - MACRO LANGUAGE DRIVER'
PUBLIC_ROUTINES = ['FETCHR', 'FETCHZ', 'DECFET', 'VALSCN', 'VALSC2', 'VARGET', 'NEGD', 'MACLNG', 'MCLXEQ']
SUBSECTIONS = []
PORT_NOTE = 'Graphics macro-language driver, mainly DRAW support. The port preserves the macro as source commands for a higher-level graphics adapter.'
