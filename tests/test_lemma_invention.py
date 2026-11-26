import copy, unittest
from fractions import Fraction as F
import polynomial as p
from lemma_invention import invent,replay,auto_invent
from discovery import new,apply,closure
from discovery_run import auto_discharge
from hypothesis import sum_bridge


def target(a=4,b=2,c=1):
    # a(x²-y²)²+(bxy+cy)²
    return dict(variables=['x','y'],domain='real',relation='nonnegative',terms=[[[4,0],a],[[0,4],a],[[2,2],b*b-2*a],[[1,2],2*b*c],[[0,2],c*c]])

class InventionTests(unittest.TestCase):
    def test_target_only(self):
        s=target();self.assertEqual(p.solve(s)['status'],'unknown');r=invent(s);self.assertEqual(r['status'],'proved');self.assertTrue(replay(s,r));self.assertTrue(sum_bridge(s,r['parts']))
    def test_auto_state(self):
        g=new(p.statement(target()));h=auto_discharge(g);self.assertIn('goal',closure(h));self.assertEqual(len(h['edges']),1);self.assertEqual(len(h['nodes']),3);self.assertEqual(h['nodes']['goal']['statement'],g['nodes']['goal']['statement']);self.assertEqual(auto_discharge(h),h)
        e=next(iter(h['edges'].values()));self.assertTrue(all(h['nodes'][i]['status']=='established' for i in e['premises']))
    def test_no_invent_before_abstention(self):
        g=new(p.statement(target()));self.assertEqual(auto_invent(g),g)
    def test_tampered_weight(self):
        s=target();r=invent(s);r['certificates'][0]['squares'][0][0]='-1';self.assertFalse(replay(s,r))
    def test_tampered_part(self):
        s=target();r=invent(s);r['parts'][1]['terms'][0][1]='0';self.assertFalse(replay(s,r))
    def test_domain_mismatch(self):
        s=target();r=invent(s);r['parts'][0]['domain']='nonnegative';self.assertFalse(replay(s,r))
    def test_false_target(self):
        s=target();s['terms'].append([[0,0],-1]);self.assertEqual(invent(s)['status'],'unknown');h=auto_discharge(new(p.statement(s)));self.assertEqual(h['nodes']['goal']['status'],'refuted')
    def test_unknown_not_proof(self):
        s=dict(variables=['x','y'],domain='real',relation='nonnegative',terms=[[[4,2],1],[[2,4],1],[[2,2],-3],[[0,0],1]])
        r=invent(s);self.assertEqual(r['status'],'unknown');self.assertFalse(replay(s,r));g=auto_discharge(new(p.statement(s)));self.assertNotIn('goal',closure(g));self.assertEqual(auto_discharge(g),g)
    def test_existing_route_preserved(self):
        g=apply(new(p.statement(target())),[dict(op='claim',id='aux',statement='Unrelated candidate'),dict(op='derive',id='edge',parent='goal',premises=['aux'],argument='candidate')]);h=auto_discharge(g);self.assertNotIn('goal',closure(h));self.assertEqual(set(h['edges']),{'edge'})
    def test_reserved_evidence(self):
        with self.assertRaises(ValueError):apply(new('target'),[dict(op='observe',id='invent-fake',focus='goal',kind='experiment',detail='fake')])
    def test_point_not_proof(self):
        s=target();r=invent(s);r['certificates'][0]={'kind':'point','point':['0','0']};self.assertFalse(replay(s,r))
    def test_budget(self):
        s=target();r=invent(s,1);self.assertLessEqual(r['tested'],1)
        for b in (0,True,513):self.assertRaises(ValueError,invent,s,b)
    def test_unsupported(self):
        s=target();s['relation']='zero';self.assertEqual(invent(s)['status'],'unknown')
    def test_fractional_coefficients(self):
        s=target(F(4,3),F(2,3),F(1,3));s['terms']=[[e,str(v)] for e,v in s['terms']];r=invent(s);self.assertTrue(replay(s,r))
