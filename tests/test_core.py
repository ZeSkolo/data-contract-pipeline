import unittest, tempfile
from pathlib import Path
from core import run, validate

class Tests(unittest.TestCase):

    def p(self):
        return {'csv': 'id,value\na,2\nb,-1\na,3\n', 'contract': {'id': {'type': 'str', 'unique': True}, 'value': {'type': 'int', 'min': 0}}}

    def test_quarantine(self):
        r = run(self.p())
        self.assertEqual((r['accepted'], r['rejected']), (1, 2))

    def test_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            db = str(Path(d) / 'x')
            run(self.p(), db)
            r = run(self.p(), db)
            self.assertTrue(r['already_ingested'])
            self.assertEqual(r['stored_rows'], 1)

    def test_schema(self):
        p = self.p()
        p['csv'] = 'unknown\nx\n'
        with self.assertRaises(ValueError):
            run(p)

    def test_nonfinite(self):
        self.assertEqual(len(validate('x\nnan\n', {'x': {'type': 'float'}})[1]), 1)

    def test_bad_names(self):
        with self.assertRaises(ValueError):
            validate('x\n1\n', {'x;DROP': {'type': 'int'}})
