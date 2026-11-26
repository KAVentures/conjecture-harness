import unittest
from discovery import new
from proof_audit import audit
import polynomial as p
import conditional_theorems as ct
import theorem_recombination as tr

def pol(terms,vs=('x',)):
    return p.statement(dict(variables=list(vs),domain='real',relation='nonnegative',terms=terms))

def cond(terms,assumptions,vs=('x',)):
    return ct.statement(dict(variables=list(vs),domain='real',conclusion=terms,assumptions=assumptions))

class TheoremRecombinationTests(unittest.TestCase):
    def test_exact_cancellation(self):
        # (x-1)^2+(x+1)^2=2x^2+2; x^2+1 is the target.
        a=pol([[[2],1],[[1],-2],[[0],1]])
        b=pol([[[2],1],[[1],2],[[0],1]])
        goal=pol([[[2],1],[[0],1]])
        image=[[[[1],'1']]]
        cert=dict(instances=[dict(source=a,images=image,weight='1/2'),
                             dict(source=b,images=image,weight='1/2')],context_terms=[])
        self.assertTrue(tr.replay(goal,[a,b],cert))
        self.assertFalse(tr.replay(goal,[a],cert))
        cert['instances'][0]['weight']='1'
        self.assertFalse(tr.replay(goal,[a,b],cert))
    def test_joint_discovery_and_audit(self):
        # A single source can be instantiated in two different ways.
        a=pol([[[2],1],[[1],-2],[[0],1]])
        goal=pol([[[2],1],[[0],1]])
        hit=tr.discover(goal,[a],[a])
        self.assertIsNotNone(hit)
        self.assertTrue(tr.replay(goal,hit['premises'],hit['certificate']))
        g=tr.insert(new(goal),'goal',hit)
        self.assertEqual(len(audit(g)['checked_edges']),1)
        self.assertNotIn('goal',audit(g)['proved'])
    def test_context_and_missing_hypothesis(self):
        a=cond([[[1],1]],[dict(relation='nonnegative',terms=[[[1],1]])])
        goal=pol([[[1],1]])
        image=[[[[1],'1']]]
        cert=dict(instances=[dict(source=a,images=image,weight='1')],context_terms=[])
        # The substituted hypothesis is exactly the target: circular.
        self.assertFalse(tr.replay(goal,[a,goal],cert))
        goal=cond([[[1],2]],[dict(relation='nonnegative',terms=[[[1],1]])])
        cert['instances'][0]['weight']='2'
        self.assertTrue(tr.replay(goal,[a],cert))
    def test_domain_rejected(self):
        src=p.statement(dict(variables=['x'],domain='nonnegative',relation='nonnegative',terms=[[[1],1]]))
        goal=pol([[[1],1]])
        cert=dict(instances=[dict(source=src,images=[[[[1],'1']]],weight='1')],context_terms=[])
        self.assertFalse(tr.replay(goal,[src],cert))

if __name__=='__main__':
    unittest.main()
