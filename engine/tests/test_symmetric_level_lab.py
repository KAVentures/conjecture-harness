import copy
import unittest
from fractions import Fraction as Q
import symmetric_level_lab as m
from discovery import new,apply,prompt,plan
from discovery_run import auto_discharge
from proof_audit import audit
from knowledge_bank import export
from proof_bundle import export as bundle_export,replay as bundle_replay

class SymmetricLevelTests(unittest.TestCase):
    def test_equal_level_reduction(self):
        # Cauchy: sum x_i^2 >= 1/n for x in the n-simplex.
        s=dict(dimension=24,terms=[[[1,0,0],1],[[0,0,0],' -1/24'.strip()]])
        r=m.solve(s);self.assertEqual(r['status'],'proved')
        self.assertEqual(r['levels'],1)
        self.assertEqual(r['tested'],24)
        self.assertEqual(m.replay(s,r['certificate']),'proved')
        bad=copy.deepcopy(r['certificate']);bad['charts'].pop()
        self.assertIsNone(m.replay(s,bad))
        self.assertIsNone(m.replay(dict(s,dimension=25),r['certificate']))

    def test_two_level_stationarity(self):
        # p3 >= p2^2 (weighted Cauchy) for every nonnegative simplex point.
        s=dict(dimension=12,terms=[[[0,1,0],1],[[2,0,0],-1]])
        r=m.solve(s);self.assertEqual(r['status'],'proved')
        self.assertEqual(r['levels'],2)
        self.assertTrue(any(len(row[0])==2 for row in r['certificate']['charts']))
        self.assertEqual(m.replay(s,r['certificate']),'proved')
        bad=copy.deepcopy(r['certificate']);bad['charts'][-1][0].reverse()
        if bad!=r['certificate']:self.assertIsNone(m.replay(s,bad))

    def test_secondary_extremum(self):
        # Nonconstant top derivative: cannot use the k-1 shortcut.
        s=dict(dimension=8,terms=[[[2,0,0],1],[[1,0,0],-1],[[0,0,0],'1/4']])
        self.assertEqual(m.levels(s),2)
        r=m.solve(s);self.assertEqual(r['status'],'proved')
        self.assertEqual(m.replay(s,r['certificate']),'proved')

    def test_three_level_coverage(self):
        # p4 >= 0; top derivative constant -> three levels.
        s=dict(dimension=6,terms=[[[0,0,1],1]])
        self.assertEqual(m.levels(s),3)
        r=m.solve(s);self.assertEqual(r['status'],'proved')
        self.assertTrue(any(len(row[0])==3 for row in r['certificate']['charts']))
        self.assertEqual(m.replay(s,r['certificate']),'proved')

    def test_exact_refutation_and_scope(self):
        s=dict(dimension=5,terms=[[[1,0,0],1],[[0,0,0],' -1/4'.strip()]])
        r=m.solve(s);self.assertEqual(r['status'],'counterexample')
        self.assertEqual(m.replay(s,r['certificate']),'refuted')
        self.assertIsNone(m.replay(dict(s,dimension=4),r['certificate']))
        bad=dict(kind='point',point=['-1','1','1','0','0'])
        self.assertIsNone(m.replay(s,bad))

    def test_chart_identity_and_weighted_degree(self):
        s=dict(dimension=9,terms=[[[1,1,0],3],[[0,0,1],-2]])
        y=[Q(1,3),Q(1,4),Q(5,12)];counts=(1,2,4)
        q=m.chart_poly(s,counts);x=m.lift(9,counts,y)
        self.assertEqual(m.p.value(q,y),m.point_value(s,x))
        with self.assertRaises(ValueError):
            m.normalize(dict(dimension=3,terms=[[[0,0,2],1]]))

    def test_graph_audit_and_portability(self):
        text=m.statement(dict(dimension=7,terms=[[[1,0,0],1],[[0,0,0],'-1/7']]))
        g=auto_discharge(new(text))
        self.assertEqual(audit(g)['status'],'proved')
        self.assertTrue(any(f['prefix']=='symmetric-level-' for f in export(g)['facts']))
        self.assertTrue(bundle_replay(bundle_export(g),text))
        self.assertIn('Symmetric simplex moment inequality',prompt(new(text),plan(new(text))))
        with self.assertRaises(ValueError):
            apply(new(text),[dict(op='observe',id='symmetric-level-fake',focus='goal',kind='proof_sketch',detail='fake')])

    def test_budget_not_proof(self):
        s=dict(dimension=64,terms=[[[0,0,1],1]])
        with self.assertRaises(OverflowError):m.charts(s)
        self.assertEqual(m.solve(s)['status'],'unknown')
