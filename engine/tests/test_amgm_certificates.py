import copy,random,unittest
from fractions import Fraction as Q
import amgm_certificates as a
import amgm_lab as lab
import polynomial as p
from discovery import new,closure,apply
from proof_audit import audit

class AMGMTests(unittest.TestCase):
    def spec(self):
        return dict(variables=['x','y'],domain='real',relation='nonnegative',terms=[[[4,2],1],[[2,4],1],[[0,0],1],[[2,2],-3]])
    def test_motzkin(self):
        s=self.spec();r=lab.solve(s)
        self.assertEqual(r['status'],'proved')
        self.assertEqual(lab.replay(s,r['certificate']),'proved')
        bad=copy.deepcopy(r['certificate']);bad['circuits'][0]['coefficient']='4'
        self.assertIsNone(lab.replay(s,bad))
        g=lab.auto_discharge(new(p.statement(s)))
        self.assertIn('goal',closure(g));self.assertEqual(audit(g)['status'],'proved')
    def test_domain_and_exact_weights(self):
        s=dict(variables=['x','y'],domain='nonnegative',relation='nonnegative',terms=[[[2,0],1],[[0,2],1],[[1,1],-2]])
        self.assertEqual(lab.solve(s)['status'],'proved')
        self.assertEqual(a.weights([(0,0),(6,0)],(2,0)),[2,1])
        self.assertTrue(a.sufficient([Q(2),Q(1)],[2,1],Q(3)))
        self.assertFalse(a.sufficient([Q(1),Q(1)],[2,1],Q(3)))
        odd=dict(s,terms=[[[1,0],1],[[0,1],1]])
        self.assertEqual(lab.solve(odd)['status'],'proved')
        self.assertEqual(lab.solve(dict(odd,domain='real'))['status'],'unknown')
    def test_random_circuits_and_tampering(self):
        rng=random.Random(67);cnt=0
        for _ in range(300):
            n=rng.choice([1,2,3,4]);dom=rng.choice(['real','nonnegative']);unit=2 if dom=='real' else 1
            e=tuple(unit*rng.randint(0,1) for i in range(n));f=tuple(unit*rng.randint(0,1) for i in range(n))
            if e==f or any((x+y)%2 for x,y in zip(e,f)):continue
            beta=tuple((x+y)//2 for x,y in zip(e,f));poly={e:Q(1),f:Q(1),beta:Q(-2)}
            cert,_=a.solve(poly,dom);self.assertIsNotNone(cert);self.assertTrue(a.replay(poly,dom,cert))
            self.assertFalse(a.replay(dict(poly)|{beta:Q(-3)},dom,cert));cnt+=1
        self.assertEqual(cnt,116)
    def test_reserved_and_wrong_relation(self):
        with self.assertRaises(ValueError):apply(new('x'),[dict(op='observe',id='amgm-fake',focus='goal',kind='proof_sketch',detail='fake')])
        self.assertEqual(lab.solve(dict(self.spec(),relation='zero'))['status'],'unknown')
