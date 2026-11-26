import random,unittest,copy
from fractions import Fraction as Q
import exponential_sign as e
import exponential_lab as lab
from discovery import new,apply
from proof_audit import audit

class ExponentialSignTests(unittest.TestCase):
    def test_generated_dominance(self):
        r=random.Random(921)
        for i in range(300):
            rows=[(Q(r.randint(1,5),r.randint(1,3)),r.randrange(5),Q(r.randint(-6,6))) for j in range(r.randrange(1,8))]
            t=e.canonical(rows);c=e.classify(rows,1,'eventual')
            self.assertEqual(e.replay(rows,1,'eventual',c),c['outcome'])
            if t and e.tail(t,512):self.assertEqual(e.value(t,512)>=0,c['outcome']=='proved')
        for i in range(80):
            b=r.randint(2,5);a=r.randint(1,b-1);k=r.randrange(1,4);j=r.randrange(k+1);c=r.randint(1,5);d=r.randint(1,c)
            rows=[(b,k,c),(a,j,-d)]
            cert=e.classify(rows,1,'all')
            self.assertEqual(cert['outcome'],'proved')
            self.assertEqual(e.replay(rows,1,'all',cert),'proved')
    def test_scope_and_cancellation(self):
        s=dict(start=1,quantifier='all',terms=[[2,0,1],[1,3,-1]])
        self.assertEqual(lab.solve(s)['status'],'refuted')
        s['quantifier']='eventual';r=lab.solve(s)
        self.assertEqual(r['status'],'proved')
        self.assertIsNone(lab.replay(dict(s,quantifier='all'),r['certificate']))
        self.assertEqual(lab.solve(dict(s,terms=[[2,0,1],[2,0,-1]]))['certificate']['kind'],'zero')
        self.assertEqual(lab.solve(dict(s,terms=[[2,1,-1],[2,0,3]]))['status'],'refuted')
    def test_tail_and_audit(self):
        s=dict(start=1,quantifier='all',terms=[[3,1,1],[2,0,-1]])
        r=lab.solve(s)
        self.assertEqual(r['status'],'proved')
        self.assertEqual(lab.replay(s,r['certificate']),'proved')
        self.assertEqual(audit(lab.auto_discharge(new(lab.statement(s))))['status'],'proved')
        self.assertIsNone(lab.replay(dict(s,terms=[[3,1,-1],[2,0,-1]]),r['certificate']))
        with self.assertRaises(ValueError):apply(new('x'),[dict(op='observe',id='exponential-sign-fake',focus='goal',kind='proof_sketch',detail='fake')])
