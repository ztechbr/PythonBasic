"""Academic semantic port notes for GWINIT.ASM.

Original title: GWINIT GW-BASIC-86 Initialization

Purpose
-------
System initialization and memory-layout setup. Python initializes RuntimeState and sandbox directories.

Translation rule
----------------
This module intentionally does not emulate 8086 registers instruction by
instruction. Register state, flags, segment offsets and jump-table addresses are
translated into Python values, exceptions, dataclasses and method dispatch.
The original file remains under ``reference/asm/GWINIT.ASM`` for side-by-side study.
"""

ORIGINAL_FILE = 'GWINIT.ASM'
ORIGINAL_TITLE = 'GWINIT GW-BASIC-86 Initialization'
PUBLIC_ROUTINES = ['INIT', 'CMDERR', '$LAST', 'LASTWR']
SUBSECTIONS = ['INIT - System Initialization Code', 'Read Operating System Parameters (memsiz etc.)', 'Allocate Space for Disk Buffers', 'INIT TXTAB, STKTOP, VARTAB, MEMSIZ, FRETOP, STREND']
PORT_NOTE = 'System initialization and memory-layout setup. Python initializes RuntimeState and sandbox directories.'
