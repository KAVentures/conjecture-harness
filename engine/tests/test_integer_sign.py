import random,unittest,copy
from fractions import Fraction as Q
from univariate_sign import multiply
from sign_cells import value
import integer_sign as ins
import integer_lab as lab
from discovery import new,apply
from proof_audit import audit

class IntegerSignTests(unittest.TestCase):
    def test_factored_oracle(self):
        r=random.Random(822)
        for _ in range(600):
            ps=[]
            for i in range(r.randrange(1,5)):
                p=[Q(r.choice([-2,-1,1,3]))]
                for j in range(r.randrange(5)):
                    x=Q(r.randint(-12,20),r.randint(1,4));p=multiply(p,[-x,Q(1)])
                if r.randrange(3)==0:p=multiply(p,[Q(1),Q(0),Q(1)])
                ps.append(p)
            rs=[r.choice(['zero','nonnegative']) for p in ps[:-1]]
            start=r.randrange(8)
            # All possible real roots are <=20; 23 samples the final tail.
            expected=not any(all(value(p,Q(i))==0 if rel=='zero' else value(p,Q(i))>=0 for p,rel in zip(ps,rs)) and value(ps[-1],Q(i))<0 for i in range(start,24))
            result=ins.classify(ps,rs,start)
            self.assertEqual(result['outcome']=='proved',expected)
            self.assertEqual(ins.replay(ps,rs,start,dict(kind='integer-sign',classification=result)),result['outcome'])
    def test_between_integers_and_remote(self):
        self.assertEqual(ins.classify([[Q(2,9),-1,1]],[],0)['outcome'],'proved')
        m=10**9
        r=ins.classify([[m*m-1,-2*m,1]],[],0)
        self.assertEqual(r['witness'],str(m))
        self.assertEqual(ins.replay([[m*m-1,-2*m,1]],[],0,dict(kind='integer-sign',classification=r)),'refuted')
    def test_integer_vs_eventual(self):
        s=dict(start=0,quantifier='all',assumptions=[],conclusion=[[[1],1],[[0],-2]])
        self.assertEqual(lab.solve(s)['status'],'refuted')
        s['quantifier']='eventual';r=lab.solve(s)
        self.assertEqual(r['status'],'proved')
        self.assertEqual(lab.replay(s,r['certificate']),'proved')
        self.assertIsNone(lab.replay(dict(s,quantifier='all'),r['certificate']))
        self.assertEqual(lab.solve(dict(s,conclusion=[[[1],-1]]))['status'],'refuted')
    def test_irrational_equality_and_graph(self):
        s=dict(start=0,quantifier='all',assumptions=[dict(relation='zero',terms=[[[2],1],[[0],-2]])],conclusion=[[[0],-1]])
        self.assertEqual(lab.solve(s)['status'],'proved')
        g=lab.auto_discharge(new(lab.statement(s)))
        self.assertEqual(audit(g)['status'],'proved')
        with self.assertRaises(ValueError):apply(new('x'),[dict(op='observe',id='integer-sign-fake',focus='goal',kind='proof_sketch',detail='fake')])
