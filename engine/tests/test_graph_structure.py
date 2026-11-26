import itertools,random,unittest,copy
import graph_structure as gs
import graph_structure_lab as lab
from discovery import new,apply,closure
from proof_audit import audit

def spec(n,edges,k,invariant='alpha'):
    return dict(n=n,edges=[list(e) for e in edges],upper=k,invariant=invariant)

def brute(n,edges,invariant):
    es=set(map(tuple,edges))
    return max(len(v) for k in range(n+1) for v in itertools.combinations(range(n),k) if all((e in es)==(invariant=='omega') for e in itertools.combinations(v,2)))

class GraphStructureTests(unittest.TestCase):
    def test_exact_random(self):
        rng=random.Random(479)
        for n in range(1,9):
            for _ in range(20):
                edges=[e for e in itertools.combinations(range(n),2) if rng.random()<.5]
                for inv in ('alpha','omega'):
                    k=brute(n,edges,inv)
                    for bound,outcome in ((k,'proved'),(k-1,'refuted')):
                        s=spec(n,edges,bound,inv);r=gs.solve(s)
                        self.assertEqual(r['status'],outcome)
                        self.assertEqual(gs.replay(s,r['certificate']),outcome)
    def test_odd_cycle_branch(self):
        s=spec(5,[(0,1),(1,2),(2,3),(3,4),(0,4)],2)
        r=gs.solve(s);self.assertEqual(r['status'],'proved')
        self.assertIn('branch',[row[1] for row in r['certificate']['rows']])
        self.assertIsNone(gs.replay(dict(s,upper=1),r['certificate']))
        bad=copy.deepcopy(r['certificate']);bad['rows'][-1][2]=99
        self.assertIsNone(gs.replay(s,bad))
        self.assertEqual(gs.solve(s,budget=1)['status'],'unknown')
    def test_component_certificate(self):
        edges=[(i,j) for i,j in itertools.combinations(range(10),2) if i//5==j//5 and ((j-i)%5 in (1,4))]
        s=spec(10,edges,4);r=gs.solve(s)
        self.assertEqual(r['status'],'proved')
        self.assertEqual(r['certificate']['rows'][-1][1],'components')
    def test_audit_and_reserved(self):
        s=spec(5,[(0,1),(1,2),(2,3),(3,4),(0,4)],2)
        g=lab.auto_discharge(new(gs.statement(s)))
        self.assertIn('goal',closure(g));self.assertEqual(audit(g)['status'],'proved')
        self.assertEqual(audit(lab.auto_discharge(new(gs.statement(dict(s,upper=1)))))['status'],'refuted')
        with self.assertRaises(ValueError):apply(new('x'),[dict(op='observe',id='structure-fake',focus='goal',kind='proof_sketch',detail='fake')])
