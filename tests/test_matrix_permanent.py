import unittest
from fractions import Fraction as Q
from math import factorial
from itertools import product
import matrix_permanent as m
from matrix_permanent_lab import auto_discharge
from discovery import new,closure,apply
from proof_audit import audit

class MatrixTests(unittest.TestCase):
    def setUp(self):
        self.a=m.matrix([[1,0,0],[0,'1/2','1/2'],[0,'1/2','1/2']])
    def test_exact_coefficients(self):
        c=m.coefficients(self.a);self.assertEqual(c[:2],[1,0])
        for t in (Q(0),Q(1,3),Q(1),Q(-1,2)):
            b=[[Q(1,3)*(1-t)+t*x for x in row] for row in self.a]
            self.assertEqual(m.value(c,t),m.permanent(b)/Q(6,27))
    def test_symbolic_contractions(self):
        b=[[x-Q(1,3) for x in row] for row in self.a]
        c=m.coefficients(self.a)
        for k in (2,3):
            total=Q(0)
            for rows,cols,w in m.matching_identity(k):
                for ix in product(range(3),repeat=len(rows)+len(cols)):
                    ri={v:ix[j] for j,r in enumerate(rows) for v in r}
                    ci={v:ix[len(rows)+j] for j,r in enumerate(cols) for v in r}
                    v=Q(w)
                    for j in range(k):v*=b[ri[j]][ci[j]]
                    total+=v
            self.assertEqual(total*Q(3**k*factorial(3-k),factorial(k)*factorial(3)),c[k])
    def test_finite_certificate_and_audit(self):
        s=dict(kind='lih-wang',matrix=m.encode(self.a));r=m.solve(s)
        self.assertEqual(r['status'],'proved');self.assertEqual(m.replay(s,r['certificate']),'proved')
        self.assertIsNone(m.replay(dict(kind='lih-wang'),r['certificate']))
        self.assertIsNone(m.replay(s,dict(r['certificate'],matrix=[['1e999999999',0,0],[0,1,0],[0,0,1]])))
        cert=dict(r['certificate'],intervals=[['0','1/4']]);self.assertIsNone(m.replay(s,cert))
        g=auto_discharge(new(m.statement(s)));self.assertIn('goal',closure(g));self.assertEqual(audit(g)['status'],'proved')
    def test_universal_never_proved(self):
        s=dict(kind='lih-wang');r=m.solve(s,budget=12);self.assertIn(r['status'],('unknown','counterexample'))
        self.assertFalse(m.prefix_bridge(m.statement(s),m.statement(dict(kind='signed-prefix',matrix=m.encode(self.a)))))
        g=auto_discharge(new(m.statement(s)))
        if r['status']=='unknown':
            self.assertNotIn('goal',closure(g));self.assertTrue(any(e['rule']=='accepted' for e in g['edges'].values()));self.assertEqual(audit(g)['status'],'unverified')
    def test_transport(self):
        import random
        rng=random.Random(3);a=self.a
        for _ in range(20):
            a=m.cycle_move(a,rng);self.assertEqual(m.matrix(m.encode(a)),a)
    def test_validation(self):
        for a in ([[1,0,0],[0,1,0],[0,1,0]],[[1.0,0,0],[0,1,0],[0,0,1]]):self.assertRaises(ValueError,m.matrix,a)
        self.assertRaises(ValueError,m.solve,dict(kind='lih-wang'),0)
        self.assertRaises(ValueError,apply,new('target'),[dict(op='observe',id='matrix-fake',focus='goal',kind='proof_sketch',detail='fake')])
    def test_prefix_bridge_fixed_scope(self):
        s=dict(kind='lih-wang',matrix=m.encode(self.a));p=dict(s,kind='signed-prefix')
        self.assertTrue(m.prefix_bridge(m.statement(s),m.statement(p)))
        self.assertFalse(m.prefix_bridge(m.statement(p),m.statement(s)))
        self.assertEqual(m.solve(p)['status'],'proved')
