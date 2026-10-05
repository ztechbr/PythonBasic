"""Facade corresponding to GWMAIN.ASM.

GWMAIN's MAIN/NEWSTT statement loop is implemented by
``app.services.interpreter.GWBasicInterpreter``. This alias gives students a
one-hop mapping from the historical source filename to the Python engine.
"""
from app.services.interpreter import GWBasicInterpreter

__all__=['GWBasicInterpreter']
