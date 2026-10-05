from __future__ import annotations
import tempfile
import unittest
from pathlib import Path

from app.services.interpreter import GWBasicInterpreter


class InterpreterTests(unittest.TestCase):
    def make(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        return GWBasicInterpreter(self.tmp.name)

    def load(self, engine, lines):
        for line in lines:
            self.assertEqual(engine.submit(line)['status'], 'ok')

    def test_for_next(self):
        b=self.make()
        self.load(b,['10 S=0','20 FOR I=1 TO 5','30 S=S+I','40 NEXT I','50 PRINT S'])
        r=b.submit('RUN')
        self.assertEqual(r['status'],'ended')
        self.assertEqual(r['output'],'15\n')

    def test_if_gosub_return(self):
        b=self.make()
        self.load(b,['10 A=2','20 IF A=2 THEN GOSUB 100 ELSE PRINT "BAD"','30 PRINT "OK"','40 END','100 PRINT "SUB"','110 RETURN'])
        r=b.submit('RUN')
        self.assertEqual(r['status'],'stopped')
        self.assertEqual(r['output'],'SUB\nOK\n')

    def test_data_read_array(self):
        b=self.make()
        self.load(b,['10 DATA 2,3','20 READ A,B','30 DIM M(2,3)','40 M(A,B)=A^B','50 PRINT M(2,3)'])
        r=b.submit('RUN')
        self.assertEqual(r['output'],'8\n')

    def test_input_continuation(self):
        b=self.make()
        self.load(b,['10 INPUT "NOME";N$','20 PRINT "OLA ";N$'])
        r=b.submit('RUN')
        self.assertEqual(r['status'],'waiting_input')
        r=b.submit('ZARONI')
        self.assertEqual(r['status'],'ended')
        self.assertEqual(r['output'],'OLA ZARONI\n')

    def test_file_round_trip(self):
        b=self.make()
        b.submit('OPEN "A.TXT" FOR OUTPUT AS #1')
        b.submit('PRINT #1, "ABC"')
        b.submit('CLOSE #1')
        b.submit('OPEN "A.TXT" FOR INPUT AS #1')
        b.submit('LINE INPUT #1, A$')
        self.assertEqual(b.state.get_var('A$'),'ABC')
        b.submit('CLOSE #1')

    def test_path_traversal_is_rejected(self):
        b=self.make()
        r=b.submit('OPEN "../x.txt" FOR OUTPUT AS #1')
        self.assertEqual(r['status'],'error')

    def test_print_using(self):
        b=self.make()
        r=b.submit('PRINT USING "###.##"; 12.3')
        self.assertEqual(r['output'],' 12.30\n')


if __name__=='__main__':
    unittest.main()
