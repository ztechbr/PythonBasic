"""Port guide for GWRAM.ASM.

Every mutable OEM-independent RAM declaration is represented as a named field in
``app.models.runtime.RuntimeState``. This file is intentionally small because
Python object attributes *are* the RAM layout for the semantic port.
"""
from app.models.runtime import RuntimeState


def allocate_runtime() -> RuntimeState:
    return RuntimeState()
