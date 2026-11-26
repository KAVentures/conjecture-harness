import unittest,copy
from affine import statement
from affine_bridge import synthesize,replay_bridge,discharge,auto_discharge
from discovery import new,apply,closure
from lean_export import source


def s(ass,con,vs=None):return dict(variables=vs or ['x'],assumptions=ass,conclusion=con)

def graph(goal,ps):
    return apply(new(statement(goal)),[dict(op='claim',id=i,statement=statement(p)) for i,p in ps.items()]+[dict(op='derive',id='edge',parent='goal',premises=list(ps),argument='candidate')])

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.goal=s([[0,1]],[-2,1]);self.ps={'a':s([[0,1]],[-1,1]),'b':s([[-1,1]],[-2,1])}
    def test_chain(self):
        r=synthesize(self.goal,self.ps);self.assertEqual(r['status'],'proved');self.assertEqual([x['premise'] for x in r['certificate']['steps']],['a','b']);self.assertTrue(replay_bridge(self.goal,self.ps,r['certificate']))
    def test_missing_assumption(self):
        self.assertEqual(synthesize(self.goal,{'b':self.ps['b']})['status'],'unknown')
    def test_binding(self):
        self.assertRaises(ValueError,synthesize,self.goal,{'a':s([],[-2,1],['y'])})
    def test_tamper_order(self):
        c=synthesize(self.goal,self.ps)['certificate'];c['steps'].reverse();self.assertFalse(replay_bridge(self.goal,self.ps,c))
    def test_tamper_goal(self):
        c=synthesize(self.goal,self.ps)['certificate'];self.assertFalse(replay_bridge(s([[0,1]],[-3,1]),self.ps,c))
    def test_budget(self):self.assertEqual(synthesize(self.goal,self.ps,max_calls=1)['status'],'unknown')
    def test_accept_not_close(self):
        g=graph(self.goal,self.ps);h,r=discharge(g,'edge');self.assertEqual(h['edges']['edge']['rule'],'accepted');self.assertNotIn('goal',closure(h));self.assertEqual(g['edges']['edge']['rule'],'candidate')
        h=apply(h,[dict(op='review_claim',id=i,decision='established',evidence='synthetic fixture, not mathematical evidence') for i in self.ps],trusted=True);self.assertIn('goal',closure(h))
    def test_automatic_and_no_repetition(self):
        g=graph(self.goal,{'b':self.ps['b']});h=auto_discharge(g);self.assertEqual(h['edges']['edge']['rule'],'candidate');self.assertEqual(auto_discharge(h),h)
    def test_reserved(self):
        self.assertRaises(ValueError,apply,new('target'),[dict(op='observe',id='bridge-fake',focus='goal',kind='experiment',detail='fake')])
    def test_lean_affine(self):
        t=source('affine',s([[0,'1/2']],[-2,1],['theorem']));self.assertIn('(v0 : ℝ)',t);self.assertIn('((1 : ℝ) / 2)',t);self.assertIn('linarith',t);self.assertIn('#print axioms conjecture_harness_claim',t);self.assertNotIn('(theorem :',t)
    def test_lean_polynomial(self):
        p=dict(variables=['x','y'],domain='nonnegative',relation='zero',terms=[[[2,0],1],[[2,0],-1]]);t=source('polynomial',p);self.assertIn('(h0 : v0 ≥ 0)',t);self.assertIn(' = 0 := by',t);self.assertIn('ring',t)
    def test_lean_invalid(self):
        self.assertRaises(ValueError,source,'affine',s([],[-2,1],['x) := by sorry']))
