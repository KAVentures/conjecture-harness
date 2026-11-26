import itertools,unittest
import capacity as c
import graph_reduction as r
from discovery import new,apply,closure
from discovery_run import auto_discharge
from finite_power import graph


def spec(n,es,t='9/4'):return dict(n=n,edges=[list(e) for e in es],upper=t)
def cycle(extra):return spec(6,[(0,1),(1,2),(2,3),(3,4),(0,4)]+[(i,5) for i in extra])

def alpha(s,k):
    _,adj=graph(dict(n=s['n'],edges=s['edges'],power=k,upper=0))
    def rec(mask):
        if not mask:return 0
        v=(mask&-mask).bit_length()-1;rest=mask^(1<<v)
        return max(rec(rest),1+rec(rest&adj[v]))
    return rec((1<<len(adj))-1)

class ReductionTests(unittest.TestCase):
    def test_cycle_extensions(self):
        for extra in ([0,1,4],[0,1,2,3,4],[0,1,2,4]):
            s=cycle(extra);self.assertEqual(c.solve(s)['status'],'unknown');q=r.solve(s);self.assertEqual(q['status'],'proved');self.assertTrue(r.replay(s,q['certificate']));self.assertEqual(len(q['reduction']['subset']),5)
    def test_all_small_graphs(self):
        count=0
        for n in range(1,5):
            es=list(itertools.combinations(range(n),2))
            for mask in range(1<<len(es)):
                s=spec(n,[e for i,e in enumerate(es) if mask>>i&1]);m=r.fold(s)
                if m is None:continue
                count+=1;self.assertTrue(r.verify_map(s,m['subset'],m['mapping']));h=r.reduced(s,m['subset'])
                for k in (1,2):self.assertEqual(alpha(s,k),alpha(h,k))
        self.assertGreater(count,0)
    def test_complete_chain(self):
        s=spec(5,itertools.combinations(range(5),2),'1');m=r.fold(s);self.assertEqual(len(m['subset']),1);self.assertTrue(r.replay(s,r.solve(s)['certificate']))
    def test_empty_irreducible(self):self.assertIsNone(r.fold(spec(4,[])))
    def test_cycle_irreducible(self):self.assertIsNone(r.fold(spec(5,[(0,1),(1,2),(2,3),(3,4),(0,4)])))
    def test_nonadjacent_collapse(self):self.assertFalse(r.verify_map(spec(3,[(0,1)]),[0,1],[0,1,0]))
    def test_nonedge_to_edge(self):self.assertFalse(r.verify_map(spec(3,[(0,1)]),[0,1],[0,1,1]))
    def test_invalid_subset(self):
        for sub in ([],[1,0],[0,0],[0,1,2],[False]):self.assertFalse(r.verify_map(spec(3,[(0,1)]),sub,[0,1,0]))
    def test_tamper(self):
        s=cycle([0,1,4]);q=r.solve(s)['certificate'];q['mapping'][5]=2;self.assertFalse(r.replay(s,q));q=r.solve(s)['certificate'];q['upper_certificate']['matrix'][0][0]='2';self.assertFalse(r.replay(s,q))
    def test_lifted_refutation(self):
        s=dict(cycle([0,1,4]),upper='1');q=r.solve(s);self.assertEqual(q['status'],'counterexample');self.assertTrue(c.replay_counterexample(s,q['certificate']['words']))
    def test_graph_integration(self):
        g=new(c.statement(cycle([0,1,4])));h=auto_discharge(g);self.assertIn('goal',closure(h));self.assertTrue(any(k.startswith('graph-reduction-') for k in h['observations']));self.assertEqual(auto_discharge(h),h)
    def test_reserved(self):self.assertRaises(ValueError,apply,new('target'),[dict(op='observe',id='graph-reduction-fake',focus='goal',kind='experiment',detail='fake')])
