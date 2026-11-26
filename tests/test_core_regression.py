import tempfile,unittest
from pathlib import Path
import core_regression as c
from runtime import read_json
from historical_eval import digest
from proof_audit import audit

class CoreRegressionTests(unittest.TestCase):
    def test_full_exact_engine_controls(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'controls'
            r=c.run(output=out)
            failures=[(x['id'],x['actual'],x['error']) for x in r['cases'] if not x['passed']]
            self.assertEqual(failures,[])
            self.assertEqual(r['model_calls'],0)
            self.assertEqual(r['total'],22)
            for x in r['cases']:
                g=read_json(out/(x['id']+'.json'),limit=32*1024*1024)
                self.assertEqual(digest(g),x['state_sha256'])
                self.assertEqual(audit(g)['status'],x['expected'])
