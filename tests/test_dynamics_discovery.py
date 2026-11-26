import unittest
from fractions import Fraction as Q
import dynamics_discovery as d
import dynamics_lab
from discovery import new,closure,apply
from proof_audit import audit

class DynamicsTests(unittest.TestCase):
    def fib(self):
        return dict(variables=['x','y'],transition=[[[[0,1],1]],[[[1,0],1],[[0,1],1]]],observable=[[[1,0],1]])
    def parabola(self):
        return dict(variables=['x','y'],transition=[[[[1,0],1],[[0,0],1]],[[[0,1],1],[[1,0],2],[[0,0],1]]])
    def test_recurrence_discovery(self):
        r=d.discover(self.fib())
        self.assertEqual(r['spec']['weights'],['-1','-1','1'])
        self.assertEqual(d.replay(r['spec'],r['certificate']),'proved')
        self.assertIsNone(d.replay(r['spec'],dict(kind='recurrence-identity',weights=['-1','1'])))
    def test_invariant_discovery(self):
        r=d.invariant_basis(self.parabola(),2)
        self.assertEqual(r['status'],'complete_degree_space')
        self.assertTrue(r['basis'])
        expected={ (0,1):Q(1), (2,0):Q(-1) }
        self.assertTrue(any(d.terms(x['spec']['observable'],2)==expected or d.terms(x['spec']['observable'],2)=={e:-v for e,v in expected.items()} for x in r['basis']))
        for x in r['basis']:self.assertEqual(d.replay(x['spec'],x['certificate']),'proved')
    def test_orbit_induction(self):
        s=dict(self.parabola(),kind='orbit-zero',observable=[[[0,1],1],[[2,0],-1]],initial=['2','4'])
        r=d.solve(s);self.assertEqual(r['status'],'proved')
        self.assertEqual(d.replay(s,r['certificate']),'proved')
        bad=dict(s,initial=['2','5'])
        self.assertIsNone(d.replay(bad,r['certificate']))
        rr=d.solve(bad);self.assertEqual(rr['status'],'counterexample')
        self.assertEqual(d.replay(bad,rr['certificate']),'refuted')
    def test_refute_wrong_recurrence(self):
        s=dict(self.fib(),kind='recurrence',weights=['-1','1'])
        r=d.solve(s);self.assertEqual(r['status'],'counterexample')
        self.assertEqual(d.replay(s,r['certificate']),'refuted')
        self.assertIsNone(d.replay(dict(s,weights=['-1','-1','1']),r['certificate']))
    def test_degree_growth_unknown(self):
        s=dict(variables=['x'],transition=[[[[2],1]]],observable=[[[1],1]])
        self.assertEqual(d.discover(s)['status'],'unknown')
    def test_runner_and_audit(self):
        s=dict(self.fib(),kind='recurrence',weights=['-1','-1','1'])
        g=dynamics_lab.auto_discharge(new(d.statement(s)))
        self.assertIn('goal',closure(g));self.assertEqual(audit(g)['status'],'proved')
        bad=dict(s,weights=['-1','1'])
        g=dynamics_lab.auto_discharge(new(d.statement(bad)))
        self.assertEqual(audit(g)['status'],'refuted')
    def test_reserved_and_validation(self):
        with self.assertRaises(ValueError):d.discover(dict(self.fib(),transition=[]))
        with self.assertRaises(ValueError):d.invariant_basis(self.parabola(),4)
        with self.assertRaises(ValueError):apply(new('x'),[dict(op='observe',id='dynamics-fake',focus='goal',kind='proof_sketch',detail='fake')])

    def test_nonlinear_ideal(self):
        import ideal_induction as ideal
        s=dict(kind='orbit-zero',variables=['x','y'],transition=[[[[2,0],1],[[0,1],1]],[[[0,2],1]]],observable=[[[1,0],1]],initial=[0,0])
        self.assertIsNone(d.recurrence(d.normalize(s)))
        r=d.solve(s)
        self.assertEqual(r['status'],'proved')
        self.assertEqual(r['certificate']['kind'],'ideal-induction')
        self.assertEqual(len(r['certificate']['basis']),2)
        self.assertTrue(ideal.replay(s,r['certificate']))
        self.assertFalse(ideal.replay(dict(s,initial=[0,1]),r['certificate']))
        broken=dict(r['certificate'],multipliers=[[[],[]],[[],[]]])
        self.assertIsNone(d.replay(s,broken))
    def test_division_exact(self):
        import ideal_induction as ideal
        from representation_transfer import mul
        a={(2,0):Q(1),(0,1):Q(1)};basis=[{(1,0):Q(1)}]
        qs,rem=ideal.divide(a,basis)
        self.assertEqual(d.add(mul(qs[0],basis[0]),rem),a)
        self.assertEqual(rem,{(0,1):Q(1)})
