import unittest
from fractions import Fraction as Q
import simplex_discovery as s
import extremal_reduction as e
from discovery import new,closure,apply
from proof_audit import audit
from structured_algebra_lab import auto_discharge

def spec(t,vs=None):return dict(variables=vs or ['x','y'],terms=t)
class SimplexTests(unittest.TestCase):
    def test_homogeneous_constraint(self):
        g=spec([[[0,0],-1],[[1,0],1],[[0,1],1]])
        r=s.solve(g);self.assertEqual(r['status'],'proved');self.assertEqual(s.replay(g,r['certificate']),'proved')
    def test_exact_split(self):
        g=spec([[[2,0],1],[[1,1],-2],[[0,2],1]])
        r=s.solve(g);self.assertEqual(r['status'],'proved')
        self.assertIn('split',r['certificate']['tree'])
        bad=dict(kind='simplex-cover',tree=dict(degree=2))
        self.assertIsNone(s.replay(g,bad))
        self.assertIsNone(s.replay(g,dict(kind='simplex-cover',tree=dict(split=[0,1],left=dict(degree=2)))))
    def test_witness(self):
        g=spec([[[0,0],-1],[[2,0],1]])
        r=s.solve(g);self.assertEqual(r['status'],'counterexample');self.assertEqual(s.replay(g,r['certificate']),'refuted')
        self.assertIsNone(s.replay(g,dict(kind='point',point=['0','0'])))
    def test_audit(self):
        g=spec([[[1,0],1]])
        h=auto_discharge(new(s.statement(g)))
        self.assertIn('goal',closure(h));self.assertEqual(audit(h)['status'],'proved')
    def test_extremal_reduction(self):
        g=spec([[[1,1,0],1],[[0,0,1],1]],['x','y','z'])
        parts=e.obligations(g,0,1)
        self.assertEqual(parts[0]['terms'],[[[0,0,0],'2']])
        self.assertTrue(e.replay(g,parts,dict(pair=[0,1])))
        self.assertFalse(e.replay(g,parts[:2],dict(pair=[0,1])))
        h=e.auto_discharge(new(s.statement(g)))
        self.assertNotIn('goal',closure(h))
        for _ in range(3):h=auto_discharge(h)
        self.assertIn('goal',closure(h))
        self.assertEqual(audit(h)['status'],'proved')
    def test_convex_not_reduced_as_concave(self):
        g=spec([[[2,0,0],1],[[0,2,0],1]],['x','y','z'])
        parts=e.obligations(g,0,1)
        self.assertEqual(s.solve(parts[0])['status'],'counterexample')
    def test_reserved(self):
        for prefix in ('simplex-','extremal-'):
            with self.assertRaises(ValueError):apply(new('x'),[dict(op='observe',id=prefix+'fake',focus='goal',kind='proof_sketch',detail='fake')])
