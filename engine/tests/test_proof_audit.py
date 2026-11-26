import unittest,copy,json
from discovery import new,apply,closure
from discovery_run import auto_discharge
import polynomial as p,capacity as c,affine
from proof_audit import audit
from test_recursive_invention import target

class AuditTests(unittest.TestCase):
    def test_direct_proof(self):
        s=p.statement(dict(variables=['x'],domain='real',relation='nonnegative',terms=[[[2],1]]));g=auto_discharge(new(s));self.assertEqual(audit(g)['status'],'proved')
    def test_direct_refutation(self):
        s=p.statement(dict(variables=['x'],domain='real',relation='nonnegative',terms=[[[0],-1]]));self.assertEqual(audit(auto_discharge(new(s)))['status'],'refuted')
    def test_manual_review_not_proof(self):
        g=apply(new('Goal'),[dict(op='review_claim',id='goal',decision='established',evidence='manual')],trusted=True);r=audit(g);self.assertEqual(r['status'],'unverified');self.assertEqual(r['unverified_recorded_claims'],['goal'])
    def test_tampered_certificate(self):
        s=p.statement(dict(variables=['x'],domain='real',relation='nonnegative',terms=[[[2],1]]));g=auto_discharge(new(s));o=next(iter(g['observations'].values()));r=json.loads(o['detail']);r['certificate']['monomials'][0][1]='2';o['detail']=json.dumps(r);a=audit(g);self.assertEqual(a['status'],'unverified');self.assertEqual(len(a['invalid_observations']),1)
    def test_recursive(self):self.assertEqual(audit(auto_discharge(new(p.statement(target()))))['status'],'proved')
    def test_capacity(self):self.assertEqual(audit(auto_discharge(new(c.statement(dict(n=2,edges=[[0,1]],upper=1)))))['status'],'proved')
    def test_affine(self):self.assertEqual(audit(auto_discharge(new(affine.statement(dict(variables=['x'],assumptions=[[0,1]],conclusion=[0,2])))))['status'],'proved')
    def test_additive_bridge(self):
        def s(ts):return p.statement(dict(variables=['x'],domain='real',relation='nonnegative',terms=ts))
        g=apply(new(s([[[2],1],[[0],1]])),[dict(op='claim',id='a',statement=s([[[2],1]])),dict(op='claim',id='b',statement=s([[[0],1]])),dict(op='derive',id='e',parent='goal',premises=['a','b'],argument='sum'),dict(op='review_edge',id='e',decision='accepted',evidence='manual')],trusted=True)
        # Direct solver can also prove target; prove only the two premises first.
        from polynomial_lab import discharge
        for i in ('a','b'):g,_=discharge(g,i,p.parse_statement(g['nodes'][i]['statement']))
        self.assertEqual(audit(g)['status'],'proved');self.assertEqual(audit(g)['proved']['goal'],'e')
    def test_unverified_premise(self):
        def s(ts):return p.statement(dict(variables=['x'],domain='real',relation='nonnegative',terms=ts))
        g=apply(new(s([[[0],-1],[[2],1]])),[dict(op='claim',id='a',statement=s([[[0],-1]])),dict(op='claim',id='b',statement=s([[[2],1]])),dict(op='derive',id='e',parent='goal',premises=['a','b'],argument='sum'),dict(op='review_edge',id='e',decision='accepted',evidence='manual'),dict(op='review_claim',id='a',decision='established',evidence='false manual claim'),dict(op='review_claim',id='b',decision='established',evidence='manual')],trusted=True)
        self.assertIn('goal',closure(g));self.assertEqual(audit(g)['status'],'unverified')
    def test_read_only(self):
        g=auto_discharge(new(c.statement(dict(n=2,edges=[[0,1]],upper=1))));h=copy.deepcopy(g);audit(g);self.assertEqual(g,h)
    def test_graph_witness(self):
        import graph_lemma,lemma_lab
        s=dict(min_n=2,properties=[],coefficients={'alpha':1},constant=2);g,_=lemma_lab.falsify(new(graph_lemma.statement(s)),'goal',s);self.assertEqual(audit(g)['status'],'refuted')
        o=next(iter(g['observations'].values()));r=json.loads(o['detail']);r['spec']['constant']=3;o['detail']=json.dumps(r);self.assertEqual(audit(g)['status'],'unverified')
    def test_finite(self):
        import finite_power
        s=finite_power.statement(dict(n=2,edges=[],power=2,upper=4));self.assertEqual(audit(auto_discharge(new(s)))['status'],'proved')
    def test_transfer(self):
        from theorem_transfer import auto_transfer
        a=c.statement(dict(n=3,edges=[[0,1]],upper=2));b=c.statement(dict(n=2,edges=[],upper=2));g=apply(new(a),[dict(op='claim',id='a',statement=b),dict(op='derive',id='e',parent='goal',premises=['a'],argument='map')]);g=auto_transfer(g)
        from capacity_lab import auto_discharge as solve
        # The direct solver may close the goal, so record only the premise certificate.
        from discovery import record
        r=c.solve(c.parse_statement(b));g=record(g,'forward','a',[dict(op='observe',id='capacity-fixture',focus='a',kind='proof_sketch',detail=json.dumps(r)),dict(op='review_claim',id='a',decision='established',evidence='certificate fixture')],trusted=True)
        self.assertEqual(audit(g)['proved']['goal'],'e')
