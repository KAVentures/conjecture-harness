import unittest
import conditional_theorems as c
import conditional_lab
import theorem_application as a
import polynomial as p
import polynomial_lab
from discovery import new,closure,apply,record,fingerprint
from proof_audit import audit
import json

def h(terms,relation='nonnegative'):return dict(relation=relation,terms=terms)
def rule(assumptions,conclusion,vs=None,domain='real'):
    return dict(variables=vs or ['x'],domain=domain,assumptions=assumptions,conclusion=conclusion)
def claim(t,vs=None,domain='real'):
    return p.statement(dict(variables=vs or ['x'],domain=domain,relation='nonnegative',terms=t))

class ConditionalTests(unittest.TestCase):
    def test_nonnegative_multiplier(self):
        s=rule([h([[[1],1]])],[[[3],1]])
        r=c.solve(s);self.assertEqual(r['status'],'proved')
        self.assertEqual(c.replay(s,r['certificate']),'proved')
        self.assertIsNone(c.replay(rule([],[[[3],1]]),r['certificate']))
    def test_equality_signed_multiplier(self):
        s=rule([h([[[1],1]],'zero')],[[[1],-1]])
        r=c.solve(s);self.assertEqual(r['status'],'proved')
        self.assertIsNone(c.replay(rule([h([[[1],1]])],[[[1],-1]]),r['certificate']))
    def test_two_assumption_product(self):
        s=rule([h([[[1,0],1]]),h([[[0,1],1]])],[[[1,1],1]],['x','y'])
        r=c.solve(s);self.assertEqual(r['status'],'proved')
        self.assertEqual(c.replay(s,r['certificate']),'proved')
    def test_counterexample_is_feasible(self):
        s=rule([h([[[1],1]])],[[[1],-1]])
        r=c.solve(s);self.assertEqual(r['status'],'counterexample')
        self.assertEqual(c.replay(s,r['certificate']),'refuted')
        self.assertIsNone(c.replay(s,dict(kind='point',point=['-1'])))
    def test_audit(self):
        s=rule([h([[[1],1]])],[[[3],1]])
        g=conditional_lab.auto_discharge(new(c.statement(s)))
        self.assertEqual(audit(g)['status'],'proved')
    def test_missing_hypothesis(self):
        src=c.statement(rule([h([[[1],1]])],[[[3],1]]))
        target=claim([[[6],1]])
        hit=a.propose(target,src,512)
        self.assertIsNotNone(hit)
        self.assertEqual(len(hit['premises']),2)
        self.assertIn(claim([[[2],1]]),hit['premises'])
        self.assertFalse(a.replay(target,[src],hit['certificate']))
        g=a.insert(new(target),'goal',src,hit,dict(source='test',locator='test fixture'))
        self.assertNotIn('goal',closure(g))
        self.assertEqual(audit(g)['status'],'unverified')
        edge=next(iter(g['edges']))
        g=conditional_lab.auto_discharge(g)
        for i in g['edges'][edge]['premises']:
            if g['nodes'][i]['statement']==src:continue
            g,_=polynomial_lab.discharge(g,i,p.parse_statement(g['nodes'][i]['statement']))
        self.assertEqual(audit(g)['status'],'proved')
        self.assertEqual(audit(g)['proved']['goal'],edge)
    def test_equality_creates_two_obligations(self):
        src=c.statement(rule([h([[[1],1]],'zero')],[[[3],1]]))
        target=claim([[[6],1]])
        hit=a.propose(target,src,512)
        self.assertIsNotNone(hit)
        self.assertEqual(len(hit['premises']),3)
        self.assertIn(claim([[[2],-1]]),hit['premises'])
    def test_conditional_context(self):
        src=c.statement(rule([h([[[1],1]])],[[[3],1]]))
        g=c.statement(rule([h([[[1],1]])],[[[3],2]]))
        hit=a.propose(g,src)
        self.assertIsNotNone(hit)
        for t in hit['premises'][1:]:
            self.assertEqual(c.parse_statement(t)['assumptions'],c.parse_statement(g)['assumptions'])
    def test_reserved(self):
        for prefix in ('conditional-','application-'):
            with self.assertRaises(ValueError):apply(new('x'),[dict(op='observe',id=prefix+'fake',focus='goal',kind='proof_sketch',detail='fake')])
