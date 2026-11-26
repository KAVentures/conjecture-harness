import unittest
import polynomial as p
import representation_transfer as r
from discovery import new,apply,closure
from proof_audit import audit

def spec(v,t,d='real'):
    return dict(variables=v,domain=d,relation='nonnegative',terms=t)
class RepresentationTests(unittest.TestCase):
    def test_dimension_change(self):
        source=spec(['x'],[[[2],1]])
        goal=spec(['u','v'],[[[2,0],1],[[1,1],2],[[0,2],1]])
        hit=r.synthesize(goal,source)
        self.assertIsNotNone(hit);self.assertTrue(r.replay(goal,source,hit['certificate']))
        self.assertFalse(r.replay(goal,source,dict(hit['certificate'],scale='-1')))
    def test_domain_preservation(self):
        source=spec(['x'],[[[1],1]],'nonnegative')
        goal=spec(['u'],[[[1],1]],'real')
        cert=dict(images=[[[[1],'1']]],scale='1')
        self.assertFalse(r.replay(goal,source,cert))
        square=spec(['u'],[[[2],1]],'real')
        self.assertIsNotNone(r.synthesize(square,source))
    def test_audit_no_false_closure(self):
        source=spec(['x'],[[[2],1]])
        goal=spec(['u','v'],[[[2,0],1],[[1,1],2],[[0,2],1]])
        g=new(p.statement(goal))
        g=apply(g,[dict(op='claim',id='source',statement=p.statement(source)),dict(op='review_claim',id='source',decision='established',evidence='manual premise')],trusted=True)
        g=r.auto_discharge(g);self.assertIn('goal',closure(g))
        self.assertEqual(audit(g)['status'],'unverified')
        self.assertTrue(audit(g)['checked_edges'])
