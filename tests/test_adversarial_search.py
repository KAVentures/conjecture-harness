import unittest
from fractions import Fraction as Q
from adversarial_search import search
import polynomial as p

class AdversarialTests(unittest.TestCase):
    def test_narrow_negative_region(self):
        val=lambda x:(x[0]-Q(17,8))**4-Q(1,65536)
        seen={(Q(0),),(Q(1),),(Q(2),)}
        cert,count=search(val,1,'real','nonnegative',24,[(x,val(x)) for x in seen],seen)
        self.assertEqual(cert['point'],['17/8'])
        self.assertLessEqual(count,24)
        self.assertLess(val(tuple(map(Q,cert['point']))),0)
    def test_integrated_narrow_quartic(self):
        # (x-17/8)^4 - 1/65536
        s=dict(variables=['x'],domain='real',relation='nonnegative',terms=[[[4],1],[[3],'-17/2'],[[2],'867/32'],[[1],'-4913/128'],[[0],'1336335/65536']])
        # Exact constant is 17^4 / 8^4 - 1/65536.
        r=p.solve(s,256);self.assertEqual(r['status'],'counterexample')
        self.assertTrue(p.replay(s,r['certificate']))
        self.assertLessEqual(r['tested'],256)
    def test_unbounded_scale(self):
        val=lambda x:Q(100)-x[0]**3
        cert,n=search(val,1,'nonnegative','nonnegative',64)
        self.assertIsNotNone(cert);self.assertGreaterEqual(Q(cert['point'][0]),0)
        self.assertLess(val(tuple(map(Q,cert['point']))),0)
    def test_budget_and_no_false_proof(self):
        calls=[]
        def val(x):calls.append(x);return x[0]**2
        cert,n=search(val,1,'real','nonnegative',7)
        self.assertIsNone(cert);self.assertEqual(n,len(calls));self.assertEqual(n,len(set(calls)));self.assertLessEqual(n,7)
        self.assertEqual(search(val,1,'real','nonnegative',0),(None,0))
    def test_domain_and_equality(self):
        cert,n=search(lambda x:x[0],1,'nonnegative','nonnegative',32)
        self.assertIsNone(cert)
        cert,n=search(lambda x:x[0],1,'real','zero',8)
        self.assertIsNotNone(cert)
