import itertools,unittest,copy
import graph_consequences as gc
import graph_consequence_lab as lab
import graph_lemma as gl
from discovery import new,apply,closure
from proof_audit import audit

def spec(c,k=0,n=1,props=None):return dict(min_n=n,properties=props or [],coefficients=c,constant=k)

class GraphConsequenceTests(unittest.TestCase):
    def test_graph_theorem_basis_exhaustive(self):
        for n in range(1,6):
            pairs=list(itertools.combinations(range(n),2))
            for mask in range(1<<len(pairs)):
                edges=[list(e) for j,e in enumerate(pairs) if mask>>j&1]
                p=gl.properties(n,edges)
                props=[x for x in gl.PROPS if p[x]]
                for row in gc.basis(spec({'n':1},n=n,props=props)).values():
                    self.assertGreaterEqual(row[0]+sum(c*p[k] for k,c in zip(gc.FIELDS,row[1:])),0)
    def test_combined_universal_bound(self):
        s=spec({'n':1,'m':1,'omega':-1,'alpha':-1},0)
        # alpha+omega <= n+1 and m>=1 when connected n>=2.
        s=spec(s['coefficients'],n=2,props=['connected'])
        r=gc.solve(s)
        self.assertEqual(r['status'],'proved')
        self.assertEqual(gc.replay(s,r['certificate']),'proved')
        self.assertEqual(gc.parse_statement(gl.statement(s)),gl.validate(s))
        g=lab.auto_discharge(new(gl.statement(s)))
        self.assertIn('goal',closure(g));self.assertEqual(audit(g)['status'],'proved')
    def test_property_binding(self):
        s=spec({'omega':-1},-2,props=['triangle_free'])
        r=gc.solve(s);self.assertEqual(r['status'],'proved')
        self.assertIsNone(gc.replay(spec({'omega':-1},-2),r['certificate']))
        self.assertEqual(gc.solve(spec({'omega':-1},-2),budget=8)['status'],'unknown')
    def test_tampering(self):
        s=spec({'m':2,'delta':-4},n=4)
        r=gc.solve(s);self.assertEqual(r['status'],'proved')
        bad=copy.deepcopy(r['certificate']);bad['rows'][0]='invented'
        self.assertIsNone(gc.replay(s,bad))
        with self.assertRaises(ValueError):apply(new('x'),[dict(op='observe',id='graph-linear-fake',focus='goal',kind='proof_sketch',detail='fake')])
