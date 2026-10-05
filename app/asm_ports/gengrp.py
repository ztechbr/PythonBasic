"""Academic semantic port notes for GENGRP.ASM.

Original title: GENGRP  GENERALIZED GRAPHICS    /WHG

Purpose
-------
General graphics primitives such as PSET/PRESET/POINT/LINE and coordinate scanning. Mapped to graphics command objects.

Translation rule
----------------
This module intentionally does not emulate 8086 registers instruction by
instruction. Register state, flags, segment offsets and jump-table addresses are
translated into Python values, exceptions, dataclasses and method dispatch.
The original file remains under ``reference/asm/GENGRP.ASM`` for side-by-side study.
"""

ORIGINAL_FILE = 'GENGRP.ASM'
ORIGINAL_TITLE = 'GENGRP  GENERALIZED GRAPHICS    /WHG'
PUBLIC_ROUTINES = ['HLFDE', 'SCAND', 'ATRSCN', 'SCAN1', 'DOGRPH', 'XCHGX', 'XCHGY', 'XDELT', 'YDELT', 'PSET', 'PRESET', 'POINT', 'NEGHL', 'GLINE', 'GRPINI', 'GRPRST']
SUBSECTIONS = ['SCAN A COORDINATE - SCAN1 AND SCAND', 'PSET,PRESET,POINT', 'UTILITY ROUTINES FOR LINE CODE', 'LINE COMMAND', 'Graphics Initialization']
PORT_NOTE = 'General graphics primitives such as PSET/PRESET/POINT/LINE and coordinate scanning. Mapped to graphics command objects.'
