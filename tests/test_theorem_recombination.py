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
        a=pol([[[2,0],1],[[1,1],-2],[[0,2],1]],('x','y'))
        goal=pol([[[2,0],1],[[1,1],-2],[[0,2],2]],('x','y'))
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

    def test_domain_from_context(self):
        src=p.statement(dict(variables=['u'],domain='nonnegative',relation='nonnegative',terms=[[[1],1]]))
        goal=cond([[[0],1],[[1],-1]],[dict(relation='nonnegative',terms=[[[0],1],[[1],-1]])])
        cert=dict(instances=[dict(source=src,images=[[[[0],'1'],[[1],'-1']]],weight='1')],context_terms=[])
        self.assertTrue(tr.replay(goal,[src],cert))
        # Removing the context requires an additional obligation, equal to
        # the goal itself, so no circular application may be accepted.
        self.assertFalse(tr.replay(pol([[[0],1],[[1],-1]]),[src],cert))
    def test_context_maps(self):
        from fractions import Fraction as Q
        from constraint_maps import candidates
        g=ct.parse_statement(cond([[[0,0],1]],[dict(relation='zero',terms=[[[0,0],-1],[[1,0],1],[[0,1],1]])],('x','y')))
        self.assertIn({(0,0):Q(1),(0,1):Q(-1)},candidates(g))
        self.assertIn({(0,0):Q(1),(1,0):Q(-1)},candidates(g))

if __name__=='__main__':
    unittest.main()
