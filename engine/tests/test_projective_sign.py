import random,unittest
from fractions import Fraction as Q
import projective_sign as p
import univariate_sign as u
import projective_lab as lab
import conditional_theorems as ct
import simplex_discovery as sx
import polynomial
from discovery import new,closure,apply
from proof_audit import audit

class ProjectiveTests(unittest.TestCase):
    def test_exact_factored_oracle(self):
        rng=random.Random(277)
        for i in range(250):
            raw=[];roots=set()
            for _ in range(rng.randrange(1,5)):
                q=[Q(rng.choice([-1,1,2]))]
                for _ in range(rng.randrange(0,5)):
                    x=Q(rng.randint(-6,6),rng.randint(1,4));roots.add(x);q=u.multiply(q,[-x,Q(1)])
                d=len(q)-1+rng.randrange(0,3)
                raw.append({(k,d-k):c for k,c in enumerate(q) if c})
            rs=[rng.choice(['zero','nonnegative']) for _ in raw[:-1]]
            xs=sorted(roots|{-x for x in roots}|{Q(0)})
            samples=xs+[xs[0]-1,xs[-1]+1]+[(a+b)/2 for a,b in zip(xs,xs[1:])]
            for domain in ('real','nonnegative'):
                pts=[(x,y) for x in samples for y in (-1,1) if domain=='real' or x>=0 and y>=0]+[(Q(x),Q(0)) for x in (-1,0,1) if domain=='real' or x>=0]
                def evaluate(q,x,y):return sum(c*x**a*y**b for (a,b),c in q.items())
                expected=not any(all(evaluate(q,x,y)==0 if r=='zero' else evaluate(q,x,y)>=0 for q,r in zip(raw,rs)) and evaluate(raw[-1],x,y)<0 for x,y in pts)
                self.assertEqual(p.binary(raw,rs,domain)['outcome']=='proved',expected)
    def test_axis_orientation_and_roots(self):
        self.assertEqual(p.binary([{(1,0):1}],[],'real')['witness']['kind'],'axis')
        self.assertEqual(p.binary([{(0,1):1}],[],'real')['witness']['orientation'],-1)
        self.assertEqual(p.binary([{(0,1):1}],[],'nonnegative')['outcome'],'proved')
        self.assertEqual(p.binary([{(2,0):1,(0,2):-2},{(0,2):-1}],['zero'],'real')['outcome'],'refuted')
    def test_conditional_and_audit(self):
        s=dict(variables=['x','y'],domain='real',assumptions=[dict(relation='zero',terms=[[[2,0],1],[[0,2],-2]])],conclusion=[[[0,2],-1]])
        text=ct.statement(s);g=lab.auto_discharge(new(text))
        self.assertEqual(audit(g)['status'],'refuted')
        r=lab.solve(text)
        self.assertIsNone(lab.replay(ct.statement(dict(s,conclusion=[[[0,2],1]])),r['certificate']))
    def test_segment_and_unsupported(self):
        text=sx.statement(dict(variables=['x','y'],terms=[[[2,0],1],[[1,1],-2],[[0,2],1]]))
        g=lab.auto_discharge(new(text))
        self.assertIn('goal',closure(g));self.assertEqual(audit(g)['status'],'proved')
        spec=dict(variables=['x','y'],domain='real',relation='nonnegative',terms=[[[0,0],1],[[2,0],1]])
        self.assertEqual(lab.solve(polynomial.statement(spec))['status'],'unknown')
    def test_reserved(self):
        with self.assertRaises(ValueError):apply(new('x'),[dict(op='observe',id='projective-fake',focus='goal',kind='proof_sketch',detail='fake')])
