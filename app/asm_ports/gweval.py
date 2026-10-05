"""Facade corresponding to GWEVAL.ASM.

FRMEVL/EVAL in ASM operate on token pointers and the FAC accumulator. The Python
facade receives source text and returns a Python value explicitly.
"""
from app.services.expression import ExpressionParser
from app.models.runtime import RuntimeState


def frmevl(state: RuntimeState, source: str):
    return ExpressionParser(state).evaluate(source)
