import unittest,itertools
import capacity as c
from theorem_transfer import RULE,search,replay,power_graph,auto_transfer
from discovery import new,apply,closure


def spec(n,es,t):return dict(n=n,edges=[list(e) for e in es],upper=t)
def cycle(t='9/4'):return spec(5,[(0,1),(1,2),(2,3),(3,4),(0,4)],t)
def state(a,b,edge=True):
    ops=[dict(op='claim',id='aux',statement=c.statement(b))]
    if edge:ops.append(dict(op='derive',id='bridge',parent='goal',premises=['aux'],argument='candidate'))
    return apply(new(c.statement(a)),ops)

class TransferTests(unittest.TestCase):
    def test_map(self):
        a=spec(3,[(0,1)],2);b=spec(2,[],2);r=search(a,b);self.assertEqual(r['status'],'proved_bridge');self.assertTrue(replay(a,b,r['certificate']))
    def test_power_identity(self):
        a=cycle();n,e=power_graph(a,2);b=spec(n,e,'81/16');cert=dict(rule=RULE,power=2,mapping=list(range(n)));self.assertTrue(replay(a,b,cert));self.assertFalse(replay(a,dict(b,upper='82/16'),cert))
    def test_power_search(self):
        a=spec(2,[],2);b=spec(4,[],4);r=search(a,b);self.assertEqual(r['certificate']['power'],2);self.assertTrue(replay(a,b,r['certificate']))
    def test_wrong_direction(self):
        a=spec(3,[],2);b=spec(2,[],2);self.assertEqual(search(a,b)['status'],'unknown')
    def test_bad_map(self):
        a=spec(2,[],2);b=spec(2,[],2);self.assertFalse(replay(a,b,dict(rule=RULE,power=1,mapping=[0,0])));self.assertFalse(replay(a,b,dict(rule=RULE,power=1,mapping=[False,1])))
    def test_edge_not_nonedge(self):self.assertFalse(replay(spec(2,[],2),spec(2,[(0,1)],1),dict(rule=RULE,power=1,mapping=[0,1])))
    def test_bound_mismatch(self):self.assertFalse(replay(spec(2,[],1),spec(2,[],2),dict(rule=RULE,power=1,mapping=[0,1])))
    def test_conditional(self):
        g=state(spec(3,[(0,1)],2),spec(2,[],2));h=auto_transfer(g);self.assertEqual(h['edges']['bridge']['rule'],'accepted');self.assertNotIn('goal',closure(h));self.assertEqual(auto_transfer(h),h)
        h=apply(h,[dict(op='review_claim',id='aux',decision='established',evidence='empty graph capacity = order')],trusted=True);self.assertIn('goal',closure(h))
    def test_reuse_detached(self):
        g=state(spec(3,[(0,1)],2),spec(2,[],2),False);g=apply(g,[dict(op='review_claim',id='aux',decision='established',evidence='empty graph capacity = order')],trusted=True);h=auto_transfer(g);self.assertIn('goal',closure(h));self.assertEqual(len(h['edges']),1)
    def test_unreviewed_detached(self):
        g=state(spec(3,[(0,1)],2),spec(2,[],2),False);self.assertEqual(auto_transfer(g),g)
    def test_failed_cached(self):
        g=state(spec(3,[],2),spec(2,[],2));h=auto_transfer(g);self.assertEqual(h['edges']['bridge']['rule'],'candidate');self.assertEqual(auto_transfer(h),h)
    def test_budget(self):self.assertEqual(search(spec(3,[],2),spec(2,[],2),1)['tested'],1)
    def test_reserved(self):self.assertRaises(ValueError,apply,new('target'),[dict(op='observe',id='theorem-fake',focus='goal',kind='experiment',detail='fake')])
