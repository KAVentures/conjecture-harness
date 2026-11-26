import itertools,random,unittest,copy
from math import prod
import graph_nonlinear as gn
import graph_nonlinear_basis as gb
import graph_nonlinear_lab as lab
from discovery import new,apply
from proof_audit import audit

def spec(v,t,props=None):return dict(min_n=1,properties=props or [],variables=v,terms=t)

class GraphNonlinearTests(unittest.TestCase):
    def test_graph_basis(self):
        rng=random.Random(631);graphs=checks=0
        for n in range(1,10):
            pairs=list(itertools.combinations(range(n),2))
            masks=range(1<<len(pairs)) if n<=5 else [rng.getrandbits(len(pairs)) for _ in range(60)]
            for mask in masks:
                a=[0]*n
                for j,(u,v) in enumerate(pairs):
                    if mask>>j&1:a[u]|=1<<v;a[v]|=1<<u
                alpha=omega=0
                for s in range(1,1<<n):
                    k=s.bit_count()
                    if all(not(a[i]&s) for i in range(n) if s>>i&1):alpha=max(alpha,k)
                    if all((a[i]&s).bit_count()==k-1 for i in range(n) if s>>i&1):omega=max(omega,k)
                ds=[x.bit_count() for x in a];v=dict(n=n,m=mask.bit_count(),alpha=alpha,omega=omega,delta=min(ds),Delta=max(ds));graphs+=1
                for row in gb.basis(['triangle_free'] if omega<=2 else []).values():
                    self.assertGreaterEqual(sum(c*prod(v[i] for i in e) for e,c in row.items()),0);checks+=1
        self.assertEqual(graphs,1339);self.assertEqual(checks,12506)
    def test_mantel_and_hypotheses(self):
        s=spec(['n','m'],[[[2,0],1],[[0,1],-4]],['triangle_free'])
        r=gn.solve(s);self.assertEqual(r['status'],'proved')
        self.assertEqual(gn.replay(s,r['certificate']),'proved')
        self.assertIsNone(gn.replay(dict(s,properties=[]),r['certificate']))
        self.assertEqual(audit(lab.auto_discharge(new(gn.statement(s))))['status'],'proved')
    def test_combined(self):
        s=spec(['n','m','alpha','Delta'],[[[0,0,1,1],1],[[0,0,1,0],1],[[0,1,0,0],1],[[1,0,0,0],-1],[[0,0,0,1],-1]])
        r=gn.solve(s);self.assertEqual(r['status'],'proved')
        self.assertEqual(gn.replay(s,r['certificate']),'proved')
        self.assertGreaterEqual(len(r['certificate']['rows']),2)
        bad=copy.deepcopy(r['certificate']);bad['rows'][0]='unknown'
        self.assertIsNone(gn.replay(s,bad))
    def test_unknown_not_refuted_and_reserved(self):
        self.assertEqual(gn.solve(spec(['n'],[[[1],-1]]),pivot_budget=8)['status'],'unknown')
        with self.assertRaises(ValueError):apply(new('x'),[dict(op='observe',id='graph-polynomial-fake',focus='goal',kind='proof_sketch',detail='fake')])
