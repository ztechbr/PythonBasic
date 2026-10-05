"""Runtime model for the educational GW-BASIC port.

The original interpreter stores most state in the 8086 data segment, especially
GWDATA.ASM and GWRAM.ASM.  In Python we make that implicit RAM explicit and typed.

ASM mapping
-----------
- GWDATA.ASM: token/error tables, interpreter globals, FAC/ARG numeric state.
- GWRAM.ASM: mutable RAM declarations used by statements and devices.
- GWINIT.ASM: initializes pointers such as TXTTAB/VARTAB/STREND/FRETOP.

Instead of byte offsets and segment registers, this port uses dataclasses,
dictionaries and Python objects.  This preserves interpreter semantics while
making memory ownership visible to students.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


class BasicError(Exception):
    """GW-BASIC style runtime/syntax error with a compact message."""

    def __init__(self, message: str, line: int | None = None):
        self.message = message
        self.line = line
        super().__init__(f"{message}{' in ' + str(line) if line is not None else ''}")


class InputRequired(Exception):
    """Non-blocking replacement for the old keyboard INPUT wait loop."""

    def __init__(self, prompt: str, variables: list[str]):
        self.prompt = prompt
        self.variables = variables
        super().__init__(prompt)


@dataclass(slots=True)
class ForFrame:
    variable: str
    limit: float
    step: float
    line_index: int
    statement_index: int


@dataclass(slots=True)
class WhileFrame:
    line_index: int
    statement_index: int
    condition: str


@dataclass(slots=True)
class FileHandle:
    number: int
    path: Path
    mode: str
    handle: Any


@dataclass
class ScreenBuffer:
    """Web-safe replacement for SCNDRV/GIOSCN video memory."""

    width: int = 80
    height: int = 25
    lines: list[str] = field(default_factory=list)
    cursor_row: int = 1
    cursor_col: int = 1

    def clear(self) -> None:
        self.lines.clear()
        self.cursor_row = self.cursor_col = 1

    def write(self, text: str, newline: bool = True) -> None:
        if not self.lines:
            self.lines.append("")
        parts = text.split("\n")
        for i, part in enumerate(parts):
            self.lines[-1] += part
            if i < len(parts) - 1:
                self.lines.append("")
        if newline:
            self.lines.append("")
        self.lines = self.lines[-2000:]
        self.cursor_row = min(self.height, max(1, len(self.lines)))
        self.cursor_col = len(self.lines[-1]) + 1 if self.lines else 1

    def text(self) -> str:
        return "\n".join(self.lines).rstrip("\n")


@dataclass
class RuntimeState:
    """High-level equivalent of the mutable BASIC interpreter data segment."""

    program: dict[int, str] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)
    arrays: dict[str, Any] = field(default_factory=dict)
    data_values: list[Any] = field(default_factory=list)
    data_pointer: int = 0
    gosub_stack: list[tuple[int, int]] = field(default_factory=list)
    for_stack: list[ForFrame] = field(default_factory=list)
    while_stack: list[WhileFrame] = field(default_factory=list)
    output: list[str] = field(default_factory=list)
    printer_output: list[str] = field(default_factory=list)
    screen: ScreenBuffer = field(default_factory=ScreenBuffer)
    trace: bool = False
    stopped: bool = False
    pc_line_index: int = 0
    pc_statement_index: int = 0
    running: bool = False
    pending_input: Optional[list[str]] = None
    pending_prompt: str = "? "
    pending_resume: Optional[tuple[int, int]] = None
    file_handles: dict[int, FileHandle] = field(default_factory=dict)
    common_variables: set[str] = field(default_factory=set)
    last_error: Optional[str] = None
    random_seeded: bool = False
    memory: dict[int, int] = field(default_factory=dict)
    io_ports: dict[int, int] = field(default_factory=dict)
    graphics_commands: list[dict[str, Any]] = field(default_factory=list)
    call_registry: dict[str, Any] = field(default_factory=dict)

    def reset_runtime(self, preserve_program: bool = True) -> None:
        """Equivalent to CLEAR/STKINI style initialization in BIMISC.ASM."""
        program = self.program if preserve_program else {}
        for fh in list(self.file_handles.values()):
            try:
                fh.handle.close()
            except Exception:
                pass
        self.__dict__.update(RuntimeState(program=program).__dict__)

    def emit(self, text: str = "", newline: bool = True) -> None:
        self.output.append(text + ("\n" if newline else ""))
        self.screen.write(text, newline=newline)

    def consume_output(self) -> str:
        value = "".join(self.output)
        self.output.clear()
        return value

    @staticmethod
    def normalize_var(name: str) -> str:
        return name.strip().upper()

    def default_value(self, name: str) -> Any:
        return "" if name.endswith("$") else 0

    def get_var(self, name: str) -> Any:
        key = self.normalize_var(name)
        return self.variables.get(key, self.default_value(key))

    def set_var(self, name: str, value: Any) -> None:
        key = self.normalize_var(name)
        if key.endswith("$"):
            value = str(value)
        elif key.endswith("%"):
            value = int(float(value))
        else:
            value = float(value) if isinstance(value, str) and _looks_number(value) else value
        self.variables[key] = value


def _looks_number(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False
