import unittest
from fractions import Fraction as F
import symbolic_discovery as s
import symbolic_lab
from discovery import new,closure,apply
from proof_audit import audit
class SymbolicTests(unittest.TestCase):
    def spec(self,relation='zero'):
        return dict(parameters=['x'],relation=relation,summand=[[[1,1],2],[[0,1],1]],rhs=[[[2,1],1]])
    def test_discover(self):
        r=s.discover(self.spec()['summand'],['x'])
        self.assertEqual(r['spec'],s.normalize(self.spec()))
        self.assertEqual(s.replay(r['spec'],r['certificate']),'proved')
    def test_induction(self):
        r=s.solve(self.spec());self.assertEqual(r['status'],'proved')
        g=symbolic_lab.auto_discharge(new(s.statement(self.spec())))
        self.assertIn('goal',closure(g));self.assertEqual(audit(g)['status'],'proved')
    def test_integer_domain(self):
        z=dict(parameters=[],relation='nonnegative',summand=[],rhs=[[[1],1],[[2],-1]])
        r=s.solve(z);self.assertEqual(r['status'],'proved')
        self.assertIsNone(s.replay(z,dict(kind='newton-induction',residual=[[[1],1]])))
    def test_refute(self):
        z=dict(self.spec(),rhs=[[[2,1],2]])
        r=s.solve(z);self.assertEqual(r['status'],'counterexample')
        self.assertEqual(s.replay(z,r['certificate']),'refuted')
        self.assertIsNone(s.replay(self.spec(),r['certificate']))
    def test_degree_and_parameters(self):
        z=s.discover([[[4,2,1],3],[[2,0,3],-5]],['x','y'])
        self.assertEqual(s.replay(z['spec'],z['certificate']),'proved')
        self.assertEqual(s.newton({(2,):F(1)}),{(1,):1,(2,):2})
    def test_limits_and_reserved(self):
        with self.assertRaises(ValueError):s.discover([[[13],1]],[])
        with self.assertRaises(ValueError):s.solve(self.spec(),True)
        with self.assertRaises(ValueError):apply(new('x'),[dict(op='observe',id='symbolic-fake',focus='goal',kind='proof_sketch',detail='fake')])
