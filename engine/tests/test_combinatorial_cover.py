import unittest
import combinatorial_cover as c
from discovery import new
from combinatorial_cover_lab import auto_discharge
from proof_audit import audit

class CoverTests(unittest.TestCase):
    def path(self,**kw):
        s=dict(kind="paths",n=3,edges=[[0,1],[1,2]],endpoints=[1,0,1],max_pieces=1)
        s.update(kw);return s

    def test_positive_and_tamper(self):
        s=self.path();r=c.solve(s)
        self.assertEqual(r["status"],"proved")
        self.assertEqual(c.replay(s,r["certificate"]),"proved")
        self.assertIsNone(c.replay(s,dict(kind="cover",rows=[])))
        self.assertEqual(c.parse_statement(c.statement(s)),c.normalize(s))

    def test_negative_and_tamper(self):
        s=self.path(endpoints=[0,2,0]);r=c.solve(s)
        self.assertEqual(r["status"],"refuted")
        self.assertEqual(c.replay(s,r["certificate"]),"refuted")
        self.assertIsNone(c.replay(self.path(),r["certificate"]))
        self.assertIsNone(c.replay(s,dict(kind="no-cover-dag",states=[[0,0,[0,0,0]]])))

    def test_negative_nontrivial_and_budget(self):
        s=dict(kind="cover",items=3,rows=[[[0,1],[]],[[0,2],[]],[[1,2],[]]],resources=[],max_pieces=2)
        r=c.solve(s);self.assertEqual(r["status"],"refuted")
        self.assertEqual(c.solve(s,budget=1)["status"],"unknown")
        self.assertIsNone(c.replay(s,dict(kind="no-cover-dag",states=r["certificate"]["states"][-1:])))

    def test_exact_resources(self):
        s=dict(kind="cover",items=2,rows=[[[0],[1]],[[1],[1]],[[0,1],[1]]],resources=[2],max_pieces=2)
        self.assertEqual(c.solve(s)["status"],"proved")
        s["max_pieces"]=1
        self.assertEqual(c.solve(s)["status"],"refuted")

    def test_cycle_is_not_path(self):
        s=self.path(edges=[[0,1],[0,2],[1,2]],endpoints=None)
        self.assertEqual(c.solve(s)["status"],"refuted")
        s["max_pieces"]=2
        self.assertEqual(c.solve(s)["status"],"proved")

    def test_empty_and_malformed(self):
        self.assertEqual(c.solve(dict(kind="cover",items=0,rows=[],resources=[],max_pieces=0))["status"],"proved")
        with self.assertRaises(ValueError):c.solve(self.path(edges=[[0,1],[1,0]]))
        with self.assertRaises(ValueError):c.solve(self.path(max_pieces=True))

    def test_activation_receipt(self):
        import tempfile
        from pathlib import Path
        from activate import execute
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"run"
            r=execute(root,c.statement(self.path()),passes=1,seconds=10)
            self.assertIn("goal",r["audit"]["proved"])
            self.assertEqual(r["exact_execution"]["model_calls"],0)
            self.assertTrue((root/r["checkpoint"]).is_file())

    def test_proof_graph(self):
        for s,expected in [(self.path(),"proved"),(self.path(endpoints=[0,2,0]),"refuted")]:
            g=auto_discharge(new(c.statement(s)));a=audit(g)
            self.assertIn("goal",a[expected])
            self.assertFalse(a["invalid_observations"])

if __name__=="__main__":unittest.main()
