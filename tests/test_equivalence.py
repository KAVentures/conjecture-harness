import unittest
import affine,polynomial
from equivalence import equivalent,signature,auto_reuse
from discovery import new,apply,closure
from discovery_portfolio import reconcile


def a(v,rows,goal):return affine.statement(dict(variables=v,assumptions=rows,conclusion=goal))
def p(v,terms,domain='real',relation='nonnegative'):return polynomial.statement(dict(variables=v,terms=terms,domain=domain,relation=relation))
def c(i,s):return dict(op='claim',id=i,statement=s)
def e(i,parent,ps):return dict(op='derive',id=i,parent=parent,premises=ps,argument='candidate')
def review(i,d):return dict(op='review_claim',id=i,decision=d,evidence='synthetic test fixture')

class EquivalenceTests(unittest.TestCase):
    def test_affine_permutation_scaling(self):
        x=a(['x','y'],[[0,1,-1],[-2,0,1]],[-2,1,0]);y=a(['v','u'],[[-6,3,0],[0,-2,2],[1,0,0],[0,-2,2]],[-8,0,4]);self.assertTrue(equivalent(x,y))
    def test_affine_sign_and_hypothesis(self):
        x=a(['x'],[[0,1]],[0,1]);self.assertFalse(equivalent(x,a(['x'],[[0,-1]],[0,1])));self.assertFalse(equivalent(x,a(['x'],[],[0,1])))
    def test_polynomial_permutation_scaling(self):
        x=p(['x','y'],[[[2,0],1],[[0,1],-2]]);y=p(['v','u'],[[[0,2],3],[[1,0],-6]]);self.assertTrue(equivalent(x,y))
    def test_polynomial_sign_and_domain(self):
        x=p(['x'],[[[1],1]]);self.assertFalse(equivalent(x,p(['x'],[[[1],-1]])));self.assertFalse(equivalent(x,p(['x'],[[[1],1]],'nonnegative')));self.assertFalse(equivalent(x,p(['x'],[[[1],1]],relation='zero')))
    def test_identity_negative_scale(self):
        self.assertTrue(equivalent(p(['x'],[[[1],1]],relation='zero'),p(['t'],[[[1],-3]],relation='zero')))
    def test_untyped_and_malformed(self):
        self.assertFalse(equivalent('x >= 0','x >= 0'));self.assertIsNone(signature(affine.PREFIX+'{}'))
    def test_six_variables_positional(self):
        x=a(list('abcdef'),[],[0,1,0,0,0,0,0]);y=a(list('uvwxyz'),[],[0,3,0,0,0,0,0]);self.assertTrue(equivalent(x,y))
    def test_worker_dedup(self):
        x=p(['x'],[[[2],1]]);y=p(['y'],[[[2],2]]);g=apply(new('Target'),[c('a',x),e('b','goal',['a'])]);self.assertEqual(reconcile(g,g,[c('z',y),e('d','goal',['z'])],'test'),[])
    def test_worker_self_cycle(self):
        x=p(['x'],[[[2],1]]);y=p(['y'],[[[2],2]]);g=new(x);self.assertRaises(ValueError,reconcile,g,g,[c('z',y),e('d','goal',['z'])],'test')
    def test_transfer_reviewed_only(self):
        x=p(['x'],[[[2],1]]);y=p(['y'],[[[2],2]]);g=apply(new(x),[c('a',y)]);self.assertEqual(auto_reuse(g),g);g=apply(g,[review('a','established')],trusted=True);h=auto_reuse(g);self.assertIn('goal',closure(h));self.assertEqual(h['nodes']['goal']['statement'],x);self.assertEqual(auto_reuse(h),h)
    def test_transfer_refuted(self):
        x=p(['x'],[[[1],1]]);y=p(['y'],[[[1],2]]);g=apply(new(x),[c('a',y),review('a','refuted')],trusted=True);self.assertEqual(auto_reuse(g)['nodes']['goal']['status'],'refuted')
    def test_conflict(self):
        x=p(['x'],[[[2],1]]);g=apply(new(x),[c('a',p(['a'],[[[2],2]])),c('b',p(['b'],[[[2],3]])),review('a','established'),review('b','refuted')],trusted=True);self.assertRaises(ValueError,auto_reuse,g)
    def test_reserved(self):
        self.assertRaises(ValueError,apply,new('target'),[dict(op='observe',id='equiv-fake',focus='goal',kind='experiment',detail='fake')])
