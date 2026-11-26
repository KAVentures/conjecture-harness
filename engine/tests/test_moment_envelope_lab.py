import unittest
from fractions import Fraction as Q
import moment_envelope_lab as m
from discovery import new,apply,prompt,plan
from discovery_run import auto_discharge
from proof_audit import audit
from knowledge_bank import export
from proof_bundle import export as bundle_export,replay as bundle_replay

def mean_square(mean='1/2',bound='1/4'):
    return dict(assumptions=[dict(relation='zero',terms=[[[1],1],[[0],str(-Q(mean))]])],objective=[[[2],1]],bound=bound)

class MomentEnvelopeTests(unittest.TestCase):
    def test_jensen_arbitrary_support_and_sharp(self):
        s=mean_square();r=m.solve(s)
        self.assertEqual(r['status'],'proved')
        self.assertEqual(m.replay(s,r['certificate']),'proved')
        self.assertEqual(m.atomic_value(s,r['sharpness']['atoms']),Q(1,4))
        self.assertIsNotNone(m.sharpness(s,r['certificate'],r['sharpness']['atoms']))
        self.assertIsNone(m.sharpness(s,r['certificate'],[['0','1/2'],['1','1/2']]))
        self.assertIsNone(m.replay(dict(s,bound='1/3'),r['certificate']))

    def test_nongrid_mean_and_cubic(self):
        s=mean_square('2/5','8/125');s['objective']=[[[3],1]]
        r=m.solve(s);self.assertEqual(r['status'],'proved')
        self.assertEqual(m.atomic_value(s,r['sharpness']['atoms']),Q(8,125))

    def test_exact_refutation(self):
        s=mean_square(bound='1/3');r=m.solve(s)
        self.assertEqual(r['status'],'counterexample')
        self.assertEqual(m.replay(s,r['certificate']),'refuted')
        self.assertIsNone(m.replay(s,dict(kind='point',atoms=[['0','1']])))
        self.assertIsNone(m.replay(s,dict(kind='point',atoms=[['1/2','2']])))

    def test_inequality_multiplier_and_boundary(self):
        s=dict(assumptions=[dict(relation='nonnegative',terms=[[[1],1],[[0],'-1/2']])],objective=[[[2],1]],bound='1/4')
        r=m.solve(s);self.assertEqual(r['status'],'proved')
        self.assertIn(0,r['sharpness']['active_inequalities'])
        self.assertIsNone(m.replay(s,dict(kind='envelope',multipliers=['-1'])))
        self.assertFalse(m.interval_nonnegative([Q(0),Q(-1)]))
        self.assertTrue(m.interval_nonnegative([Q(1),Q(-1)]))

    def test_discover_sharp_bound(self):
        s=mean_square(bound='0');r=m.discover_bounds(s,steps=12)
        self.assertEqual(r['status'],'sharp')
        self.assertEqual(r['lower'],'1/4')
        self.assertEqual(r['upper'],'1/4')
        self.assertEqual(m.replay(dict(s,bound=r['lower']),r['certificate']),'proved')

    def test_graph_audit_and_portability(self):
        text=m.statement(mean_square());g=auto_discharge(new(text))
        self.assertEqual(audit(g)['status'],'proved')
        self.assertTrue(any(f['prefix']=='moment-envelope-' for f in export(g)['facts']))
        self.assertTrue(bundle_replay(bundle_export(g),text))
        self.assertIn('Moment envelope inequality',prompt(new(text),plan(new(text))))
        with self.assertRaises(ValueError):
            apply(new(text),[dict(op='observe',id='moment-envelope-fake',focus='goal',kind='proof_sketch',detail='fake')])

    def test_two_contact_points(self):
        # x(1-x) >= 0, with equality at either endpoint, mean 1/2 forces a mixture.
        s=mean_square(bound='0');s['objective']=[[[1],1],[[2],-1]]
        r=m.solve(s);self.assertEqual(r['status'],'proved')
        self.assertEqual(m.atomic_value(s,r['sharpness']['atoms']),0)
        self.assertIsNone(m.sharpness(s,r['certificate'],[['1/2','1']]))
