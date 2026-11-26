import unittest,tempfile,sys,json
from pathlib import Path
from discovery import new,record,plan,save,MODES,closure
from strategy_profile import build,prior,validate,load
from strategy import ranking
from discovery_portfolio import assignments,run as parallel
from discovery_run import run
from runtime import read_json
import polynomial as p


def sample(target='Past target',mode='forward'):
    g=record(new(target),mode,'goal',[dict(op='claim',id='a',statement='Private auxiliary'),dict(op='derive',id='e',parent='goal',premises=['a'],argument='private reasoning')])
    return record(g,'forward','a',[dict(op='review_claim',id='a',decision='established',evidence='private synthetic review')],trusted=True)

class ProfileTests(unittest.TestCase):
    def test_only_aggregate(self):
        prof=build([sample()]);s=json.dumps(prof);self.assertNotIn('Past target',s);self.assertNotIn('Private auxiliary',s);self.assertNotIn('private reasoning',s);self.assertNotIn('private synthetic review',s);self.assertGreater(prior(prof,new('Goal'))['forward'],0)
    def test_same_target_excluded(self):self.assertEqual(prior(build([sample()]),new('Past target')),dict.fromkeys(MODES,0))
    def test_duplicate_target(self):self.assertRaises(ValueError,build,[sample(),sample()])
    def test_domains_separate(self):
        s=p.statement(dict(variables=['x'],domain='real',relation='nonnegative',terms=[[[2],1]]));self.assertEqual(prior(build([sample(s)]),new('Goal')),dict.fromkeys(MODES,0))
    def test_bias_not_truth(self):
        g=new('Goal');prof=build([sample()]);self.assertEqual(plan(g,prof)['mode'],'forward');self.assertEqual(plan(g)['mode'],'backward');self.assertEqual(closure(g),set());self.assertEqual(len(g['nodes']),1)
    def test_escape_preserved(self):
        g=new('Goal');prof=build([sample()]); 
        for _ in range(3):g=record(g,'forward','goal',[])
        self.assertEqual(plan(g,prof)['mode'],'blind');self.assertIn('blind',{p['mode'] for p in assignments(g,3,prof)})
    def test_malformed_counts(self):
        prof=build([sample()]);r=next(iter(prof['targets'].values()))['modes']['forward'];r['credits']=2;self.assertRaises(ValueError,validate,prof);r['credits']=True;self.assertRaises(ValueError,validate,prof)
    def test_bounded_bias(self):
        prof=build([sample(str(i)) for i in range(30)]);self.assertTrue(all(abs(x)<=.15 for x in prior(prof,new('Goal')).values()));self.assertRaises(ValueError,ranking,[],MODES,{'forward':1})
    def test_cli_roundtrip(self):
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            s=Path(d)/'state.json';out=Path(d)/'profile.json';save(s,sample());cmd=[sys.executable,'strategy_profile.py',str(out),str(s)];subprocess.run(cmd,check=True,capture_output=True);self.assertEqual(load(out),build([sample()]));self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0)
    def test_runners_use_profile(self):
        prof=build([sample()]);cmd=[sys.executable,'-c','print("[]")']
        with tempfile.TemporaryDirectory() as d:
            for name,fn in [('serial',lambda path:run(path,cmd,1,5,2,prof)),('parallel',lambda path:parallel(path,[cmd],1,5,2,1,prof))]:
                path=Path(d)/name;save(path,new('Goal'));fn(path);g=read_json(path);self.assertEqual(g['history'][0]['mode'],'forward');self.assertNotIn('goal',closure(g))
