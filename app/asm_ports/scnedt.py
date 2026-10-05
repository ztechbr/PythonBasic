"""Web adaptation of SCNEDT.ASM.

SCNEDT implements a full-screen line editor around KEYIN/SCNRDL. In Flask the
browser owns character editing and submits completed lines. INPUT therefore uses
``InputRequired`` to suspend BASIC execution until the next HTTP command arrives.
"""
from app.models.runtime import InputRequired


def request_line(prompt: str, variables: list[str]):
    raise InputRequired(prompt,variables)
