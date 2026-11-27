import itertools,unittest
import finite_csp as fc
import modular_discovery as md
from discovery import new
from constraint_discovery_lab import auto_discharge
from proof_audit import audit
from proof_bundle import export,replay

class ConstraintTests(unittest.TestCase):
    def test_linear_and_table(self):
        s=dict(domains=[[0,1],[0,1]],constraints=[dict(kind="linear",coefficients=[1,1],relation="eq",rhs=1),dict(kind="table",variables=[0,1],allowed=[[0,1]])])
        r=fc.solve(s);self.assertEqual(r["status"],"proved")
        self.assertEqual(fc.replay(s,r["certificate"]),"proved")
        self.assertIsNone(fc.replay(s,dict(kind="assignment",assignment=[1,0])))
        self.assertEqual(fc.parse_statement(fc.statement(s)),fc.normalize(s))

    def test_hall_and_tamper(self):
        s=dict(domains=[[1,2]]*3,constraints=[dict(kind="different",variables=[0,1,2])])
        r=fc.solve(s);self.assertEqual(r["status"],"refuted")
        self.assertEqual(fc.replay(s,r["certificate"]),"refuted")
        self.assertIsNone(fc.replay(dict(s,domains=[[1,2,3]]*3),r["certificate"]))

    def test_split_and_unknown(self):
        s=dict(domains=[[0,2],[0,2]],constraints=[dict(kind="linear",coefficients=[1,1],relation="eq",rhs=1)])
        r=fc.solve(s);self.assertEqual(r["status"],"refuted")
        self.assertEqual(fc.solve(s,1)["status"],"unknown")
        self.assertIsNone(fc.replay(s,dict(kind="no-solution",nodes=r["certificate"]["nodes"][-1:])))

    def test_residue_and_counterexample(self):
        s=dict(variables=1,modulus=6,assumptions=[],conclusion=dict(terms=[[[3],1],[[1],-1]],allowed=[0]))
        r=md.solve(s);self.assertEqual(r["status"],"proved")
        self.assertEqual(md.solve(s,2)["status"],"unknown")
        t=dict(s,modulus=5)
        r=md.solve(t);self.assertEqual(r["status"],"refuted")
        self.assertIsNone(md.replay(s,r["certificate"]))
        self.assertEqual(md.parse_statement(md.statement(s)),md.normalize(s))

    def test_conditional_residues(self):
        s=dict(variables=1,modulus=4,assumptions=[dict(terms=[[[1],1]],allowed=[0,2])],conclusion=dict(terms=[[[2],1]],allowed=[0]))
        self.assertEqual(md.solve(s)["status"],"proved")
        self.assertEqual(md.crt_children(s),[])

    def test_crt_invention_and_audit(self):
        s=dict(variables=1,modulus=6,assumptions=[],conclusion=dict(terms=[[[3],1],[[1],-1]],allowed=[0]))
        g=auto_discharge(new(md.statement(s)));self.assertEqual(len(g["edges"]),1)
        self.assertNotIn("goal",audit(g)["proved"])
        # Discharge both children without direct goal proof; then replay bridge.
        from discovery import frontier,record,fingerprint
        import json
        for i in frontier(g):
            if i=="goal":continue
            t=md.parse_statement(g["nodes"][i]["statement"]);r=md.solve(t)
            oid="modular-residue-"+fingerprint(i)[:20]
            g=record(g,"forward",i,[dict(op="observe",id=oid,focus=i,kind="proof_sketch",detail=json.dumps(r)),dict(op="review_claim",id=i,decision="established",evidence=oid)],trusted=True)
        a=audit(g);self.assertIn(a["proved"]["goal"],a["checked_edges"])
        self.assertTrue(replay(export(g),md.statement(s)))

    def test_csp_audit(self):
        s=dict(domains=[[0,1]],constraints=[dict(kind="linear",coefficients=[1],relation="eq",rhs=2)])
        g=auto_discharge(new(fc.statement(s)));self.assertIn("goal",audit(g)["refuted"])
