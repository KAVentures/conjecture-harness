import copy
import unittest
from fractions import Fraction as Q
import parametric_cone_lab as m
from discovery import new,apply,prompt,plan
from discovery_run import auto_discharge
from proof_audit import audit
from knowledge_bank import export
from proof_bundle import export as bundle_export,replay as bundle_replay

class ParametricConeTests(unittest.TestCase):
    def test_signed_cancellation(self):
        # x>=0, x+y>=0. Then x+t*y>=0, including arbitrarily negative y.
        s=dict(start=0,rows=[[1,0],[1,1]],equalities=[],weights=[[[[0,0],1]],[[[0,1],1]]])
        r=m.solve(s);self.assertEqual(r['status'],'proved')
        self.assertEqual(m.replay(s,r['certificate']),'proved')
        text=m.statement(s);g=auto_discharge(new(text))
        self.assertEqual(audit(g)['status'],'proved')
        self.assertTrue(any(f['prefix']=='parametric-cone-' for f in export(g)['facts']))
        self.assertTrue(bundle_replay(bundle_export(g),text))
        self.assertIn('Parametric cone inequality',prompt(new(text),plan(new(text))))
        with self.assertRaises(ValueError):
            apply(new(text),[dict(op='observe',id='parametric-cone-fake',focus='goal',kind='proof_sketch',detail='fake')])

    def test_integer_tail_not_real_interval(self):
        # n(n-1) >=0 on nonnegative integers, not all nonnegative reals.
        s=dict(start=0,rows=[[1]],equalities=[],weights=[[[[2,0],1],[[1,0],-1]]])
        r=m.solve(s);self.assertEqual(r['status'],'proved')
        c=r['certificate'];self.assertEqual(c['offset'],1)
        self.assertEqual(m.replay(s,c),'proved')
        bad=copy.deepcopy(c);bad['prefix']=[]
        self.assertIsNone(m.replay(s,bad))
        bad=copy.deepcopy(c);bad['offset']=0
        self.assertIsNone(m.replay(s,bad))

    def test_subdivision_and_equality(self):
        # (t-1/2)^2 >=0 needs interval subdivision with degree 2.
        s=dict(start=0,rows=[[1,0]],equalities=[[1,-1]],
               weights=[[],[[[0,0],'1/4'],[[0,1],-1],[[0,2],1]]])
        r=m.solve(s);self.assertEqual(r['status'],'proved')
        c=r['certificate'];self.assertIn('split',c['tail'])
        self.assertEqual(m.replay(s,c),'proved')
        bad=copy.deepcopy(c);bad['tail']['split'].pop()
        self.assertIsNone(m.replay(s,bad))
        self.assertIsNone(m.replay(dict(s,equalities=[]),c))

    def test_exact_refutation_and_scope(self):
        s=dict(start=3,rows=[[1]],equalities=[],weights=[[[[1,0],-1]]])
        r=m.solve(s);self.assertEqual(r['status'],'counterexample')
        self.assertEqual(m.replay(s,r['certificate']),'refuted')
        bad=dict(r['certificate'],n=2)
        self.assertIsNone(m.replay(s,bad))
        self.assertIsNone(m.replay(s,dict(r['certificate'],t='2')))
        self.assertIsNone(m.replay(s,dict(r['certificate'],x=[-1])))

    def test_shifted_basis_identity(self):
        w=[{(2,2):Q(3),(1,0):Q(-2),(0,1):Q(5)}]
        l,r=Q(1,4),Q(3,4);vs=m.vectors(w,4,True,l,r)
        from math import comb
        for u in (Q(0),Q(1,3),Q(3)):
            for v in (Q(0),Q(1,5),Q(1)):
                reconstructed=sum(vs[a*3+b][0]*u**a*comb(2,b)*v**b*(1-v)**(2-b)
                                  for a in range(3) for b in range(3))
                self.assertEqual(reconstructed,m.p.value(w[0],[4+u,l+(r-l)*v]))

    def test_no_assumptions(self):
        s=dict(start=0,rows=[],equalities=[],weights=[[]])
        self.assertEqual(m.solve(s)['status'],'proved')
        s['weights']=[[[[0,0],1]]]
        self.assertEqual(m.solve(s)['status'],'counterexample')
