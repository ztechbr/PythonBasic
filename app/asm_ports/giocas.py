"""Academic semantic port notes for GIOCAS.ASM.

Original title: GIOCAS - Cassette Machine Independent Device Driver Code

Purpose
-------
Cassette device hook. Preserved as an educational compatibility abstraction; no physical cassette hardware is required.

Translation rule
----------------
This module intentionally does not emulate 8086 registers instruction by
instruction. Register state, flags, segment offsets and jump-table addresses are
translated into Python values, exceptions, dataclasses and method dispatch.
The original file remains under ``reference/asm/GIOCAS.ASM`` for side-by-side study.
"""

ORIGINAL_FILE = 'GIOCAS.ASM'
ORIGINAL_TITLE = 'GIOCAS - Cassette Machine Independent Device Driver Code'
PUBLIC_ROUTINES = ['MOTOR']
SUBSECTIONS = []
PORT_NOTE = 'Cassette device hook. Preserved as an educational compatibility abstraction; no physical cassette hardware is required.'
