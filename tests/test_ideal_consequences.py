import random,unittest,copy
from fractions import Fraction as Q
import ideal_consequences as ic
import ideal_consequence_lab as lab
import conditional_theorems as ct
from discovery import new,closure,apply
from proof_audit import audit

def spec(g,t):
    return dict(variables=['x','y'],domain='real',assumptions=[dict(relation='zero',terms=q) for q in g],conclusion=t)

class IdealConsequenceTests(unittest.TestCase):
    def test_s_pair_and_replay(self):
        s=spec([[[[1,1],1],[[0,0],-1]],[[[0,2],1],[[0,0],-1]]],[[[1,0],1],[[0,1],-1]])
        r=lab.solve(s);self.assertEqual(r['status'],'proved')
        self.assertEqual(r['certificate']['kind'],'residual')
        self.assertGreater(r['pairs'],0)
        self.assertEqual(lab.replay(s,r['certificate']),'proved')
        bad=copy.deepcopy(r['certificate']);bad['multipliers'][0]=[]
        self.assertIsNone(lab.replay(s,bad))
        g=lab.auto_discharge(new(ct.statement(s)))
        self.assertIn('goal',closure(g));self.assertEqual(audit(g)['status'],'proved')
    def test_inconsistent(self):
        s=spec([[[[1,0],1]],[[[1,0],1],[[0,0],-1]]],[[[0,0],-1]])
        r=lab.solve(s);self.assertEqual(r['certificate']['kind'],'inconsistent')
        self.assertIsNone(lab.replay(dict(s,assumptions=s['assumptions'][:1]),r['certificate']))
    def test_radical(self):
        s=spec([[[[2,0],1]]],[[[1,0],1]])
        r=lab.solve(s);self.assertEqual(r['certificate']['kind'],'zero-power')
        self.assertEqual(r['certificate']['power'],2)
        self.assertIsNone(lab.replay(dict(s,conclusion=[[[0,1],1]]),r['certificate']))
    def test_residual_sos_and_false_claim(self):
        s=spec([[[[1,0],1],[[0,1],-1]]],[[[1,0],1],[[0,1],-1],[[0,2],1]])
        self.assertEqual(lab.solve(s)['status'],'proved')
        self.assertEqual(lab.solve(dict(s,conclusion=[[[0,0],-1]]))['status'],'unknown')
    def test_inequality_not_generator(self):
        s=spec([[[[1,0],1]]],[[[1,0],-1]])
        s['assumptions'][0]['relation']='nonnegative'
        self.assertEqual(lab.solve(s)['status'],'unknown')
    def test_random_basis_identities(self):
        rng=random.Random(479);tested=0
        for _ in range(150):
            def poly(d=2):
                q={}
                for j in range(4):q[rng.randint(0,d),rng.randint(0,d)]=Q(rng.randint(-3,3))
                return ic.clean(q)
            gs=[poly(),poly()];target=ic.identity(gs,[poly(1),poly(1)],2)
            try:
                basis,_=ic.basis_search(gs,2,24)
                for q,v in basis:
                    self.assertEqual(ic.identity(gs,v,2),q);tested+=1
                for kind,k,rem,v,_ in ic.candidates(gs,target,2,24):
                    q=ic.identity(gs,v,2)
                    if kind=='inconsistent':self.assertEqual(q,{(0,0):Q(1)})
                    elif kind=='residual':self.assertEqual(ic.add(q,rem),target)
                    else:
                        power=target
                        for j in range(k-1):power=ic.mul(power,target)
                        self.assertEqual(q,power)
                    tested+=1
            except ValueError:continue
        self.assertGreater(tested,500)
    def test_reserved(self):
        with self.assertRaises(ValueError):apply(new('x'),[dict(op='observe',id='ideal-consequence-fake',focus='goal',kind='proof_sketch',detail='fake')])
