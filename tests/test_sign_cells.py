import random,unittest
from fractions import Fraction as Q
import sign_cells as s
import univariate_sign as u
import sign_cells_lab as lab
import conditional_theorems as ct
from discovery import new,closure,apply
from proof_audit import audit

class SignCellTests(unittest.TestCase):
    def test_exact_factored_oracle(self):
        rng=random.Random(920)
        for i in range(400):
            ps=[];roots=set()
            for _ in range(rng.randrange(1,5)):
                p=[Q(rng.choice([-1,1,2]))]
                for _ in range(rng.randrange(0,5)):
                    x=Q(rng.randint(-6,6),rng.randint(1,4));roots.add(x);p=u.multiply(p,[-x,Q(1)])
                if rng.randrange(3)==0:p=u.multiply(p,[Q(1),Q(0),Q(1)])
                ps.append(p)
            rs=[rng.choice(['zero','nonnegative']) for _ in ps[:-1]]
            for dom in ('real','nonnegative'):
                xs=sorted(roots|{Q(0)})
                samples=xs+[xs[0]-1,xs[-1]+1]+[(a+b)/2 for a,b in zip(xs,xs[1:])]
                expected=not any((dom=='real' or x>=0) and all(s.value(p,x)==0 if r=='zero' else s.value(p,x)>=0 for p,r in zip(ps,rs)) and s.value(ps[-1],x)<0 for x in samples)
                self.assertEqual(s.classify(ps,rs,dom)['outcome']=='proved',expected)
    def test_irrational_feasible_points(self):
        r=s.classify([[-2,0,1],[-2,1]],['zero'],'real')
        self.assertEqual(r['outcome'],'refuted')
        self.assertEqual(r['witness']['kind'],'algebraic-root')
        self.assertEqual(s.classify([[-2,0,1],[0,1]],['zero'],'nonnegative')['outcome'],'proved')
        self.assertEqual(s.classify([[0,1],[-1]],['zero'],'nonnegative')['witness']['point'],'0')
    def test_graph_audit(self):
        spec=dict(variables=['x'],domain='real',assumptions=[dict(relation='zero',terms=[[[2],1],[[0],-2]])],conclusion=[[[1],1],[[0],-2]])
        g=lab.auto_discharge(new(ct.statement(spec)))
        self.assertEqual(audit(g)['status'],'refuted')
        r=lab.solve(spec)
        self.assertEqual(lab.replay(spec,r['certificate']),'refuted')
        self.assertIsNone(lab.replay(dict(spec,conclusion=[[[2],1]]),r['certificate']))
        good=dict(spec,domain='nonnegative',conclusion=[[[1],1]])
        g=lab.auto_discharge(new(ct.statement(good)))
        self.assertIn('goal',closure(g));self.assertEqual(audit(g)['status'],'proved')
    def test_reserved(self):
        with self.assertRaises(ValueError):apply(new('x'),[dict(op='observe',id='sign-cell-fake',focus='goal',kind='proof_sketch',detail='fake')])
