"""Semantic port of SCNDRV.ASM.

The original driver owns cursor movement, line reading, scrolling and physical
screen output. ``ScreenBuffer`` offers the same logical responsibilities without
binding them to CGA/MDA/BIOS memory.
"""
from app.models.runtime import ScreenBuffer


def scnclr(screen: ScreenBuffer): screen.clear()
def scnout(screen: ScreenBuffer, value): screen.write(str(value), newline=False)
def scnpos(screen: ScreenBuffer): return screen.cursor_row, screen.cursor_col
def scnloc(screen: ScreenBuffer, row: int, col: int):
    screen.cursor_row=max(1,int(row)); screen.cursor_col=max(1,int(col))
