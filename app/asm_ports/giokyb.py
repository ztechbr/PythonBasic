"""Academic semantic port notes for GIOKYB.ASM.

Original title: GIOKYB - Machine Independent Keyboard Device Driver Code

Purpose
-------
Keyboard driver and break polling. Blocking keyboard loops become HTTP requests and non-blocking pending INPUT state.

Translation rule
----------------
This module intentionally does not emulate 8086 registers instruction by
instruction. Register state, flags, segment offsets and jump-table addresses are
translated into Python values, exceptions, dataclasses and method dispatch.
The original file remains under ``reference/asm/GIOKYB.ASM`` for side-by-side study.
"""

ORIGINAL_FILE = 'GIOKYB.ASM'
ORIGINAL_TITLE = 'GIOKYB - Machine Independent Keyboard Device Driver Code'
PUBLIC_ROUTINES = ['KYBDSP', 'KYBINI', 'KYBTRM', 'KYBCLR', 'KYBSIN', 'INCHRI', 'CHGET', 'KEYIN', 'POLKEY', 'CHKKYB', 'CHSNS', 'SFTOFF', 'KYBSNS', 'FKYSNS', 'INKEY', 'STCTYP', 'SETCSR']
SUBSECTIONS = ['Keyboard Primitive I/O Routines', 'Keyboard Interrupt/Trap Checking in an Operating System Environment', 'CHKKYB - OEM Version of POLKEY', 'CNTCCN, PKQUE, TRPKTB', 'Machine independent Keyboard input routines CHSNS, INKEY$', 'Cursor Support']
PORT_NOTE = 'Keyboard driver and break polling. Blocking keyboard loops become HTTP requests and non-blocking pending INPUT state.'
