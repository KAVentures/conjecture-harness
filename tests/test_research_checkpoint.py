import json,sys,tempfile,unittest,subprocess
from pathlib import Path
from research_checkpoint import initialize,report,typed
from discovery import new,apply,closure
from discovery_tools import run
from runtime import read_json

class CheckpointTests(unittest.TestCase):
    def test_typed_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            s=Path(d)/'state.json';g=initialize(s,'polynomial',dict(variables=['x'],domain='real',relation='nonnegative',terms=[[[2],1]]));self.assertEqual(report(g)['status'],'open');run(s);r=report(read_json(s));self.assertEqual(r['status'],'established');self.assertEqual(r['attempts'],0);self.assertEqual(r['target_sha256'],g['target_sha256']);self.assertIn('not independent',r['trust'])
    def test_refutation(self):
        with tempfile.TemporaryDirectory() as d:
            s=Path(d)/'state.json';initialize(s,'polynomial',dict(variables=['x'],domain='real',relation='nonnegative',terms=[[[0],-1]]));run(s);r=report(read_json(s));self.assertEqual(r['status'],'refuted');self.assertEqual(r['refuted'],['goal'])
    def test_prose_not_proof(self):
        r=report(new('An open conjecture'));self.assertEqual(r['status'],'open');self.assertEqual(r['unresolved'],['goal'])
    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            s=Path(d)/'state.json';initialize(s,'prose','Original');self.assertRaises(FileExistsError,initialize,s,'prose','Replacement');self.assertEqual(read_json(s)['nodes']['goal']['statement'],'Original')
    def test_derived_goal(self):
        g=apply(new('Goal'),[dict(op='claim',id='a',statement='A'),dict(op='derive',id='e',parent='goal',premises=['a'],argument='fixture'),dict(op='review_claim',id='a',decision='established',evidence='fixture'),dict(op='review_edge',id='e',decision='accepted',evidence='fixture')],trusted=True);r=report(g);self.assertEqual(r['status'],'established');self.assertEqual(r['accepted_edges'],['e']);self.assertEqual(g['nodes']['goal']['status'],'open')
    def test_roundtrip_and_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            s=Path(d)/'state.json';p=Path(d)/'checkpoint.json';t=Path(d)/'restored.json';initialize(s,'prose','Goal');subprocess.run([sys.executable,'research_checkpoint.py','checkpoint',str(s),str(p)],check=True,capture_output=True);subprocess.run([sys.executable,'research_checkpoint.py','resume',str(p),str(t)],check=True,capture_output=True);self.assertEqual(read_json(s),read_json(t));r=read_json(p);r['status']='established';p.write_text(json.dumps(r));self.assertNotEqual(subprocess.run([sys.executable,'research_checkpoint.py','resume',str(p),str(t)+'2'],capture_output=True).returncode,0)
    def test_invalid_kind(self):self.assertRaises(ValueError,typed,'invalid',{})
