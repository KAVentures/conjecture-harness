import unittest
import polynomial as p
import proof_synthesis as s
from discovery import new,apply,closure
from proof_audit import audit
def spec(terms,domain='real'):
    return dict(variables=['x','y'],domain=domain,relation='nonnegative',terms=terms)
class SynthesisTests(unittest.TestCase):
    def setUp(self):
        self.x=spec([[[2,0],1]]);self.y=spec([[[0,2],1]])
        self.goal=spec([[[2,0],2],[[0,2],3]])
    def test_weights(self):
        r=s.synthesize(self.goal,{'x':self.x,'y':self.y})
        self.assertEqual(r['certificate'],{'weights':['2','3']})
        self.assertTrue(s.replay(self.goal,[self.x,self.y],r['certificate']))
        self.assertFalse(s.replay(self.goal,[self.y,self.x],r['certificate']))
        self.assertFalse(s.replay(self.goal,[self.x,self.y],{'weights':['-2','3']}))
        self.assertFalse(s.replay(self.goal,[self.x,spec([[[0,2],1]],'nonnegative')],r['certificate']))
    def test_no_fake_proof(self):
        g=new(p.statement(self.goal))
        g=apply(g,[dict(op='claim',id='x',statement=p.statement(self.x)),dict(op='claim',id='y',statement=p.statement(self.y))])
        self.assertEqual(s.auto_discharge(g),g)
        g=apply(g,[dict(op='review_claim',id=i,decision='established',evidence='manual') for i in ('x','y')],trusted=True)
        g=s.auto_discharge(g);self.assertIn('goal',closure(g))
        self.assertEqual(audit(g)['status'],'unverified')
        self.assertTrue(audit(g)['checked_edges'])
    def test_inconsistent(self):
        self.assertIsNone(s.synthesize(self.goal,{'x':self.x}))
        self.assertIsNone(s.synthesize(spec([[[2,0],-1]]),{'x':self.x}))
