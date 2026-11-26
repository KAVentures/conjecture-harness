import copy,unittest
import polynomial as p
import polynomial_lab,proof_synthesis,proof_bundle as b
from discovery import new,apply,closure
from proof_audit import audit

def spec(t):return dict(variables=['x','y'],domain='real',relation='nonnegative',terms=t)
class BundleTests(unittest.TestCase):
    def graph(self):
        x=spec([[[2,0],1]]);y=spec([[[0,2],1]]);goal=spec([[[2,0],2],[[0,2],3]])
        g=new(p.statement(goal))
        g=apply(g,[dict(op='claim',id='x',statement=p.statement(x)),dict(op='claim',id='y',statement=p.statement(y)),dict(op='derive',id='route',parent='goal',premises=['x','y'],argument='Weighted sum')])
        g,_=polynomial_lab.discharge(g,'x',x)
        g,_=polynomial_lab.discharge(g,'y',y)
        return proof_synthesis.auto_discharge(g)
    def test_roundtrip(self):
        g=self.graph();self.assertEqual(audit(g)['status'],'proved')
        bundle=b.export(g);self.assertEqual(len(bundle['steps']),3)
        self.assertTrue(b.replay(bundle))
        h,i=b.import_bundle(new(g['nodes']['goal']['statement']),bundle)
        self.assertEqual(i,'goal');self.assertIn('goal',closure(h));self.assertEqual(audit(h)['status'],'proved')
        self.assertEqual(b.import_bundle(h,bundle)[0],h)
    def test_tampering(self):
        bundle=b.export(self.graph())
        bad=copy.deepcopy(bundle);bad['steps'][-1]['proof']['premises'].pop()
        self.assertFalse(b.replay(bad))
        bad=copy.deepcopy(bundle);bad['steps'][0]['statement']=p.statement(spec([[[2,0],-1]]))
        self.assertFalse(b.replay(bad))
        bad=copy.deepcopy(bundle);bad['steps'].reverse()
        self.assertFalse(b.replay(bad))
    def test_no_manual_proof(self):
        g=apply(new('not checked'),[dict(op='review_claim',id='goal',decision='established',evidence='manual')],trusted=True)
        with self.assertRaises(ValueError):b.export(g)
    def test_reject_nested(self):
        g=self.graph();bundle=b.export(g)
        h,_=b.import_bundle(new(g['nodes']['goal']['statement']),bundle)
        with self.assertRaises(ValueError):b.export(h)
