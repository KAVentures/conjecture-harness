import unittest
from fractions import Fraction as F
import polynomial as p
from polynomial_transform import shift,solve,auto_discharge
from discovery import new,closure,apply
from discovery_run import auto_discharge as full


def spec(k,neg=0,domain='real'):
    # (x-k)^4-neg
    return dict(variables=['x'],domain=domain,relation='nonnegative',terms=[[[4],1],[[3],-4*k],[[2],6*k*k],[[1],-4*k**3],[[0],k**4-neg]])

class TransformTests(unittest.TestCase):
    def test_exact_expansion(self):
        self.assertEqual(shift({(2,):F(1)},F(1,2)),{(0,):F(1,4),(1,):F(1),(2,):F(1)})
    def test_quartic_proof(self):
        s=spec(3);self.assertEqual(p.solve(s)['status'],'unknown');r=solve(s);self.assertEqual(r['status'],'proved');self.assertTrue(p.replay(s,r['certificate']));self.assertEqual(r['translation'],'3')
    def test_quartic_counterexample(self):
        s=spec(7,1);self.assertEqual(p.solve(s)['status'],'unknown');r=solve(s);self.assertEqual(r['status'],'counterexample');self.assertEqual(r['certificate']['point'],['7']);self.assertTrue(p.replay(s,r['certificate']))
    def test_orthant_no_transport(self):self.assertEqual(solve(spec(-3,1,'nonnegative'))['status'],'unknown')
    def test_zero_shift(self):self.assertEqual(solve(spec(0))['status'],'unknown')
    def test_runner_proof(self):
        g=full(new(p.statement(spec(3))));self.assertIn('goal',closure(g));self.assertTrue(any(k.startswith('shift-') for k in g['observations']))
    def test_runner_refutation(self):
        g=full(new(p.statement(spec(7,1))));self.assertEqual(g['nodes']['goal']['status'],'refuted')
    def test_reserved(self):self.assertRaises(ValueError,apply,new('target'),[dict(op='observe',id='shift-fake',focus='goal',kind='experiment',detail='fake')])
