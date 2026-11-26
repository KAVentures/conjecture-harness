import unittest
from affine import statement,parse_statement,prove,replay
from affine_lab import discharge,auto_discharge
from discovery import new,apply,closure


def spec(ass,goal):return dict(variables=['x','y'],assumptions=ass,conclusion=goal)

class AffineTests(unittest.TestCase):
    def test_transitive(self):
        s=spec([[0,1,-1],[-2,0,1]],[-2,1,0]);r=prove(s);self.assertEqual(r['status'],'proved');self.assertTrue(replay(s,r['certificate']))
    def test_false(self):self.assertEqual(prove(spec([[0,1,0]],[0,-1,0]))['status'],'not_proved')
    def test_vacuous(self):
        s=spec([[-1,1,0],[0,-1,0]],[0,0,1]);self.assertTrue(replay(s,prove(s)['certificate']))
    def test_constant(self):
        self.assertEqual(prove(spec([],[0,0,0]))['status'],'proved');self.assertEqual(prove(spec([],[-1,0,0]))['status'],'not_proved')
    def test_fraction(self):
        s=spec([[0,'1/3',0],[0,0,'1/2']],[0,1,1]);self.assertTrue(replay(s,prove(s)['certificate']))
    def test_tamper(self):
        s=spec([[0,1,0]],[0,1,0]);self.assertFalse(replay(s,{'multipliers':['0','0']}));self.assertRaises(ValueError,replay,s,{'multipliers':['-1','1']})
    def test_invalid(self):
        for s in (spec([[0,1.0,0]],[0,1,0]),spec([[0,1]],[0,1,0]),spec([],[True,0,0])):self.assertRaises(ValueError,prove,s)
    def test_binding(self):
        s=spec([[0,1,0]],[0,1,0]);self.assertRaises(ValueError,discharge,new('different'), 'goal',s);self.assertEqual(statement(parse_statement(statement(s))),statement(s))
    def test_auto_closure(self):
        s=spec([[0,1,-1],[0,0,1]],[0,1,0]);g=auto_discharge(new(statement(s)));self.assertIn('goal',closure(g));self.assertEqual(g['history'][-1]['reward'],1)
    def test_no_false_closure_or_repeat(self):
        g=auto_discharge(new(statement(spec([[0,1,0]],[0,-1,0]))));self.assertNotIn('goal',closure(g));self.assertEqual(auto_discharge(g),g)
    def test_auxiliary_not_goal(self):
        s=spec([],[1,0,0]);g=apply(new('Target'),[dict(op='claim',id='aux',statement=statement(s)),dict(op='derive',id='bridge',parent='goal',premises=['aux'],argument='unreviewed')]);g=auto_discharge(g);self.assertIn('aux',closure(g));self.assertNotIn('goal',closure(g))
    def test_runner_discharges_without_model(self):
        import tempfile,sys
        from pathlib import Path
        from discovery import save
        from discovery_run import run
        from runtime import read_json
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'state.json';save(path,new(statement(spec([[0,1,0]],[0,1,0]))))
            out=run(path,[sys.executable,'-c','raise SystemExit(99)'],1,10,1)
            self.assertTrue(out['derived']);self.assertIn('goal',closure(read_json(path)))
            self.assertFalse(list(Path(str(path)+'.runs').glob('*/raw.json')))
    def test_reserved_observation(self):
        with self.assertRaises(ValueError):apply(new('Target'),[dict(op='observe',id='aff-fake',focus='goal',kind='experiment',detail='fake')])
