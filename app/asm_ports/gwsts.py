"""Academic semantic port notes for GWSTS.ASM.

Original title: GWSTS - GW-BASIC Common Statement Support

Purpose
-------
Common statements for screen, graphics, sound and related parsing. The web port records graphics/sound operations in portable state.

Translation rule
----------------
This module intentionally does not emulate 8086 registers instruction by
instruction. Register state, flags, segment offsets and jump-table addresses are
translated into Python values, exceptions, dataclasses and method dispatch.
The original file remains under ``reference/asm/GWSTS.ASM`` for side-by-side study.
"""

ORIGINAL_FILE = 'GWSTS.ASM'
ORIGINAL_TITLE = 'GWSTS - GW-BASIC Common Statement Support'
PUBLIC_ROUTINES = ['PATCHG', 'CLS', 'LOCATE', 'GWWID', 'LCOPYS', 'COLOR', 'GETLIN', 'SCRENF', 'SCREEN', 'PUT', 'GET', 'SCNINT', 'EOSCHK', 'LINLP3', 'VARPT2', 'PLAYS', 'SNDINI', 'SNDRST', 'BEEPS', 'BEEP', 'SOUNDS', 'ONGOTP', 'SETGSB', 'CHKINT', 'COMS', 'COMTRP', 'KEYS', 'KEYTRP', 'SKEYON', 'KEYDSP', 'TKEYOF', 'PENS', 'PENF', 'STRIGS', 'STRIGF', 'STICKF', 'DATES', 'DATEF', 'TIMES', 'TIMEF', 'PALETE', 'TIMER', 'ERDEV', 'IOCTL', 'CHDIR', 'MKDIR', 'RMDIR', 'SHELL', 'ENVIRON', 'VIEW', 'WINDOW', 'PMAP']
SUBSECTIONS = ['CLS,LOCATE,WIDTH (of screen),LCOPY', 'COLOR,GETLIN,SCREEN (function and statement)', 'PUT & GET (Distinguish Disk from Graphics)', 'Parsing Routines for GWSTS', 'Graphics Support Specific to the 8086', 'VARPT2 - VARPTR$ Function', 'PLAY/SOUND statements', 'General Event Trapping Code', 'COM Statement and Event Trapping', 'SOFT KEY Statement and Event Trapping', 'KEYON,  KEYOFF, and KEYDSP', 'Swap Forground & Background Colors', 'PEN Statement and Event Trapping', 'STRIG Statement and Event Trapping', 'DATE - Get/Set Date.', 'TIME - Get/Set Time.', 'Error Handlers for Features not supported in a version']
PORT_NOTE = 'Common statements for screen, graphics, sound and related parsing. The web port records graphics/sound operations in portable state.'
