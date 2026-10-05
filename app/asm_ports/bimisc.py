"""Academic semantic port notes for BIMISC.ASM.

Original title: BIMISC  BASIC Interpreter miscellaneous routines/WHG/PGA etc.

Purpose
-------
Miscellaneous runtime control such as CLEAR, NEW/SCRATCH, RUN, STOP/END, CONT and stack initialization. Implemented in RuntimeState and GWBasicInterpreter.

Translation rule
----------------
This module intentionally does not emulate 8086 registers instruction by
instruction. Register state, flags, segment offsets and jump-table addresses are
translated into Python values, exceptions, dataclasses and method dispatch.
The original file remains under ``reference/asm/BIMISC.ASM`` for side-by-side study.
"""

ORIGINAL_FILE = 'BIMISC.ASM'
ORIGINAL_TITLE = 'BIMISC  BASIC Interpreter miscellaneous routines/WHG/PGA etc.'
PUBLIC_ROUTINES = ['STOPRG', 'TON', 'TOFF', 'CLEARC', 'STOP', 'ISLET', 'ISLET2', 'STKINI', 'GETSTK', 'SCRATH', 'SCRTCH', 'STPEND', 'CONT', 'ENDST', 'GTMPRT', 'RUNC', 'STPEND', 'ENDCON', 'RESTORE', 'STOP', 'RESFIN', 'STKERR', 'REASON', 'OMERR', 'OMERRR', 'NODSKS', 'DCOMPR', 'SYNCHR', 'T_ON', 'T_STOP', 'T_REQ', 'ONTRP', 'OFFTRP', 'STPTRP', 'RSTTRP', 'REQTRP', 'SETTRP', 'FRETRP', 'INITRP', 'GOTRP', 'CTROPT', 'CTRLPT', 'NULL', 'SWAP', 'ERASE', 'POPAHT', 'CLEAR', 'SUBDE', 'ISFLIO']
SUBSECTIONS = ['NODSKS, SCRATCH (NEW), RUNC, CLEARC, STKINI, QINLIN', 'DCOMPR, SYNCHR - REPLACEMENTS FOR COMPAR & SYNCHK IN RSTLES VERSION', 'TRAP ROUTINES - ON, OFF, STOP, INIT, REQUEST, FREE, RESET', 'RESTORE, STOP, END', 'CTRLPT, DDT, CONT, NULL, TRON, TROFF', 'SWAP, ERASE', 'CLEAR']
PORT_NOTE = 'Miscellaneous runtime control such as CLEAR, NEW/SCRATCH, RUN, STOP/END, CONT and stack initialization. Implemented in RuntimeState and GWBasicInterpreter.'
