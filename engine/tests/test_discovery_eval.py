import json,sys,tempfile,unittest
from pathlib import Path
from discovery_eval import generate,validate_suite,verify,prompt,run,digest,tool_only

class EvaluationTests(unittest.TestCase):
    def test_seeded_controls(self):
        s=generate(17,30);self.assertEqual(s,generate(17,30));self.assertNotEqual(digest(s),digest(generate(18,30)));validate_suite(s)
        self.assertEqual({c['expected'] for c in s['cases']},{'proved','refuted'})
    def test_exact_reference_and_abstention(self):
        for c in generate(2,10)['cases']:
            self.assertEqual(verify(c['task'],c['reference']),c['expected']);self.assertEqual(verify(c['task'],{'kind':'unknown'}),'abstained')
    def test_point_not_proof(self):
        s={'domain':'polynomial','spec':dict(variables=['x'],domain='real',relation='nonnegative',terms=[[[0],-1]])}
        self.assertEqual(verify(s,dict(kind='proof',certificate=dict(kind='point',point=['0']))),'invalid')
        self.assertEqual(verify(s,dict(kind='point',point=['0'])),'refuted')
    def test_bad_reference(self):
        s=generate(3,1);s['cases'][0]['expected']='refuted';self.assertRaises(ValueError,validate_suite,s)
    def test_no_reference_or_history_in_blind(self):
        t=generate(3,1)['cases'][0]['task'];h=[dict(stdout='SECRET',outcome='invalid')]
        self.assertNotIn('SECRET',prompt(t,'blind',h));self.assertIn('SECRET',prompt(t,'continuation',h));self.assertIn('Exact checker outcome',prompt(t,'adaptive',h));self.assertEqual(prompt(t,'blind',[]),prompt(t,'adaptive',[]))
    def test_bounded_runs_and_failures(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'run';s=generate(5,2);r=run(s,[sys.executable,'-c','raise SystemExit(3)'],p,2,2,7)
            self.assertTrue(r['complete']);self.assertTrue(all(x['calls']==4 and x['failures']==4 and x['solved']==0 for x in r['summary'].values()));self.assertEqual(len(list(p.glob('*/result.json'))),12);self.assertRaises(FileExistsError,run,s,[sys.executable],p)
    def test_success_early_stops_all_arms(self):
        s=generate(5,1);a=json.dumps(s['cases'][0]['reference']);cmd=[sys.executable,'-c','print('+repr(a)+')']
        with tempfile.TemporaryDirectory() as d:
            r=run(s,cmd,Path(d)/'r',3,2);self.assertTrue(all(x['solved']==1 and x['calls']==1 for x in r['summary'].values()))
    def test_malformed_output(self):
        with tempfile.TemporaryDirectory() as d:
            r=run(generate(4,1),[sys.executable,'-c','print("not JSON")'],Path(d)/'r',1,2)
            self.assertTrue(all(x['invalid']==1 and x['solved']==0 for x in r['summary'].values()))
    def test_tools_only_baseline(self):
        s=generate(1729,25);r=tool_only(s);self.assertEqual(r['total'],25);self.assertEqual(r['suite_sha256'],digest(s));self.assertGreater(r['solved'],0);self.assertTrue(all(x['outcome'] in ('proved','refuted','abstained') for x in r['results']))
    def test_abstention_accounting_and_paired(self):
        with tempfile.TemporaryDirectory() as d:
            r=run(generate(4,1),[sys.executable,'-c','import json;print(json.dumps(dict(kind="unknown")))'],Path(d)/'r',1,2,model_label='synthetic mock')
            self.assertTrue(all(x['abstentions']==1 and x['invalid']==0 for x in r['summary'].values()));self.assertEqual(r['paired']['blind__adaptive']['neither'],1);self.assertEqual(r['design']['model_label'],'synthetic mock')
