import unittest
from fractions import Fraction as Q
from itertools import product
import moment_chart_lab as m
from discovery import new,apply,prompt,plan
from discovery_run import auto_discharge
from proof_audit import audit
from knowledge_bank import export
from proof_bundle import export as bundle_export,replay as bundle_replay

def spec(terms,domain='probability'):return dict(domain=domain,terms=terms)

class MomentChartTests(unittest.TestCase):
    def test_exact_atomic_realization(self):
        for a,b,c in product((Q(0),Q(1,5),Q(1,2),Q(4,5),Q(1)),repeat=3):
            atoms=m.atomic(a,b,c)
            self.assertEqual(sum(w for x,w in atoms),1)
            self.assertTrue(all(0<=x<=1 and w>0 for x,w in atoms))
            self.assertEqual(m.moments(atoms),m.chart_moments(a,b,c))

    def test_chart_polynomial_identity(self):
        s=spec([[[1,0,1],3],[[0,2,0],-2],[[0,0,1],1]])
        q=m.chart_poly(s)
        for x in product((Q(1,5),Q(3,4)),repeat=3):
            self.assertEqual(m.p.value(q,x),m.objective(s,m.chart_moments(*x)))

    def test_dimension_free_log_convexity(self):
        for terms in ([[[0,1,0],1],[[2,0,0],-1]],
                      [[[1,0,1],1],[[0,2,0],-1]]):
            for domain in ('probability','simplex'):
                s=spec(terms,domain);r=m.solve(s)
                self.assertEqual(r['status'],'proved')
                self.assertEqual(m.replay(s,r['certificate']),'proved')

    def test_upper_moment_determinant(self):
        # (1-m1)(m2-m3)-(m1-m2)^2 >= 0.
        s=spec([[[0,1,0],1],[[0,0,1],-1],[[1,1,0],1],
                [[1,0,1],1],[[2,0,0],-1],[[0,2,0],-1]])
        r=m.solve(s);self.assertEqual(r['status'],'proved')
        self.assertEqual(m.replay(s,r['certificate']),'proved')

    def test_no_false_transfer_of_relaxation_counterexample(self):
        # m1-m2 <= 1/4 is true in both, but a negative witness for
        # any probability claim must not automatically refute simplex.
        s=spec([[[0,0,0],'-1/8'],[[1,0,0],1],[[0,1,0],-1]])
        r=m.solve(s);self.assertEqual(r['status'],'counterexample')
        self.assertIsNone(m.replay(dict(s,domain='simplex'),r['certificate']))
        self.assertEqual(m.replay(s,r['certificate']),'refuted')
        self.assertIsNone(m.replay(s,dict(kind='moment-point',parameters=['2','0','0'])))

    def test_simplex_exact_witness(self):
        s=spec([[[1,0,0],-1],[[0,0,0],'1/2']],'simplex')
        r=m.solve(s);self.assertEqual(r['status'],'counterexample')
        self.assertEqual(m.replay(s,r['certificate']),'refuted')
        self.assertIsNone(m.replay(s,dict(kind='simplex-point',point=['-1','2'])))

    def test_graph_audit_and_portability(self):
        text=m.statement(spec([[[0,1,0],1],[[2,0,0],-1]],'simplex'))
        g=auto_discharge(new(text))
        self.assertEqual(audit(g)['status'],'proved')
        self.assertTrue(any(f['prefix']=='moment-chart-' for f in export(g)['facts']))
        self.assertTrue(bundle_replay(bundle_export(g),text))
        self.assertIn('Moment chart polynomial inequality',prompt(new(text),plan(new(text))))
        with self.assertRaises(ValueError):
            apply(new(text),[dict(op='observe',id='moment-chart-fake',focus='goal',kind='proof_sketch',detail='fake')])

    def test_bad_certificate(self):
        s=spec([[[0,1,0],1],[[2,0,0],-1]])
        r=m.solve(s);self.assertEqual(r['status'],'proved')
        self.assertIsNone(m.replay(s,dict(kind='moment-box-cover',tree=[0,None])))
        self.assertIsNone(m.replay(spec([[[0,0,0],-1]]),r['certificate']))
        with self.assertRaises(ValueError):m.normalize(spec([[[0,0,3],1]]))
