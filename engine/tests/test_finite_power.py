import itertools,unittest,copy
from finite_power import statement,parse_statement,search,replay,packing,transitive,find_symmetry
from discovery import new,apply,closure
from discovery_run import auto_discharge


def spec(n,e,k,b):return dict(n=n,edges=[list(x) for x in e],power=k,upper=b)


def t5(k,b):
    v=list(itertools.combinations(range(5),2));s=spec(10,[(i,j) for i,j in itertools.combinations(range(10),2) if set(v[i])&set(v[j])],k,b)
    ps=[]
    for pair in v:
        a=list(pair)+[j for j in range(5) if j not in pair];ps.append([v.index(tuple(sorted((a[x],a[y])))) for x,y in v])
    return s,ps

class FinitePowerTests(unittest.TestCase):
    def test_t5_exact(self):
        s,ps=t5(2,5);r=search(s,2000,ps);self.assertEqual(r['status'],'proved');self.assertTrue(replay(s,r['certificate']));self.assertEqual(r['nodes'],52)
        s=dict(s,upper=4);r=search(s,2000,ps);self.assertEqual(r['status'],'counterexample');self.assertEqual(len(r['witness']),5);self.assertTrue(packing(s,r['witness']))
    def test_t5_budget_comparison(self):
        s,ps=t5(2,5);self.assertEqual(search(s,2000)['status'],'unknown');self.assertEqual(search(s,1,ps)['status'],'unknown')
    def test_cycle_square(self):
        s=spec(5,[(0,1),(1,2),(2,3),(3,4),(0,4)],2,5);r=search(s,2000);self.assertEqual(r['status'],'proved');self.assertTrue(replay(s,r['certificate']));self.assertEqual(search(dict(s,upper=4))['status'],'counterexample')
    def test_all_small_graphs(self):
        for n in range(1,5):
            pairs=list(itertools.combinations(range(n),2))
            for mask in range(1<<len(pairs)):
                es={e for i,e in enumerate(pairs) if mask>>i&1};a=max(len(v) for k in range(n+1) for v in itertools.combinations(range(n),k) if not any(e in es for e in itertools.combinations(v,2)))
                s=spec(n,sorted(es),1,a);r=search(s);self.assertEqual(r['status'],'proved');self.assertTrue(replay(s,r['certificate']));self.assertEqual(search(dict(s,upper=a-1))['status'],'counterexample')
    def test_symmetry_invalid(self):
        s=spec(3,[(0,1)],1,2);ps=[[0,1,2],[1,0,2],[2,1,0]];self.assertFalse(transitive(s,ps));self.assertRaises(ValueError,search,s,2000,ps)
    def test_tamper_symmetry(self):
        s,ps=t5(2,5);c=search(s,2000,ps)['certificate'];c['permutations'][0]=[0]*10;self.assertFalse(replay(s,c))
    def test_tamper_missing_branch(self):
        s,ps=t5(2,5);c=search(s,2000,ps)['certificate'];c['tree']['branches'].pop();self.assertFalse(replay(s,c))
    def test_tamper_coloring(self):
        s=spec(3,[(0,1),(0,2),(1,2)],1,1);c=search(s)['certificate'];c['tree']['colors'][0].pop();self.assertFalse(replay(s,c))
        s=spec(2,[],1,1);self.assertFalse(replay(s,{'permutations':None,'tree':{'colors':[[0,1]]}}))
    def test_packing(self):
        s=spec(2,[],2,2);self.assertTrue(packing(s,[[0,0],[0,1],[1,0]]));self.assertFalse(packing(s,[[0,0],[0,0]]));self.assertFalse(packing(s,[[0,2]]))
    def test_invalid(self):
        s=spec(3,[],2,3);self.assertEqual(parse_statement(statement(s)),s)
        for q in (dict(s,power=8),dict(s,upper=True),dict(s,edges=[[0,0]])):self.assertRaises(ValueError,statement,q)
    def test_graph_binding(self):
        s=spec(3,[(0,1)],1,2);g=apply(new('Original universal theorem'),[dict(op='claim',id='aux',statement=statement(s)),dict(op='derive',id='edge',parent='goal',premises=['aux'],argument='candidate')]);h=auto_discharge(g);self.assertIn('aux',closure(h));self.assertNotIn('goal',closure(h));self.assertEqual(auto_discharge(h),h)
    def test_refuted_finite_claim(self):
        g=new(statement(spec(2,[],2,2)));h=auto_discharge(g);self.assertEqual(h['nodes']['goal']['status'],'refuted')
    def test_reserved(self):
        self.assertRaises(ValueError,apply,new('Target'),[dict(op='observe',id='finite-power-fake',focus='goal',kind='experiment',detail='fake')])
    def test_automatic_symmetry(self):
        s,_=t5(2,5);ps=find_symmetry(s);self.assertTrue(transitive(s,ps));self.assertIsNone(find_symmetry(s,1));self.assertIsNone(find_symmetry(spec(3,[(0,1)],1,2)))
        self.assertIn('goal',closure(auto_discharge(new(statement(s)))))
