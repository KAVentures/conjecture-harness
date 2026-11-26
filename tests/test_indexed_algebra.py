import unittest
import indexed_algebra as a
from discovery import new,closure,apply
from proof_audit import audit
from structured_algebra_lab import auto_discharge

def term(c,fs,power=0):return dict(coefficient=c,n_power=power,factors=fs)
def tensor(sym='none',rank=2):return dict(rank=rank,symmetry=sym)
class IndexedTests(unittest.TestCase):
    def test_dummy_rename(self):
        s=dict(tensors={'A':tensor(),'B':tensor()},terms=[term(1,[['A',[0,1]],['B',[1,0]]]),term(-1,[['B',[4,2]],['A',[2,4]]])])
        r=a.solve(s);self.assertEqual(r['status'],'proved')
        g=auto_discharge(new(a.statement(s)));self.assertIn('goal',closure(g));self.assertEqual(audit(g)['status'],'proved')
    def test_symmetric_alternating(self):
        s=dict(tensors={'S':tensor('symmetric'),'A':tensor('alternating')},terms=[term(1,[['S',[0,1]],['A',[0,1]]])])
        self.assertEqual(a.replay(s,{'kind':'canonical-zero'}),'proved')
        z=dict(tensors={'A':tensor('alternating')},terms=[term(1,[['A',[0,0]]])])
        self.assertEqual(a.replay(z,{'kind':'canonical-zero'}),'proved')
    def test_alternating_sign(self):
        s=dict(tensors={'A':tensor('alternating'),'v':tensor(rank=1),'w':tensor(rank=1)},terms=[term(1,[['A',[0,1]],['v',[0]],['w',[1]]]),term(1,[['A',[1,0]],['v',[0]],['w',[1]]])])
        self.assertEqual(a.solve(s)['status'],'proved')
    def test_witness(self):
        s=dict(tensors={'A':tensor()},terms=[term(1,[['A',[0,1]]])])
        r=a.solve(s);self.assertEqual(r['status'],'counterexample');self.assertEqual(a.replay(s,r['certificate']),'refuted')
        self.assertIsNone(a.replay(s,{'kind':'canonical-zero'}))
    def test_dimension_power(self):
        s=dict(tensors={'v':tensor(rank=1)},terms=[term(1,[['v',[0]]],1),term(-1,[['v',[0]]])])
        r=a.solve(s);self.assertEqual(r['status'],'counterexample')
        self.assertGreater(r['certificate']['n'],1)
    def test_reserved_and_validation(self):
        with self.assertRaises(ValueError):a.normalize(dict(tensors={'A':tensor(rank=True)},terms=[]))
        with self.assertRaises(ValueError):apply(new('x'),[dict(op='observe',id='indexed-fake',focus='goal',kind='proof_sketch',detail='fake')])
