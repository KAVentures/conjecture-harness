import unittest,itertools
from fractions import Fraction as F
from capacity import statement,parse_statement,solve,replay,replay_counterexample,psd,rank
from discovery import new,closure,apply
from discovery_run import auto_discharge


def spec(n,edges,t):return dict(n=n,edges=[list(e) for e in edges],upper=t)

def t5(t='5/2'):
    v=list(itertools.combinations(range(5),2));return spec(10,[(i,j) for i,j in itertools.combinations(range(10),2) if set(v[i])&set(v[j])],t)

class CapacityTests(unittest.TestCase):
    def test_t5(self):
        s=t5();r=solve(s);self.assertEqual(r['status'],'proved');self.assertTrue(replay(s,r['certificate']));self.assertEqual(r['certificate']['kind'],'gram')
    def test_t5_stronger_unknown(self):self.assertEqual(solve(t5('12/5'))['status'],'unknown')
    def test_cycle(self):
        s=spec(5,[(0,1),(1,2),(2,3),(3,4),(0,4)],'9/4');self.assertEqual(solve(s)['status'],'proved')
    def test_complete(self):self.assertEqual(solve(spec(4,itertools.combinations(range(4),2),1))['status'],'proved')
    def test_empty(self):self.assertEqual(solve(spec(4,[],4))['status'],'proved')
    def test_empty_refutation(self):
        s=spec(4,[],3);r=solve(s);self.assertEqual(r['status'],'counterexample');self.assertTrue(replay_counterexample(s,r['certificate']['words']))
    def test_psd(self):
        self.assertTrue(psd([[F(1),F(1)],[F(1),F(1)]]));self.assertFalse(psd([[F(0),F(1)],[F(1),F(0)]]));self.assertFalse(psd([[F(1),F(2)],[F(2),F(1)]]))
    def test_gram_tamper(self):
        s=t5();c=solve(s)['certificate'];c['matrix'][0][0]='2';self.assertFalse(replay(s,c));c=solve(s)['certificate'];c['matrix'][0][7]='1';self.assertFalse(replay(s,c))
    def test_rank(self):
        s=spec(3,[(0,1),(0,2),(1,2)],1);c=dict(kind='rank',prime=2,matrix=[[1]*3 for _ in range(3)]);self.assertTrue(replay(s,c));self.assertEqual(rank([[1,1],[1,1]],2),1);self.assertFalse(replay(dict(s,edges=[]),c));self.assertFalse(replay(s,dict(c,prime=4)))
    def test_rank_zero_diag(self):self.assertFalse(replay(spec(1,[],1),dict(kind='rank',prime=2,matrix=[[0]])))
    def test_packing(self):
        s=spec(3,[(0,1)],1);self.assertTrue(replay_counterexample(s,[[0],[2]]));self.assertFalse(replay_counterexample(s,[[0],[1]]));self.assertFalse(replay_counterexample(s,[[0],[0]]));self.assertFalse(replay_counterexample(dict(s,upper=2),[[0],[2]]))
    def test_schema(self):
        s=t5();self.assertEqual(statement(parse_statement(statement(s))),statement(s));self.assertRaises(ValueError,statement,dict(s,edges=[[0,0]]));self.assertRaises(ValueError,statement,dict(s,upper=2.5))
    def test_graph_integration(self):
        g=new(statement(t5()));h=auto_discharge(g);self.assertIn('goal',closure(h));self.assertEqual(auto_discharge(h),h)
    def test_auxiliary_only(self):
        s=spec(2,[],1);g=apply(new('Original'),[dict(op='claim',id='aux',statement=statement(s)),dict(op='derive',id='edge',parent='goal',premises=['aux'],argument='candidate')]);h=auto_discharge(g);self.assertEqual(h['nodes']['aux']['status'],'refuted');self.assertEqual(h['nodes']['goal']['status'],'open')
    def test_reserved(self):self.assertRaises(ValueError,apply,new('target'),[dict(op='observe',id='capacity-fake',focus='goal',kind='experiment',detail='fake')])
