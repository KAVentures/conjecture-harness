import random,unittest
from fractions import Fraction as Q
import univariate_sign as s
import univariate_lab as lab
import polynomial as p
from discovery import new,closure,apply
from proof_audit import audit

class SturmTests(unittest.TestCase):
    def test_exact_factored_oracle(self):
        rng=random.Random(619)
        for i in range(500):
            poly=[Q(rng.choice([-3,-1,1,2]))];roots={}
            for j in range(rng.randrange(1,9)):
                r=Q(rng.randint(-6,6),rng.randint(1,4));roots[r]=roots.get(r,0)+1
                poly=s.multiply(poly,[-r,Q(1)])
            for domain in ('real','nonnegative'):
                expected=poly[-1]>0 and not any(k%2 and (domain=='real' or r>0) for r,k in roots.items())
                self.assertEqual(s.classify(poly,domain)['outcome']=='proved',expected)
    def test_irrational_roots_and_boundary(self):
        self.assertEqual(s.classify([-2,0,1],'real')['odd_roots'],2)
        self.assertEqual(s.classify([-2,0,1],'nonnegative')['odd_roots'],1)
        self.assertEqual(s.classify([4,0,-4,0,1],'real')['outcome'],'proved')
        self.assertEqual(s.classify([0,1],'nonnegative')['outcome'],'proved')
        self.assertEqual(s.classify([0,1],'real')['outcome'],'refuted')
        self.assertEqual(s.classify([1,1,1,1,1],'real')['outcome'],'proved')
    def test_exact_graph_replay(self):
        spec=dict(variables=['x'],domain='real',relation='nonnegative',terms=[[[0],1],[[1],1],[[2],1],[[3],1],[[4],1]])
        g=lab.auto_discharge(new(p.statement(spec)))
        self.assertIn('goal',closure(g))
        self.assertEqual(audit(g)['status'],'proved')
        r=lab.solve(spec)
        self.assertIsNone(lab.replay(dict(spec,terms=[[[0],-1]]),r['certificate']))
        spec=dict(spec,terms=[[[0],-2],[[2],1]])
        g=lab.auto_discharge(new(p.statement(spec)))
        self.assertEqual(audit(g)['status'],'refuted')
    def test_reserved(self):
        with self.assertRaises(ValueError):apply(new('x'),[dict(op='observe',id='sturm-fake',focus='goal',kind='proof_sketch',detail='fake')])
