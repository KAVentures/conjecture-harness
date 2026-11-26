import unittest,tempfile,sys
from pathlib import Path
from polynomial import statement,parse_statement,solve,replay
from polynomial_lab import auto_discharge,discharge
from discovery import new,closure,apply,save,plan
from discovery_run import run

def spec(ts,domain='real',relation='nonnegative'):return dict(variables=['x','y'],domain=domain,relation=relation,terms=ts)

class PolynomialTests(unittest.TestCase):
    def test_identity(self):
        s=spec([[[2,0],1],[[2,0],-1]],relation='zero');self.assertEqual(solve(s)['status'],'proved');self.assertTrue(replay(s,{'kind':'identity'}))
    def test_quartic(self):
        s=spec([[[4,0],1],[[2,2],-2],[[0,4],1]]);r=solve(s);self.assertEqual(r['status'],'proved');self.assertTrue(replay(s,r['certificate']))
    def test_quadratic(self):
        s=spec([[[2,0],2],[[1,1],-2],[[0,2],1]]);self.assertEqual(solve(s)['status'],'proved')
    def test_shift(self):
        s=spec([[[2,0],1],[[1,0],-2],[[0,0],1]]);self.assertEqual(solve(s)['status'],'proved')
    def test_orthant(self):
        s=spec([[[1,1],1]],'nonnegative');self.assertEqual(solve(s)['status'],'proved');self.assertEqual(solve(dict(s,domain='real'))['status'],'counterexample')
    def test_false(self):
        s=spec([[[2,0],1],[[0,0],-1]]);r=solve(s);self.assertEqual(r['status'],'counterexample');self.assertTrue(replay(s,r['certificate']))
    def test_identity_false(self):self.assertEqual(solve(spec([[[1,0],1]],relation='zero'))['status'],'counterexample')
    def test_tamper(self):
        s=spec([[[2,0],1]]);self.assertFalse(replay(s,{'kind':'sos','squares':[], 'monomials':[[[2,0],2]]}));self.assertFalse(replay(s,{'kind':'point','point':['1','0']}));self.assertFalse(replay(s,{'kind':'sos','squares':[['-1',[[[1,0],1]]]],'monomials':[]}))
    def test_domain(self):self.assertFalse(replay(spec([[[1,0],1]],'nonnegative'),{'kind':'point','point':['-1','0']}))
    def test_invalid(self):
        for t in ([[[9,0],1]],[[[True,0],1]],[[[1,0],0.5]]):self.assertRaises(ValueError,solve,spec(t))
    def test_unknown(self):
        s=spec([[[4,2],1],[[2,4],1],[[2,2],-3],[[0,0],1]]);self.assertEqual(solve(s)['status'],'unknown') # Motzkin polynomial
    def test_binding_and_auto(self):
        s=spec([[[2,0],1]]);self.assertEqual(statement(parse_statement(statement(s))),statement(s));self.assertRaises(ValueError,discharge,new('Other'),'goal',s);self.assertIn('goal',closure(auto_discharge(new(statement(s)))))
    def test_auxiliary_refutation(self):
        s=spec([[[0,0],-1]]);g=apply(new('Target'),[dict(op='claim',id='aux',statement=statement(s)),dict(op='derive',id='bridge',parent='goal',premises=['aux'],argument='candidate')]);h=auto_discharge(g);self.assertEqual(h['nodes']['aux']['status'],'refuted');self.assertEqual(h['nodes']['goal']['status'],'open');self.assertEqual(plan(h)['mode'],'refine')
    def test_runner(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json';save(p,new(statement(spec([[[2,0],1]]))));self.assertTrue(run(p,[sys.executable,'-c','raise SystemExit(99)'],1,10,1)['derived']);self.assertFalse(list(Path(str(p)+'.runs').glob('*/raw.json')))
    def test_reserved(self):self.assertRaises(ValueError,apply,new('Target'),[dict(op='observe',id='poly-fake',focus='goal',kind='experiment',detail='fake')])
