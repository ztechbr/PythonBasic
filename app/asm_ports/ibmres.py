"""Academic semantic port notes for IBMRES.ASM.

Original title: IBMRES - IBM compatible reserved words / MLC

Purpose
-------
Reserved-word/token tables and list/crunch support. Python parses textual keywords directly, so binary token numbers are documentation rather than storage.

Translation rule
----------------
This module intentionally does not emulate 8086 registers instruction by
instruction. Register state, flags, segment offsets and jump-table addresses are
translated into Python values, exceptions, dataclasses and method dispatch.
The original file remains under ``reference/asm/IBMRES.ASM`` for side-by-side study.
"""

ORIGINAL_FILE = 'IBMRES.ASM'
ORIGINAL_TITLE = 'IBMRES - IBM compatible reserved words / MLC'
PUBLIC_ROUTINES = ['$KEY2B', '$COM2B', '$PEN2B', '$STR2B', 'STMDSP', 'NUMCMD', 'THENTK', 'TABTK', 'STEPTK', 'USRTK', 'FNTK', 'SPCTK', 'NOTTK', 'ERLTK', 'ERCTK', 'USINTK', 'INSRTK', 'SNGQTK', 'CLINTK', 'GREATK', 'EQULTK', 'LESSTK', 'PLUSTK', 'MINUTK', 'MULTK', 'DIVTK', 'EXPTK', 'IDIVTK', 'LSTOPK', 'FUNDSP', 'ONEFUN', 'MIDTK', 'SQRTK', 'ATNTK', 'LASNUM', '$FIX', 'ALPTAB', 'RESLST', 'SPCTAB', 'ALPTAX', 'NUMGFN', 'BOTCON', 'TOPCON', '$RNDFN', '$DATCO', '$REMCO', 'NMREL', '$CHRFN', '$CSNGF', '$CDBLF', 'CRUNCX', 'LISTX', 'NEWSTX', 'EVALX']
SUBSECTIONS = ['Equates and External Declarations', 'Extended reserved words', 'CRUNCH code to handle extended reserved words', 'LIST code for extended reserved words', 'Extended Statement Dispatching', 'EVAL code for extended functions']
PORT_NOTE = 'Reserved-word/token tables and list/crunch support. Python parses textual keywords directly, so binary token numbers are documentation rather than storage.'
