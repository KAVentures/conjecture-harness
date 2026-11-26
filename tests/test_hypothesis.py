import unittest
from fractions import Fraction as F
import polynomial as p
from hypothesis import add,coefficients,with_terms,repair,sum_bridge,auto_refine,auto_compose
from polynomial_lab import discharge
from discovery import new,apply,closure
from discovery_run import auto_discharge

BASE=dict(variables=['x','y'],domain='real',relation='nonnegative',terms=[])
A=with_terms(BASE,{(0,4):F(4),(2,2):F(-8),(4,0):F(4)})
B=with_terms(BASE,{(0,2):F(1),(1,2):F(4),(2,2):F(4)})
T=with_terms(BASE,add(coefficients(A),coefficients(B)))
BAD=with_terms(BASE,add(coefficients(A),{(0,0):F(-1)}))
POINT=dict(kind='point',point=['0','0'])

def state(target=T,failed=BAD):
    return apply(new(p.statement(target)),[dict(op='claim',id='aux',statement=p.statement(failed)),dict(op='derive',id='edge',parent='goal',premises=['aux'],argument='unproved candidate')])

class HypothesisTests(unittest.TestCase):
    def test_repair_exact(self):
        r=repair(T,BAD,POINT);self.assertEqual(r['shift'],'1');self.assertEqual(r['premises'],[A,B]);self.assertTrue(sum_bridge(T,r['premises']))
        self.assertTrue(p.replay(BAD,POINT));self.assertFalse(p.replay(A,POINT))
    def test_false_witness(self):
        self.assertIsNone(repair(T,BAD,dict(kind='point',point=['2','0'])))
    def test_domain_mismatch(self):
        self.assertIsNone(repair(dict(T,domain='nonnegative'),BAD,POINT));self.assertFalse(sum_bridge(T,[dict(A,domain='nonnegative'),B]))
    def test_variable_order_mismatch(self):
        self.assertFalse(sum_bridge(T,[dict(A,variables=['y','x']),B]))
    def test_wrong_sum(self):
        self.assertFalse(sum_bridge(T,[A,BAD]));self.assertFalse(sum_bridge(T,[]));self.assertFalse(sum_bridge(T,[dict(A,relation='zero'),B]))
    def test_trivial_split(self):self.assertIsNone(repair(A,BAD,POINT))
    def test_refuted_target_no_repair(self):
        g,_=discharge(new(p.statement(BAD)),'goal',BAD);self.assertEqual(auto_refine(g),g)
    def test_no_unverified_refinement(self):
        g=state();g=apply(g,[dict(op='review_claim',id='aux',decision='refuted',evidence='unreplayed manual claim')],trusted=True)
        self.assertEqual(auto_refine(g),g)
    def test_reject_tampered_witness(self):
        g,_=discharge(state(),'aux',BAD)
        import json
        o=next(iter(g['observations'].values()));r=json.loads(o['detail']);r['certificate']['point']=['2','0'];o['detail']=json.dumps(r)
        self.assertEqual(auto_refine(g),g)
    def test_refine_zero_reward(self):
        g,_=discharge(state(),'aux',BAD);h=auto_refine(g)
        self.assertEqual(h['history'][-1]['reward'],0);self.assertEqual(h['nodes']['aux']['status'],'refuted');self.assertNotIn('goal',closure(h));self.assertEqual(auto_refine(h),h)
        new=[e for i,e in h['edges'].items() if i.startswith('repair-')];self.assertEqual(len(new),1);self.assertEqual(new[0]['rule'],'candidate')
    def test_compose_not_proof_until_premises(self):
        g,_=discharge(state(),'aux',BAD);h=auto_compose(auto_refine(g));e=next(e for i,e in h['edges'].items() if i.startswith('repair-'))
        self.assertEqual(e['rule'],'accepted');self.assertNotIn('goal',closure(h));self.assertEqual(h['nodes']['aux']['status'],'refuted')
    def test_full_discovery_cycle(self):
        self.assertEqual(p.solve(T)['status'],'unknown')
        g=state();h=auto_discharge(g);self.assertNotIn('goal',closure(h));self.assertEqual(h['nodes']['aux']['status'],'refuted')
        h=auto_discharge(h);self.assertIn('goal',closure(h));self.assertEqual(h['nodes']['goal']['statement'],g['nodes']['goal']['statement']);self.assertEqual(h['nodes']['aux']['status'],'refuted')
    def test_reserved_evidence(self):
        for name in ('repair-fake','sum-fake'):
            self.assertRaises(ValueError,apply,new('Target'),[dict(op='observe',id=name,focus='goal',kind='experiment',detail='fake')])
