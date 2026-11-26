import tempfile,unittest
from pathlib import Path
from discovery import new,save,closure
from discovery_tools import run
from runtime import read_json
import polynomial as p

class ToolsTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.path=Path(t.name)/'state.json'
    def test_proof_and_resume(self):
        save(self.path,new(p.statement(dict(variables=['x'],domain='real',relation='nonnegative',terms=[[[2],1]]))))
        r=run(self.path);self.assertEqual(r['reason'],'closed');self.assertEqual(r['model_calls'],0);self.assertIn('goal',closure(read_json(self.path)));self.assertEqual(run(self.path)['passes'],0)
    def test_unknown_fixed_point(self):
        save(self.path,new('Unformalized research statement'));r=run(self.path);self.assertEqual(r['reason'],'fixed_point');self.assertNotIn('stop',r['next']);self.assertEqual(r['passes'],1)
    def test_refutation(self):
        save(self.path,new(p.statement(dict(variables=['x'],domain='real',relation='nonnegative',terms=[[[0],-1]]))));r=run(self.path);self.assertEqual(r['next']['goal_status'],'refuted');self.assertFalse(r['next']['derived'])
    def test_limits(self):
        save(self.path,new('Goal'))
        for a in (dict(passes=0),dict(passes=True),dict(seconds=float('inf'))):self.assertRaises(ValueError,run,self.path,**a)
