"""IBM PC 5150 cassette audio codec for the GW-BASIC/BASICA family.

Historical mapping
------------------
The supplied GIOCAS.ASM is only a machine-independent stub whose MOTOR entry
raises Device unavailable. On an original IBM PC, the physical modulation was
implemented by BIOS INT 15h cassette services. This module ports that external
hardware contract, not instructions absent from GIOCAS.ASM.

IBM PC tape signal:
* bit 1: PIT count 1184, nominal 1 ms / about 1000 Hz
* bit 0: PIT count 592, nominal 0.5 ms / about 2000 Hz
* 256 bytes of FF leader, sync bit 0, sync byte 16h
* 256-byte physical blocks, each followed by complemented CRC-16/CCITT
* four FF trailer bytes

WAV is the archival/native representation. MP3 is supported through ffmpeg as a
convenience transport, but because MP3 is lossy it cannot be guaranteed to retain
all edge timing of marginal historical recordings.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import os
import shutil
import struct
import subprocess
import tempfile
import wave
from typing import Iterable

PIT_HZ = 1_193_182.0
ONE_COUNT = 1184.0
ZERO_COUNT = 592.0
SAMPLE_RATE = 48_000
AMPLITUDE = 20_000
SYNC_BYTE = 0x16
HEADER_MAGIC = 0xA5
CRC_GOOD_REMAINDER = 0x1D0F

TYPE_DATA = 0x00
TYPE_MEMORY = 0x01
TYPE_PROTECTED = 0xA0
TYPE_ASCII = 0x40
TYPE_TOKENISED = 0x80
PROGRAM_TYPES = {TYPE_ASCII, TYPE_TOKENISED, 0x20, TYPE_PROTECTED}


class CassetteError(Exception):
    pass


@dataclass
class TapeFile:
    name: str
    file_type: int
    payload: bytes
    segment: int = 0
    offset: int = 0
    crc_ok: bool = True

    @property
    def type_letter(self) -> str:
        return {
            TYPE_DATA: 'D', TYPE_MEMORY: 'M', TYPE_ASCII: 'A',
            TYPE_TOKENISED: 'B', 0x20: 'P', TYPE_PROTECTED: 'P',
        }.get(self.file_type, '?')


def crc_register(data: bytes, init: int = 0xFFFF) -> int:
    """Exact bit-order used by the IBM 5150 BIOS CRC_GEN routine."""
    crc = init & 0xFFFF
    for byte in data:
        for shift in range(7, -1, -1):
            bit = (byte >> shift) & 1
            xor = ((crc >> 15) & 1) ^ bit
            crc = (crc << 1) & 0xFFFF
            if xor:
                crc ^= 0x1021
    return crc


def crc_bytes(data: bytes) -> bytes:
    """BIOS writes one's complement of CRC, most-significant byte first."""
    value = (~crc_register(data)) & 0xFFFF
    return value.to_bytes(2, 'big')


def crc_valid(block: bytes, crc: bytes) -> bool:
    return len(crc) == 2 and crc_register(block + crc) == CRC_GOOD_REMAINDER


def _byte_bits(value: int) -> list[int]:
    return [(value >> bit) & 1 for bit in range(7, -1, -1)]


def _bytes_bits(data: bytes) -> list[int]:
    out: list[int] = []
    for value in data:
        out.extend(_byte_bits(value))
    return out


def make_data_blocks(payload: bytes) -> list[bytes]:
    """Build 256-byte BASIC cassette blocks: length byte + 255 payload bytes."""
    if not payload:
        return [bytes([1]) + bytes(255)]
    blocks: list[bytes] = []
    for start in range(0, len(payload), 255):
        chunk = payload[start:start+255]
        last = start + len(chunk) >= len(payload)
        # A full final 255-byte chunk cannot encode 256 in one byte. Header length
        # resolves this for binary files; for sequential files add an empty terminator.
        count = (len(chunk) + 1) if last and len(chunk) < 255 else 0
        fill = chunk[-1:] if chunk else b'\x00'
        padded = chunk + fill * (255 - len(chunk))
        blocks.append(bytes([count & 0xFF]) + padded)
    if len(payload) % 255 == 0:
        blocks.append(bytes([1]) + bytes(255))
    return blocks


def make_header(file: TapeFile) -> bytes:
    raw_name = file.name.encode('cp437', errors='replace')[:8].ljust(8, b' ')
    header = bytearray()
    header.append(HEADER_MAGIC)
    header.extend(raw_name)
    header.append(file.file_type & 0xFF)
    header.extend((len(file.payload) & 0xFFFF).to_bytes(2, 'little'))
    header.extend((file.segment & 0xFFFF).to_bytes(2, 'little'))
    header.extend((file.offset & 0xFFFF).to_bytes(2, 'little'))
    header.append(0)
    header.extend(b'\x01' * 239)
    assert len(header) == 256
    return bytes(header)


def parse_header(block: bytes) -> tuple[str, int, int, int, int]:
    if len(block) != 256 or block[0] != HEADER_MAGIC:
        raise CassetteError('Invalid cassette header')
    name = block[1:9].decode('cp437', errors='replace').rstrip(' ')
    file_type = block[9]
    length = int.from_bytes(block[10:12], 'little')
    segment = int.from_bytes(block[12:14], 'little')
    offset = int.from_bytes(block[14:16], 'little')
    return name, file_type, length, segment, offset


def _record_bits(blocks: Iterable[bytes]) -> list[int]:
    bits = _bytes_bits(b'\xFF' * 256)
    bits.append(0)
    bits.extend(_byte_bits(SYNC_BYTE))
    for block in blocks:
        if len(block) != 256:
            raise ValueError('physical cassette block must be 256 bytes')
        bits.extend(_bytes_bits(block))
        bits.extend(_bytes_bits(crc_bytes(block)))
    bits.extend(_bytes_bits(b'\xFF' * 4))
    return bits


def file_to_bits(file: TapeFile) -> list[int]:
    """Encode one logical BASIC cassette file, header record plus data record(s)."""
    bits = _record_bits([make_header(file)])
    data_blocks = make_data_blocks(file.payload)
    if file.file_type in (TYPE_ASCII, TYPE_DATA):
        # Sequential files use one physical block per record.
        for block in data_blocks:
            bits.extend(_record_bits([block]))
    else:
        # Tokenised, protected and BSAVE files use one multi-block record.
        bits.extend(_record_bits(data_blocks))
    return bits


def bits_to_pcm(bits: Iterable[int], sample_rate: int = SAMPLE_RATE) -> bytes:
    """Render IBM timer periods as 16-bit mono PCM square waves."""
    samples = bytearray()
    # Keep a fractional sample clock instead of rounding every bit independently.
    # This preserves the average period of the actual IBM PIT counts 1184/592 at
    # arbitrary PCM sample rates, avoiding long-record timing drift.
    exact_cursor = 0.0
    emitted = 0
    for bit in bits:
        period = (ONE_COUNT if bit else ZERO_COUNT) / PIT_HZ
        exact_cursor += period * sample_rate
        target = int(round(exact_cursor))
        n = max(8, target - emitted)
        emitted += n
        # One complete square-wave period per bit. Ending phase equals starting phase.
        half = n / 2.0
        for j in range(n):
            value = AMPLITUDE if j < half else -AMPLITUDE
            samples.extend(struct.pack('<h', value))
    return bytes(samples)


def write_wav(path: Path, bits: Iterable[int], sample_rate: int = SAMPLE_RATE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(bits_to_pcm(bits, sample_rate))


def _ffmpeg() -> str:
    exe = shutil.which('ffmpeg')
    if not exe:
        raise CassetteError('MP3 requires ffmpeg; use WAV for lossless cassette interchange')
    return exe


def write_audio(path: Path, files: Iterable[TapeFile]) -> None:
    bits: list[int] = []
    first = True
    for file in files:
        if not first:
            # A short run of 1-bits behaves like leader/gap and keeps edge timing valid.
            bits.extend([1] * 256)
        bits.extend(file_to_bits(file)); first = False
    suffix = path.suffix.lower()
    if suffix in ('', '.wav'):
        if not suffix:
            path = path.with_suffix('.wav')
        write_wav(path, bits)
        return
    if suffix == '.mp3':
        with tempfile.TemporaryDirectory() as td:
            wav_path = Path(td) / 'cassette.wav'
            write_wav(wav_path, bits)
            proc = subprocess.run([
                _ffmpeg(), '-y', '-loglevel', 'error', '-i', str(wav_path),
                '-codec:a', 'libmp3lame', '-b:a', '320k', str(path)
            ], capture_output=True, text=True)
            if proc.returncode:
                raise CassetteError(proc.stderr.strip() or 'ffmpeg MP3 conversion failed')
        return
    raise CassetteError('Cassette image must be .wav or .mp3')


def _read_pcm_wav(path: Path) -> tuple[int, list[float]]:
    try:
        with wave.open(str(path), 'rb') as wav:
            channels = wav.getnchannels(); width = wav.getsampwidth(); rate = wav.getframerate()
            frames = wav.readframes(wav.getnframes())
    except wave.Error as exc:
        raise CassetteError(f'Unsupported WAV: {exc}') from exc
    if width not in (1, 2, 3, 4):
        raise CassetteError('Unsupported WAV sample width')
    frame_size = width * channels
    samples: list[float] = []
    maxv = float(1 << (width * 8 - 1))
    for pos in range(0, len(frames) - frame_size + 1, frame_size):
        acc = 0.0
        for ch in range(channels):
            raw = frames[pos + ch*width:pos + (ch+1)*width]
            if width == 1:
                value = raw[0] - 128
                scale = 128.0
            else:
                value = int.from_bytes(raw, 'little', signed=True)
                scale = maxv
            acc += value / scale
        samples.append(acc / channels)
    if not samples:
        raise CassetteError('Empty audio file')
    # Remove DC bias found in analog captures.
    mean = sum(samples) / len(samples)
    samples = [x - mean for x in samples]
    return rate, samples


def read_audio_samples(path: Path) -> tuple[int, list[float]]:
    if path.suffix.lower() == '.wav':
        return _read_pcm_wav(path)
    if path.suffix.lower() == '.mp3':
        with tempfile.TemporaryDirectory() as td:
            wav_path = Path(td) / 'decoded.wav'
            proc = subprocess.run([
                _ffmpeg(), '-y', '-loglevel', 'error', '-i', str(path),
                '-ac', '1', '-ar', str(SAMPLE_RATE), '-c:a', 'pcm_s16le', str(wav_path)
            ], capture_output=True, text=True)
            if proc.returncode:
                raise CassetteError(proc.stderr.strip() or 'ffmpeg MP3 decode failed')
            return _read_pcm_wav(wav_path)
    raise CassetteError('Cassette image must be .wav or .mp3')


def samples_to_bits(rate: int, samples: list[float]) -> list[int | None]:
    """Recover bit periods using hysteretic rising-edge detection.

    This intentionally measures timing rather than waveform amplitude so recordings
    from real cassette decks can tolerate gain variation and DC offset.
    """
    peak = max(abs(x) for x in samples)
    if peak < 0.01:
        raise CassetteError('No cassette signal detected')
    hi = peak * 0.12; lo = -hi
    state = 1 if samples[0] > hi else -1 if samples[0] < lo else 0
    rising: list[int] = []
    for idx, value in enumerate(samples[1:], 1):
        if state <= 0 and value >= hi:
            rising.append(idx); state = 1
        elif state >= 0 and value <= lo:
            state = -1
    if len(rising) < 100:
        raise CassetteError('Too few signal transitions')
    one_n = rate * ONE_COUNT / PIT_HZ
    zero_n = rate * ZERO_COUNT / PIT_HZ
    threshold = (one_n + zero_n) / 2.0
    bits: list[int | None] = []
    for a, b in zip(rising, rising[1:]):
        d = b - a
        if d < zero_n * 0.55 or d > one_n * 1.65:
            bits.append(None)
        else:
            bits.append(1 if d > threshold else 0)
    return bits


def _bits_byte(bits: list[int | None], pos: int) -> int | None:
    if pos + 8 > len(bits): return None
    value = 0
    for bit in bits[pos:pos+8]:
        if bit not in (0, 1): return None
        value = (value << 1) | int(bit)
    return value


def find_record_starts(bits: list[int | None], min_leader_bits: int = 128) -> list[int]:
    """Return bit positions immediately after the sync byte for every tape record."""
    starts: list[int] = []
    run = 0
    i = 0
    while i < len(bits) - 10:
        bit = bits[i]
        if bit == 1:
            run += 1; i += 1; continue
        if bit == 0 and run >= min_leader_bits:
            syn = _bits_byte(bits, i + 1)
            if syn == SYNC_BYTE:
                starts.append(i + 9)
                i += 9; run = 0; continue
        run = 0
        i += 1
    return starts


def _read_physical_block(bits: list[int | None], pos: int) -> tuple[bytes, bool, int]:
    data = bytearray()
    for _ in range(256):
        value = _bits_byte(bits, pos)
        if value is None:
            raise CassetteError('Damaged or incomplete cassette data block')
        data.append(value); pos += 8
    crc_hi = _bits_byte(bits, pos); pos += 8
    crc_lo = _bits_byte(bits, pos); pos += 8
    if crc_hi is None or crc_lo is None:
        raise CassetteError('Damaged cassette CRC')
    crc = bytes((crc_hi, crc_lo))
    return bytes(data), crc_valid(bytes(data), crc), pos


def scan_audio(path: Path) -> list[TapeFile]:
    rate, samples = read_audio_samples(path)
    bits = samples_to_bits(rate, samples)
    starts = find_record_starts(bits)
    if not starts:
        raise CassetteError('No IBM PC cassette leader/sync record found')
    files: list[TapeFile] = []
    r = 0
    while r < len(starts):
        try:
            header_block, header_crc, _ = _read_physical_block(bits, starts[r])
            if header_block[0] != HEADER_MAGIC:
                r += 1; continue
            name, file_type, length, segment, offset = parse_header(header_block)
            overall_crc = header_crc
            r += 1
            if r >= len(starts):
                break
            payload = bytearray()
            if file_type in (TYPE_ASCII, TYPE_DATA):
                while r < len(starts):
                    block, ok, _ = _read_physical_block(bits, starts[r]); overall_crc &= ok
                    count = block[0]
                    if count:
                        payload.extend(block[1:1 + max(0, count - 1)])
                        r += 1
                        break
                    payload.extend(block[1:])
                    r += 1
            else:
                # Binary record starts once and may hold several 256+CRC blocks.
                pos = starts[r]
                block_count = max(1, math.ceil(length / 255))
                # Encoder may add an empty terminator for exact multiples of 255;
                # historical binary loaders already know length, so don't require it.
                for _ in range(block_count):
                    block, ok, pos = _read_physical_block(bits, pos); overall_crc &= ok
                    count = block[0]
                    take = max(0, count - 1) if count else 255
                    payload.extend(block[1:1+take])
                r += 1
                payload = payload[:length]
            files.append(TapeFile(name, file_type, bytes(payload[:length] if length else payload), segment, offset, overall_crc))
        except CassetteError:
            r += 1
    if not files:
        raise CassetteError('Cassette records found, but no valid BASIC file header')
    return files


def append_file(path: Path, file: TapeFile) -> None:
    """Append logically to a tape image by decoding existing BASIC files and re-rendering.

    This preserves the digital IBM cassette records. For archival analog captures, keep an
    untouched master and save new data to another image.
    """
    files: list[TapeFile] = []
    if path.exists() and path.stat().st_size:
        try:
            files = scan_audio(path)
        except CassetteError:
            # Do not silently destroy an unreadable historical recording.
            raise CassetteError('Mounted cassette cannot be decoded; refusing to overwrite it')
    files.append(file)
    write_audio(path, files)


def find_file(path: Path, name: str, allowed_types: set[int]) -> TapeFile:
    wanted = name[:8]
    for file in scan_audio(path):
        if file.file_type not in allowed_types:
            continue
        if not wanted or file.name == wanted:
            return file
    raise CassetteError('File not found on cassette')
