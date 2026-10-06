from __future__ import annotations
import shutil
import tempfile
import unittest
from pathlib import Path

from app.services.interpreter import GWBasicInterpreter
from app.services import cassette, legacy_basic


class CassetteCompatibilityTests(unittest.TestCase):
    def make(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        return GWBasicInterpreter(self.tmp.name)

    def test_ibm_crc_residue(self):
        block=bytes((i & 0xFF for i in range(256)))
        crc=cassette.crc_bytes(block)
        self.assertTrue(cassette.crc_valid(block,crc))
        self.assertEqual(cassette.crc_register(block+crc),cassette.CRC_GOOD_REMAINDER)

    def test_tokenized_program_codec(self):
        program={10:'IF X=1.25 THEN 100 ELSE 200',20:'ON X GOTO 100,200',100:'PRINT TAB(5);&HFF',200:'END'}
        payload=legacy_basic.tokenize_program(program)
        decoded=legacy_basic.detokenize_program(payload)
        self.assertEqual(decoded,program)
        # 0E is the indirect line-number token; 1D is MBF single precision.
        self.assertIn(b'\x0e\x64\x00',payload)
        self.assertIn(b'\x1d'+legacy_basic.float_to_mbf(1.25),payload)

    def test_protected_program_codec(self):
        program={10:'PRINT "SECRET"',20:'END'}
        payload=legacy_basic.tokenize_program(program)
        encrypted=legacy_basic.protect_payload(payload)
        self.assertNotEqual(encrypted,payload)
        self.assertEqual(legacy_basic.unprotect_payload(encrypted),payload)

    def test_save_load_wav_cassette(self):
        b=self.make()
        for line in ['10 FOR I=1 TO 3','20 PRINT I','30 NEXT I']:
            self.assertEqual(b.submit(line)['status'],'ok')
        self.assertEqual(b.submit('SAVE "CAS1:TEST"')['status'],'ok')
        wav=Path(self.tmp.name)/'cassette.wav'
        files=cassette.scan_audio(wav)
        self.assertEqual(files[0].name,'TEST')
        self.assertEqual(files[0].file_type,cassette.TYPE_TOKENISED)
        self.assertTrue(files[0].crc_ok)
        b.submit('NEW')
        self.assertEqual(b.submit('LOAD "CAS1:TEST"')['status'],'ok')
        self.assertEqual(b.submit('RUN')['output'],'1\n2\n3\n')

    def test_bsave_bload_preserves_segment_offset(self):
        b=self.make(); b.submit('DEF SEG=&H1234')
        expected=[0x10,0x20,0x30,0xFE]
        for i,value in enumerate(expected): b.submit(f'POKE {200+i},{value}')
        self.assertEqual(b.submit('BSAVE "CAS1:MEM",200,4')['status'],'ok')
        b.state.memory.clear(); b.submit('DEF SEG=&H7777')
        self.assertEqual(b.submit('BLOAD "CAS1:MEM"')['status'],'ok')
        actual=[b.state.memory.get(b.state.linear_address(200+i,0x1234)) for i in range(4)]
        self.assertEqual(actual,expected)

    @unittest.skipUnless(shutil.which('ffmpeg'),'ffmpeg not installed')
    def test_mp3_round_trip(self):
        path=Path(self.tmpdir())/'tape.mp3'
        tf=cassette.TapeFile('HELLO',cassette.TYPE_ASCII,b'10 PRINT "X"\r\n\x1A')
        cassette.write_audio(path,[tf])
        got=cassette.scan_audio(path)[0]
        self.assertEqual((got.name,got.file_type,got.payload),(tf.name,tf.file_type,tf.payload))
        self.assertTrue(got.crc_ok)

    @unittest.skipUnless(shutil.which('ffmpeg'),'ffmpeg not installed')
    def test_wav_decoder_tolerates_tape_speed_drift(self):
        root=Path(self.tmpdir()); original=root/'original.wav'
        tf=cassette.TapeFile('OLDTAPE',cassette.TYPE_ASCII,b'10 PRINT "OLD"\r\n\x1A')
        cassette.write_audio(original,[tf])
        for factor in (0.90,1.10):
            shifted=root/f'drift-{factor}.wav'
            import subprocess
            subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(original),
                            '-af',f'asetrate=48000*{factor},aresample=48000',str(shifted)],check=True)
            got=cassette.scan_audio(shifted)[0]
            self.assertEqual(got.payload,tf.payload); self.assertTrue(got.crc_ok)

    def tmpdir(self):
        td=tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup); return td.name


if __name__=='__main__':
    unittest.main()
