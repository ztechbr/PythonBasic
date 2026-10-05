"""Port of NEXT86.ASM.

The 8086 source documents the exact FOR stack frame layout. Python models the
same logical frame as ``ForFrame`` instead of packing 16-19 bytes on the CPU
stack. The loop variable, limit, step and resume position are therefore named.
"""
from __future__ import annotations
from app.models.runtime import RuntimeState, ForFrame, BasicError


def begin_for(state: RuntimeState, variable: str, start, limit, step,
              line_index: int, statement_index: int) -> None:
    state.set_var(variable, start)
    # Reusing a FOR variable discards an older frame for that variable.
    state.for_stack=[f for f in state.for_stack if f.variable != variable.upper()]
    state.for_stack.append(ForFrame(variable.upper(), float(limit), float(step), line_index, statement_index))


def next_for(state: RuntimeState, variable: str | None = None):
    if not state.for_stack: raise BasicError('NEXT without FOR')
    idx=len(state.for_stack)-1
    if variable:
        wanted=variable.upper()
        while idx>=0 and state.for_stack[idx].variable != wanted: idx-=1
        if idx<0: raise BasicError('NEXT without FOR')
    frame=state.for_stack[idx]
    current=float(state.get_var(frame.variable))+frame.step
    state.set_var(frame.variable, current)
    cont = current <= frame.limit if frame.step >= 0 else current >= frame.limit
    if cont: return frame.line_index, frame.statement_index
    del state.for_stack[idx:]
    return None
