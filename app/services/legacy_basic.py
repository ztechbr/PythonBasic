"""Legacy GW-BASIC program-file codec.

Academic purpose
----------------
GWMAIN.ASM tokenises source as it is entered and DSKCOM/GIO86 save that packed
representation.  Cassette BASIC uses the same tokenised BASIC payload but wraps
it in the IBM PC cassette record structure instead of the DOS file wrapper.

This module keeps that historical binary representation separate from the modern
interpreter.  It can detokenise genuine GW-BASIC/BASICA token streams and emits a
compatible token stream for programs created by this Python port.
"""
from __future__ import annotations

import math
import re
import struct
from typing import Mapping

# Exhaustive GW-BASIC reserved-word table documented by the interpreter family.
# Single-byte tokens are ints; extended tokens are byte strings.
TOKEN_TO_KEYWORD: dict[bytes, str] = {
    bytes([0x81]): 'END', bytes([0x82]): 'FOR', bytes([0x83]): 'NEXT', bytes([0x84]): 'DATA',
    bytes([0x85]): 'INPUT', bytes([0x86]): 'DIM', bytes([0x87]): 'READ', bytes([0x88]): 'LET',
    bytes([0x89]): 'GOTO', bytes([0x8A]): 'RUN', bytes([0x8B]): 'IF', bytes([0x8C]): 'RESTORE',
    bytes([0x8D]): 'GOSUB', bytes([0x8E]): 'RETURN', bytes([0x8F]): 'REM', bytes([0x90]): 'STOP',
    bytes([0x91]): 'PRINT', bytes([0x92]): 'CLEAR', bytes([0x93]): 'LIST', bytes([0x94]): 'NEW',
    bytes([0x95]): 'ON', bytes([0x96]): 'WAIT', bytes([0x97]): 'DEF', bytes([0x98]): 'POKE',
    bytes([0x99]): 'CONT', bytes([0x9C]): 'OUT', bytes([0x9D]): 'LPRINT', bytes([0x9E]): 'LLIST',
    bytes([0xA0]): 'WIDTH', bytes([0xA1]): 'ELSE', bytes([0xA2]): 'TRON', bytes([0xA3]): 'TROFF',
    bytes([0xA4]): 'SWAP', bytes([0xA5]): 'ERASE', bytes([0xA6]): 'EDIT', bytes([0xA7]): 'ERROR',
    bytes([0xA8]): 'RESUME', bytes([0xA9]): 'DELETE', bytes([0xAA]): 'AUTO', bytes([0xAB]): 'RENUM',
    bytes([0xAC]): 'DEFSTR', bytes([0xAD]): 'DEFINT', bytes([0xAE]): 'DEFSNG', bytes([0xAF]): 'DEFDBL',
    bytes([0xB0]): 'LINE', bytes([0xB1]): 'WHILE', bytes([0xB2]): 'WEND', bytes([0xB3]): 'CALL',
    bytes([0xB7]): 'WRITE', bytes([0xB8]): 'OPTION', bytes([0xB9]): 'RANDOMIZE', bytes([0xBA]): 'OPEN',
    bytes([0xBB]): 'CLOSE', bytes([0xBC]): 'LOAD', bytes([0xBD]): 'MERGE', bytes([0xBE]): 'SAVE',
    bytes([0xBF]): 'COLOR', bytes([0xC0]): 'CLS', bytes([0xC1]): 'MOTOR', bytes([0xC2]): 'BSAVE',
    bytes([0xC3]): 'BLOAD', bytes([0xC4]): 'SOUND', bytes([0xC5]): 'BEEP', bytes([0xC6]): 'PSET',
    bytes([0xC7]): 'PRESET', bytes([0xC8]): 'SCREEN', bytes([0xC9]): 'KEY', bytes([0xCA]): 'LOCATE',
    bytes([0xCC]): 'TO', bytes([0xCD]): 'THEN', bytes([0xCE]): 'TAB(', bytes([0xCF]): 'STEP',
    bytes([0xD0]): 'USR', bytes([0xD1]): 'FN', bytes([0xD2]): 'SPC(', bytes([0xD3]): 'NOT',
    bytes([0xD4]): 'ERL', bytes([0xD5]): 'ERR', bytes([0xD6]): 'STRING$', bytes([0xD7]): 'USING',
    bytes([0xD8]): 'INSTR', bytes([0xD9]): "'", bytes([0xDA]): 'VARPTR', bytes([0xDB]): 'CSRLIN',
    bytes([0xDC]): 'POINT', bytes([0xDD]): 'OFF', bytes([0xDE]): 'INKEY$',
    bytes([0xE6]): '>', bytes([0xE7]): '=', bytes([0xE8]): '<', bytes([0xE9]): '+',
    bytes([0xEA]): '-', bytes([0xEB]): '*', bytes([0xEC]): '/', bytes([0xED]): '^',
    bytes([0xEE]): 'AND', bytes([0xEF]): 'OR', bytes([0xF0]): 'XOR', bytes([0xF1]): 'EQV',
    bytes([0xF2]): 'IMP', bytes([0xF3]): 'MOD', bytes([0xF4]): '\\',
    b'\xFD\x81': 'CVI', b'\xFD\x82': 'CVS', b'\xFD\x83': 'CVD', b'\xFD\x84': 'MKI$',
    b'\xFD\x85': 'MKS$', b'\xFD\x86': 'MKD$', b'\xFD\x8B': 'EXTERR',
    b'\xFE\x81': 'FILES', b'\xFE\x82': 'FIELD', b'\xFE\x83': 'SYSTEM', b'\xFE\x84': 'NAME',
    b'\xFE\x85': 'LSET', b'\xFE\x86': 'RSET', b'\xFE\x87': 'KILL', b'\xFE\x88': 'PUT',
    b'\xFE\x89': 'GET', b'\xFE\x8A': 'RESET', b'\xFE\x8B': 'COMMON', b'\xFE\x8C': 'CHAIN',
    b'\xFE\x8D': 'DATE$', b'\xFE\x8E': 'TIME$', b'\xFE\x8F': 'PAINT', b'\xFE\x90': 'COM',
    b'\xFE\x91': 'CIRCLE', b'\xFE\x92': 'DRAW', b'\xFE\x93': 'PLAY', b'\xFE\x94': 'TIMER',
    b'\xFE\x95': 'ERDEV', b'\xFE\x96': 'IOCTL', b'\xFE\x97': 'CHDIR', b'\xFE\x98': 'MKDIR',
    b'\xFE\x99': 'RMDIR', b'\xFE\x9A': 'SHELL', b'\xFE\x9B': 'ENVIRON', b'\xFE\x9C': 'VIEW',
    b'\xFE\x9D': 'WINDOW', b'\xFE\x9E': 'PMAP', b'\xFE\x9F': 'PALETTE', b'\xFE\xA0': 'LCOPY',
    b'\xFE\xA1': 'CALLS', b'\xFE\xA4': 'NOISE', b'\xFE\xA5': 'PCOPY', b'\xFE\xA6': 'TERM',
    b'\xFE\xA7': 'LOCK', b'\xFE\xA8': 'UNLOCK',
    b'\xFF\x81': 'LEFT$', b'\xFF\x82': 'RIGHT$', b'\xFF\x83': 'MID$', b'\xFF\x84': 'SGN',
    b'\xFF\x85': 'INT', b'\xFF\x86': 'ABS', b'\xFF\x87': 'SQR', b'\xFF\x88': 'RND',
    b'\xFF\x89': 'SIN', b'\xFF\x8A': 'LOG', b'\xFF\x8B': 'EXP', b'\xFF\x8C': 'COS',
    b'\xFF\x8D': 'TAN', b'\xFF\x8E': 'ATN', b'\xFF\x8F': 'FRE', b'\xFF\x90': 'INP',
    b'\xFF\x91': 'POS', b'\xFF\x92': 'LEN', b'\xFF\x93': 'STR$', b'\xFF\x94': 'VAL',
    b'\xFF\x95': 'ASC', b'\xFF\x96': 'CHR$', b'\xFF\x97': 'PEEK', b'\xFF\x98': 'SPACE$',
    b'\xFF\x99': 'OCT$', b'\xFF\x9A': 'HEX$', b'\xFF\x9B': 'LPOS', b'\xFF\x9C': 'CINT',
    b'\xFF\x9D': 'CSNG', b'\xFF\x9E': 'CDBL', b'\xFF\x9F': 'FIX', b'\xFF\xA0': 'PEN',
    b'\xFF\xA1': 'STICK', b'\xFF\xA2': 'STRIG', b'\xFF\xA3': 'EOF', b'\xFF\xA4': 'LOC',
    b'\xFF\xA5': 'LOF',
}
KEYWORD_TO_TOKEN = {v: k for k, v in TOKEN_TO_KEYWORD.items()}

# Match longest words first. Operators are handled as ordinary reserved tokens.
_KEYWORDS = sorted(KEYWORD_TO_TOKEN, key=len, reverse=True)


def mbf_to_float(raw: bytes) -> float:
    """Decode 4- or 8-byte Microsoft Binary Format value."""
    if len(raw) not in (4, 8):
        raise ValueError('MBF must be 4 or 8 bytes')
    exponent = raw[-1]
    if exponent == 0:
        return 0.0
    mantissa_bytes = raw[:-1]
    high = mantissa_bytes[-1]
    sign = -1.0 if high & 0x80 else 1.0
    frac_bits = 23 if len(raw) == 4 else 55
    # M1 is the most-significant mantissa byte but appears just before exponent.
    fraction = high & 0x7F
    for b in reversed(mantissa_bytes[:-1]):
        fraction = (fraction << 8) | b
    mantissa_int = (1 << frac_bits) | fraction
    mantissa = mantissa_int / float(1 << (frac_bits + 1))
    return sign * math.ldexp(mantissa, exponent - 128)



def float_to_mbf(value: float, double: bool = False) -> bytes:
    """Encode a Python finite float as GW-BASIC Microsoft Binary Format.

    MBF stores an 8-bit excess-128 exponent and a normalised mantissa whose
    implicit leading bit represents 1/2. Single precision has 23 fraction bits,
    double precision 55. This is the inverse of :func:`mbf_to_float` and is used
    only for legacy file interchange, not for Python runtime arithmetic.
    """
    value=float(value)
    if not math.isfinite(value):
        raise ValueError('MBF has no infinity or NaN')
    nbytes=8 if double else 4
    frac_bits=55 if double else 23
    if value == 0.0:
        return bytes(nbytes)
    sign=value < 0
    m,e=math.frexp(abs(value))  # 0.5 <= m < 1
    exponent=e+128
    if exponent <= 0 or exponent >= 256:
        raise OverflowError('Overflow')
    fraction=int(round((m-0.5) * (1 << (frac_bits+1))))
    if fraction >= (1 << frac_bits):
        fraction=0; exponent += 1
        if exponent >= 256: raise OverflowError('Overflow')
    low_count=(frac_bits-7)//8
    low=bytes((fraction >> (8*i)) & 0xFF for i in range(low_count))
    high=((fraction >> (8*low_count)) & 0x7F) | (0x80 if sign else 0)
    return low + bytes((high, exponent))

def _format_number(value: float) -> str:
    if math.isfinite(value) and value == int(value):
        return str(int(value))
    return format(value, '.15g')


def detokenize_body(data: bytes) -> str:
    out: list[str] = []
    i = 0
    while i < len(data):
        b = data[i]
        if b == 0:
            break
        # Numeric constants and line references.
        if b == 0x0E and i + 2 < len(data):
            out.append(str(int.from_bytes(data[i+1:i+3], 'little'))); i += 3; continue
        if b == 0x0B and i + 2 < len(data):
            out.append('&O' + format(int.from_bytes(data[i+1:i+3], 'little'), 'o')); i += 3; continue
        if b == 0x0C and i + 2 < len(data):
            out.append('&H' + format(int.from_bytes(data[i+1:i+3], 'little'), 'X')); i += 3; continue
        if 0x11 <= b <= 0x1B:
            out.append(str(b - 0x11)); i += 1; continue
        if b == 0x0F and i + 1 < len(data):
            out.append(str(data[i+1])); i += 2; continue
        if b == 0x1C and i + 2 < len(data):
            out.append(str(int.from_bytes(data[i+1:i+3], 'little', signed=True))); i += 3; continue
        if b == 0x1D and i + 4 < len(data):
            out.append(_format_number(mbf_to_float(data[i+1:i+5]))); i += 5; continue
        if b == 0x1F and i + 8 < len(data):
            out.append(_format_number(mbf_to_float(data[i+1:i+9]))); i += 9; continue

        if b in (0xFD, 0xFE, 0xFF) and i + 1 < len(data):
            token = data[i:i+2]
            if token in TOKEN_TO_KEYWORD:
                out.append(TOKEN_TO_KEYWORD[token]); i += 2; continue
        token = bytes([b])
        if token in TOKEN_TO_KEYWORD:
            word = TOKEN_TO_KEYWORD[token]
            out.append(word); i += 1
            # REM consumes the rest as literal source; no token interpretation.
            if word == 'REM':
                out.append(data[i:].decode('cp437', errors='replace'))
                break
            if word == "'":
                out.append(data[i:].decode('cp437', errors='replace'))
                break
            continue
        # Printable and code-page bytes survive verbatim.
        out.append(bytes([b]).decode('cp437', errors='replace'))
        i += 1
    return ''.join(out)


def _line_body_end(payload: bytes, pos: int) -> int:
    """Locate the NUL line terminator without mistaking binary numeric bytes for it."""
    i=pos; in_string=False
    numeric_lengths={0x0E:3,0x0B:3,0x0C:3,0x0F:2,0x1C:3,0x1D:5,0x1F:9}
    while i < len(payload):
        b=payload[i]
        if in_string:
            if b == 0x22: in_string=False
            i += 1; continue
        if b == 0x22:
            in_string=True; i += 1; continue
        if b == 0x00:
            return i
        if b in numeric_lengths:
            i += numeric_lengths[b]; continue
        if b in (0xFD,0xFE,0xFF) and i+1 < len(payload):
            i += 2; continue
        # REM and apostrophe make the remainder literal until the line terminator.
        if b in (0x8F,0xD9):
            try: return payload.index(0,i+1)
            except ValueError: return len(payload)
        i += 1
    return len(payload)


def detokenize_program(payload: bytes) -> dict[int, str]:
    """Convert a genuine tokenised GW-BASIC payload into numbered source lines.

    The cassette header already carries the file type, so cassette payloads normally
    do not need the disk magic FF byte.  We tolerate it for interchange convenience.
    """
    if payload[:1] == b'\xFF':
        payload = payload[1:]
    pos = 0
    program: dict[int, str] = {}
    while pos + 4 <= len(payload):
        next_ptr = int.from_bytes(payload[pos:pos+2], 'little')
        line_no = int.from_bytes(payload[pos+2:pos+4], 'little')
        pos += 4
        end = _line_body_end(payload, pos)
        body = payload[pos:end]
        # A naked terminator at EOF is not a program line.
        if line_no == 0 and not body and next_ptr == 0:
            break
        program[line_no] = detokenize_body(body)
        pos = end + 1
        if next_ptr == 0:
            break
    return program


def _word_boundary(source: str, start: int, word: str) -> bool:
    if not word or not (word[0].isalnum() or word[0] == '_'):
        return True
    before = source[start-1] if start else ''
    after_i = start + len(word)
    after = source[after_i] if after_i < len(source) else ''
    # BASIC permits punctuation suffixes but variable names may contain letters/digits.
    if before and (before.isalnum() or before in '_.$%!#&'):
        return False
    # TAB( and SPC( include their opening parenthesis in the token itself, so an
    # immediately following numeric argument is not a word-boundary violation.
    if not word.endswith('(') and after and (after.isalnum() or after == '_'):
        return False
    return True


def tokenize_body(source: str) -> bytes:
    """Tokenise source using the documented GW-BASIC program representation.

    Besides keywords this emits line-reference tokens, compact integers, octal
    and hexadecimal constants, and MBF single/double constants. This matters for
    cassette interoperability: an original BASIC sees the token stream after the
    BIOS has decoded the tape, so the payload must be historically meaningful too.
    """
    out=bytearray(); i=0; upper=source.upper()
    line_ref_mode=False
    line_ref_once=False
    while i < len(source):
        ch=source[i]
        if ch == '"':
            j=i+1
            while j < len(source):
                if source[j] == '"':
                    j += 1
                    if j < len(source) and source[j] == '"': j += 1; continue
                    break
                j += 1
            out.extend(source[i:j].encode('cp437',errors='replace')); i=j; continue
        if ch == "'":
            out.extend(KEYWORD_TO_TOKEN["'"]); out.extend(source[i+1:].encode('cp437',errors='replace')); break

        # &Hxxxx and &Oxxxx use dedicated numeric tokens.
        mbase=re.match(r'&([HhOo])([0-9A-Fa-f]+)',source[i:])
        if mbase:
            base=16 if mbase.group(1).upper()=='H' else 8
            try: value=int(mbase.group(2),base)
            except ValueError: value=-1
            if 0 <= value <= 0xFFFF:
                out.append(0x0C if base==16 else 0x0B); out.extend(value.to_bytes(2,'little'))
                i += len(mbase.group(0)); line_ref_once=False; continue

        matched=None
        for word in _KEYWORDS:
            if upper.startswith(word,i) and _word_boundary(source,i,word): matched=word; break
        if matched:
            out.extend(KEYWORD_TO_TOKEN[matched]); i += len(matched)
            if matched == 'REM': out.extend(source[i:].encode('cp437',errors='replace')); break
            # These statements syntactically consume line numbers. GOTO/GOSUB keep
            # the mode across comma-separated ON ... GOTO/GOSUB target lists.
            if matched in ('GOTO','GOSUB'):
                line_ref_mode=True; line_ref_once=False
            elif matched in ('THEN','ELSE','RESTORE','RESUME','RUN'):
                line_ref_once=True
            elif matched not in ('TO',):
                # Any real statement/function token ends a stale one-shot context.
                if matched not in ('GOTO','GOSUB'): line_ref_mode=False
            continue

        # A colon starts another statement and terminates GOTO target-list context.
        if ch == ':':
            line_ref_mode=False; line_ref_once=False
            out.append(ord(ch)); i += 1; continue

        # Numeric literal. Leading sign remains a separate +/- token, like GW-BASIC.
        mnum=re.match(r'(?:(?:\d+\.\d*|\.\d+|\d+)(?:[EeDd][+-]?\d+)?|\d+)([%!#]?)',source[i:])
        if mnum:
            literal=mnum.group(0); suffix=mnum.group(1)
            core=literal[:-1] if suffix else literal
            # Avoid stealing digits from variable identifiers such as A1.
            prev=source[i-1:i]; following=source[i+len(literal):i+len(literal)+1]
            if not (prev and (prev.isalnum() or prev in '.$')) and not (following and following.isalpha()):
                if (line_ref_mode or line_ref_once) and re.fullmatch(r'\d+',core):
                    value=int(core)
                    if 0 <= value <= 0xFFFF:
                        out.append(0x0E); out.extend(value.to_bytes(2,'little')); i += len(literal)
                        line_ref_once=False
                        # ON ... GOTO/GOSUB lists remain active while comma follows.
                        if line_ref_mode:
                            tail=source[i:].lstrip()
                            if not tail.startswith(','): line_ref_mode=False
                        continue
                is_float=any(c in core for c in '.EeDd') or suffix in ('!','#')
                if not is_float:
                    value=int(core)
                    if value <= 10:
                        out.append(0x11+value); i += len(literal); line_ref_once=False; continue
                    if value <= 255:
                        out.extend((0x0F,value)); i += len(literal); line_ref_once=False; continue
                    if value <= 32767:
                        out.append(0x1C); out.extend(value.to_bytes(2,'little',signed=True)); i += len(literal); line_ref_once=False; continue
                    is_float=True
                if is_float:
                    double=(suffix=='#' or 'D' in core.upper())
                    number=float(re.sub('[Dd]','E',core))
                    out.append(0x1F if double else 0x1D)
                    out.extend(float_to_mbf(number,double=double)); i += len(literal); line_ref_once=False; continue

        # Comma preserves a GOTO/GOSUB target-list context; ordinary text clears
        # one-shot line-number expectation once a non-space character is seen.
        if ch not in ' \t,' and line_ref_once: line_ref_once=False
        out.extend(ch.encode('cp437',errors='replace')); i += 1
    return bytes(out)


def tokenize_program(program: Mapping[int, str], base_address: int = 0x1000) -> bytes:
    """Build the packed in-memory/disk program-line representation.

    The link field is an 8086 offset to the next line. The loader in DSKCOM.ASM calls
    LINKER after reading a binary program, so these links are rebuilt on load; still,
    we emit plausible offsets for compatibility with tools that inspect them.
    """
    records: list[bytearray] = []
    line_numbers = sorted(int(n) for n in program)
    for n in line_numbers:
        body = tokenize_body(program[n])
        rec = bytearray(b'\x00\x00')
        rec.extend(int(n).to_bytes(2, 'little'))
        rec.extend(body)
        rec.append(0)
        records.append(rec)
    offset = 0
    for idx, rec in enumerate(records):
        if idx + 1 < len(records):
            next_addr = (base_address + offset + len(rec)) & 0xFFFF
        else:
            next_addr = 0
        rec[0:2] = next_addr.to_bytes(2, 'little')
        offset += len(rec)
    return b''.join(records) + b'\x1A'


def ascii_program_bytes(program: Mapping[int, str]) -> bytes:
    text = ''.join(f'{n} {program[n]}\r\n' for n in sorted(program))
    return text.encode('cp437', errors='replace') + b'\x1A'


def parse_ascii_program(payload: bytes) -> dict[int, str]:
    payload = payload.split(b'\x1A', 1)[0]
    text = payload.decode('cp437', errors='replace').replace('\r\n', '\n').replace('\r', '\n')
    program: dict[int, str] = {}
    for line in text.split('\n'):
        m = re.match(r'^\s*(\d+)\s?(.*)$', line)
        if m:
            program[int(m.group(1))] = m.group(2)
    return program


_KEY11 = bytes.fromhex('1E 1D C4 77 26 97 E0 74 59 88 7C')
_KEY13 = bytes.fromhex('A9 84 8D CD 75 83 43 63 24 83 19 F7 9A')
_SEQ11 = bytes(range(11, 0, -1))
_SEQ13 = bytes(range(13, 0, -1))


def protect_payload(payload: bytes) -> bytes:
    """GW-BASIC protected-file transform, equivalent to GIODSK.ASM PENCOD."""
    out = bytearray()
    for i, b in enumerate(payload):
        x = (b - _SEQ11[i % 11]) & 0xFF
        x ^= _KEY11[i % 11]
        x ^= _KEY13[i % 13]
        x = (x + _SEQ13[i % 13]) & 0xFF
        out.append(x)
    return bytes(out)


def unprotect_payload(payload: bytes) -> bytes:
    out = bytearray()
    for i, b in enumerate(payload):
        x = (b - _SEQ13[i % 13]) & 0xFF
        x ^= _KEY13[i % 13]
        x ^= _KEY11[i % 11]
        x = (x + _SEQ11[i % 11]) & 0xFF
        out.append(x)
    return bytes(out)
