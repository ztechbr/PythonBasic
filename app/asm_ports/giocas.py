"""Academic port notes for GIOCAS.ASM and the external IBM cassette BIOS contract.

Original title: GIOCAS - Cassette Machine Independent Device Driver Code

Important historical distinction
---------------------------------
The supplied GIOCAS.ASM does not contain the physical cassette encoder/decoder.
Its only PUBLIC entry is MOTOR and this build routes it to Device unavailable.
On an original IBM PC 5150, BASIC delegated the actual tape signal to BIOS
cassette services. Therefore ``app.services.cassette`` ports the *external BIOS
contract* needed to make LOAD/SAVE/BLOAD/BSAVE historically interoperable.

Python mapping
--------------
* GIOCAS.ASM MOTOR hook -> mounted CAS1: audio resource in the Flask session.
* IBM BIOS timer output -> WAV/MP3 FSK waveform generated from PIT counts.
* BIOS record framing/CRC -> ``app.services.cassette``.
* BASIC cassette headers -> TapeFile header encoder/decoder.
* GIO86/DSKCOM BLOAD/BSAVE -> explicit 20-bit segment:offset RuntimeState memory.

The original source remains under ``reference/asm/GIOCAS.ASM`` so the absence of
physical driver code can be verified side by side.
"""

ORIGINAL_FILE = 'GIOCAS.ASM'
ORIGINAL_TITLE = 'GIOCAS - Cassette Machine Independent Device Driver Code'
PUBLIC_ROUTINES = ['MOTOR']
SUBSECTIONS = []
PORT_NOTE = ('GIOCAS itself is a Device-unavailable stub in this source set. '
             'CAS1 audio compatibility is implemented from the IBM PC BIOS '
             'cassette contract in app/services/cassette.py.')
