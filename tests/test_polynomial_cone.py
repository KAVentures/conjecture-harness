import random,unittest,copy
from fractions import Fraction as Q
import rational_cone as rc
import polynomial_cone as pc
import conditional_theorems as ct
from conditional_lab import auto_discharge
from discovery import new
from proof_audit import audit

class ConeTests(unittest.TestCase):
    def test_exact_feasibility(self):
        rng=random.Random(423)
        for _ in range(300):
            m=rng.randint(1,8);n=rng.randint(1,12)
            cols=[{k:Q(rng.randint(-5,5),rng.randint(1,4)) for k in range(m)} for _ in range(n)]
            w=[Q(rng.randint(0,5),rng.randint(1,4)) for _ in cols]
            t={k:sum(v*c[k] for v,c in zip(w,cols)) for k in range(m)}
            x,_=rc.solve(cols,t)
            self.assertIsNotNone(x);self.assertTrue(all(v>=0 for v in x))
            self.assertEqual({k:sum(v*c[k] for v,c in zip(x,cols)) for k in t},t)
        for _ in range(100):
            cols=[{0:rng.randint(0,5),1:rng.randint(-5,5)} for j in range(5)]
            self.assertIsNone(rc.solve(cols,{0:-1,1:rng.randint(-5,5)})[0])
    def test_three_products(self):
        s=dict(variables=['x','y','z'],domain='real',assumptions=[dict(relation='nonnegative',terms=[[e,1]]) for e in ([1,0,0],[0,1,0],[0,0,1])],conclusion=[[[1,1,0],1],[[1,0,1],1],[[0,1,1],1]])
        r=ct.solve(s);self.assertEqual(r['status'],'proved')
        self.assertEqual(ct.replay(s,r['certificate']),'proved')
        self.assertGreaterEqual(len(r['certificate']['multipliers']),3)
        bad=copy.deepcopy(r['certificate']);bad['multipliers'].pop()
        self.assertIsNone(ct.replay(s,bad))
        self.assertEqual(audit(auto_discharge(new(ct.statement(s))))['status'],'proved')
    def test_generated_identities(self):
        rng=random.Random(74)
        for _ in range(60):
            a=[{(1,0):Q(1),(0,0):Q(-rng.randint(0,3))},{(0,1):Q(1),(0,0):Q(-rng.randint(0,3))}]
            rel=['nonnegative']*2;t={}
            for q in [a[0],a[1],pc.mul(a[0],a[1])]:
                w=Q(rng.randint(1,5),rng.randint(1,3))
                for e,v in q.items():t[e]=t.get(e,Q(0))+w*v
            t={e:c for e,c in t.items() if c}
            def encode(q):return [[list(e),str(c)] for e,c in q.items() if c]
            s=dict(variables=['x','y'],domain='real',assumptions=[dict(relation=r,terms=encode(q)) for r,q in zip(rel,a)],conclusion=encode(t))
            cert,_=pc.search(a,rel,t,2,'real')
            self.assertIsNotNone(cert)
            self.assertEqual(ct.replay(s,cert),'proved')
    def test_equality_and_domain(self):
        a=[{(1,0):Q(1),(0,1):Q(-1)}];t={(1,0):Q(-1),(0,1):Q(1)}
        s=dict(variables=['x','y'],domain='real',assumptions=[dict(relation='zero',terms=[[[1,0],1],[[0,1],-1]])],conclusion=[[[1,0],-1],[[0,1],1]])
        c,_=pc.search(a,['zero'],t,2,'real');self.assertEqual(ct.replay(s,c),'proved')
        c,_=pc.search(a,['nonnegative'],t,2,'real');self.assertIsNone(c)


    def test_degree_pruning_and_exact_input(self):
        from unittest.mock import patch
        from math import comb
        for n in range(1,5):
            for d in range(9):
                es=list(pc.monomials(n,d))
                self.assertEqual(len(es),comb(n+d,n))
                self.assertEqual(len(es),len(set(es)))
                self.assertTrue(all(sum(e)<=d for e in es))
        high=[{(8,0):Q(1)}, {(0,8):Q(1)}]
        original=pc.mul
        def bounded(a,b):
            self.assertLessEqual(max(map(sum,a))+max(map(sum,b)),8)
            return original(a,b)
        with patch.object(pc,'mul',side_effect=bounded):
            cert,_=pc.search(high,['nonnegative','nonnegative'],{(8,0):Q(1),(0,8):Q(1)},2,'real')
        self.assertIsNotNone(cert)
        with self.assertRaises(ValueError):rc.solve([{0:0.1}],{0:1})
        self.assertEqual(rc.solve([{0:1<<300}],{0:1}), (None,0))
        self.assertEqual(rc.solve([{i:0 for i in range(1000)}],{}),([Q(0)],0))
