"""Academic semantic port notes for ADVGRP.ASM.

Original title: ADVGRP - ADVANCED GENERALIZED GRAPHICS STUFF

Purpose
-------
Advanced graphics. PAINT, CIRCLE, GET/PUT and DRAW are represented as device-independent graphics commands rendered by the Flask view.

Translation rule
----------------
This module intentionally does not emulate 8086 registers instruction by
instruction. Register state, flags, segment offsets and jump-table addresses are
translated into Python values, exceptions, dataclasses and method dispatch.
The original file remains under ``reference/asm/ADVGRP.ASM`` for side-by-side study.
"""

ORIGINAL_FILE = 'ADVGRP.ASM'
ORIGINAL_TITLE = 'ADVGRP - ADVANCED GENERALIZED GRAPHICS STUFF'
PUBLIC_ROUTINES = ['PAINT', 'CIRCLE', 'GPUTG', 'DRAW']
SUBSECTIONS = ['PAINT - Fill an area with color', 'CIRCLE - Draw a circle', 'GET and PUT - read and write graphics bit array', 'GRAPHICS MACRO LANGUAGE SUPPORT']
PORT_NOTE = 'Advanced graphics. PAINT, CIRCLE, GET/PUT and DRAW are represented as device-independent graphics commands rendered by the Flask view.'
