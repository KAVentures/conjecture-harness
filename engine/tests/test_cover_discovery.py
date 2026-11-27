import copy
import unittest
import combinatorial_cover as cc
import cover_transfer as ct
import cover_experiments as ce
from discovery import new
from combinatorial_cover_lab import auto_discharge
from proof_audit import audit
from proof_bundle import export,replay

class DiscoveryTests(unittest.TestCase):
    def path(self,**kw):
        s=dict(kind="paths",n=4,edges=[[0,1],[1,2],[2,3]],endpoints=[1,0,0,1],max_pieces=1)
        s.update(kw);return s

    def test_surgery(self):
        s=self.path();p=ct.suppress(s,1);cert=dict(kind="suppress",vertex=1)
        self.assertTrue(ct.replay(cc.statement(s),[cc.statement(p)],cert))
        self.assertFalse(ct.replay(cc.statement(s),[cc.statement(p)],dict(cert,vertex=0)))
        with self.assertRaises(ValueError):ct.suppress(self.path(edges=[[0,1],[0,2],[1,2]]),1)
        with self.assertRaises(ValueError):ct.suppress(self.path(endpoints=[1,2,0,1]),1)

    def test_graph_bridge_and_bundle(self):
        g=ct.auto_discharge(new(cc.statement(self.path())))
        self.assertEqual(len(g["edges"]),1)
        self.assertNotIn("goal",audit(g)["proved"])
        g=auto_discharge(g,limit=1)
        report=audit(g)
        self.assertIn("goal",report["proved"])
        self.assertIn(report["proved"]["goal"],report["checked_edges"])
        self.assertTrue(replay(export(g),g["nodes"]["goal"]["statement"]))

    def test_monotonicity(self):
        s=self.path();g=dict(s,endpoints=None,max_pieces=2)
        self.assertTrue(ct.replay(cc.statement(g),[cc.statement(s)],dict(kind="monotone")))
        self.assertFalse(ct.replay(cc.statement(s),[cc.statement(g)],dict(kind="monotone")))
        x=dict(kind="cover",items=2,rows=[[[0],[]],[[1],[]]],resources=[],max_pieces=2)
        y=dict(x,rows=x["rows"]+[[[0,1],[]]])
        self.assertTrue(ct.replay(cc.statement(y),[cc.statement(x)],dict(kind="monotone")))

    def test_experiment(self):
        s=dict(min_n=3,max_n=3,connected=True,min_degree=0,bound=[0,1,1],graph_budget=8,state_budget=128)
        r=ce.run(s)
        self.assertEqual(r["scanned"],8)
        self.assertEqual(r["counts"],dict(proved=3,refuted=1,unknown=0,skipped=4))
        self.assertTrue(ce.replay(r))
        bad=copy.deepcopy(r);bad["counts"]["refuted"]=0
        self.assertFalse(ce.replay(bad))
        self.assertFalse(ce.run(dict(s,graph_budget=2))["enumeration_complete"])

    def test_minimum_and_lean(self):
        from cover_lean import render
        s=self.path(edges=[[0,1],[1,2],[0,2]],endpoints=None,max_pieces=3)
        r=ce.budget_frontier(s)
        self.assertEqual(r["minimum_certified"],2)
        source=render(s,cc.solve(s)["certificate"])
        self.assertIn("∃ chosen",source)
        self.assertIn("#print axioms harness_checked",source)
        with self.assertRaises(ValueError):render(s,dict(kind="cover",rows=[]))

    def test_weighted_dual(self):
        s=dict(kind="paths",n=4,edges=[[0,1],[0,2],[0,3]],endpoints=None,max_pieces=1)
        r=cc.solve(s)
        self.assertEqual(r["status"],"refuted")
        self.assertEqual(r["certificate"]["kind"],"weighted-bound")
        self.assertEqual(cc.replay(s,r["certificate"]),"refuted")
        self.assertIsNone(cc.replay(dict(s,max_pieces=2),r["certificate"]))
        self.assertIsNone(cc.replay(s,dict(r["certificate"],weights=[0,0,0])))
