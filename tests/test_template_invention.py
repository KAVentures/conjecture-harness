import unittest
from discovery import new
from proof_audit import audit
import template_invention as t

def fixture(cap=1):
    # A shared theta must satisfy theta>=x everywhere on [0,1],
    # and theta<=cap. The first attempted theta=0 is false.
    return dict(dimension=1,rows=[],rhs=[],parameter_bounds=[[0,2]],
                parameter_equalities=[],parameter_rhs=[],polynomials=[
                    dict(base=[[[1],-1]],directions=[[[[0],1]]]),
                    dict(base=[[[0],cap]],directions=[[[[0],-1]]])])

class TemplateTests(unittest.TestCase):
    def test_synthesis(self):
        s=fixture();r=t.solve(s)
        self.assertEqual(r['status'],'proved')
        self.assertEqual(r['certificate']['parameters'],['1'])
        self.assertGreaterEqual(r['tested'],2)
        self.assertEqual(t.replay(s,r['certificate']),'proved')
        self.assertIn('goal',audit(t.auto_discharge(new(t.statement(s))))['proved'])
        self.assertIsNone(t.replay(s,dict(r['certificate'],parameters=['0'])))
        self.assertIsNone(t.replay(s,dict(r['certificate'],proofs=r['certificate']['proofs'][:1])))
    def test_impossible_template(self):
        s=fixture('1/2');r=t.solve(s)
        self.assertEqual(r['status'],'counterexample')
        self.assertEqual(t.replay(s,r['certificate']),'refuted')
        self.assertIn('goal',audit(t.auto_discharge(new(t.statement(s))))['refuted'])
        bad=dict(r['certificate'],multipliers=['0']*len(r['certificate']['multipliers']))
        self.assertIsNone(t.replay(s,bad))
        bad=dict(r['certificate'],cuts=[dict(inequality=0,point=['2'])])
        self.assertIsNone(t.replay(s,bad))
    def test_parameter_equalities(self):
        s=fixture();s['parameter_equalities']=[[1]];s['parameter_rhs']=[1]
        r=t.solve(s);self.assertEqual(r['status'],'proved')
        self.assertEqual(t.replay(s,r['certificate']),'proved')
        self.assertIsNone(t.replay(dict(s,parameter_rhs=[0]),r['certificate']))
    def test_scope_and_budget(self):
        s=fixture();self.assertEqual(t.solve(s,budget=1)['status'],'unknown')
        self.assertEqual(t.parse_statement(t.statement(s)),t.normalize(s))

if __name__=='__main__':unittest.main()
