import unittest,tempfile,sys,json
from pathlib import Path
from discovery import new,record,plan,prompt,MODES,save,apply
from strategy import statistics,ranking
from discovery_run import run
from runtime import read_json


def proposal(i):return [dict(op='claim',id=i,statement='Lemma '+i),dict(op='derive',id='e'+i,parent='goal',premises=[i],argument='candidate')]
def review(i,decision='established'):return dict(op='review_claim',id=i,decision=decision,evidence='fixture review')

class StrategyTests(unittest.TestCase):
    def test_delayed_credit(self):
        g=record(new('Goal'),'reformulate','goal',proposal('a'));g=record(g,'forward','a',[review('a')],trusted=True)
        s=statistics(g['history'],MODES);self.assertEqual(s['reformulate']['credits'],1);self.assertEqual(s['forward']['attempts'],0)
    def test_no_speculative_credit(self):
        g=record(new('Goal'),'forward','goal',proposal('a'));self.assertEqual(statistics(g['history'],MODES)['forward']['credits'],0)
    def test_irrelevant_review(self):
        g=record(new('Goal'),'forward','goal',[proposal('a')[0]]);g=record(g,'backward','a',[review('a')],trusted=True);self.assertEqual(statistics(g['history'],MODES)['forward']['credits'],0)
    def test_cap_per_attempt(self):
        g=record(new('Goal'),'forward','goal',proposal('a'));g=record(g,'backward','a',[review('a'),dict(op='review_edge',id='ea',decision='accepted',evidence='fixture')],trusted=True);self.assertEqual(statistics(g['history'],MODES)['forward']['credits'],1)
    def test_legacy(self):
        g=record(new('Goal'),'backward','goal',[]);del g['history'][0]['verified_items'];self.assertEqual(statistics(g['history'],MODES)['backward']['attempts'],1)
    def test_stagnation_all_modes(self):
        g=new('Goal');seen=set()
        for i in range(10):
            q=plan(g)
            if i>=3:seen.add(q['mode'])
            g=record(g,q['mode'],q['focus'],[])
        self.assertEqual(seen,set(MODES))
    def test_cost_penalty(self):
        g=record(new('Goal'),'forward','goal',proposal('a'));g['history'][-1]['elapsed_seconds']=100;g=record(g,'backward','goal',proposal('b'));g['history'][-1]['elapsed_seconds']=1;g=record(g,'blind','goal',[review('a'),review('b')],trusted=True);r=ranking(g['history'],MODES);self.assertLess(r.index('backward'),r.index('forward'))
    def test_graph_syntax(self):
        p=prompt(new('Goal'),{'mode':'blind','focus':'goal'});self.assertIn('Shannon capacity upper bound',p);self.assertIn('Finite strong-power independence upper bound',p)
    def test_serial_blind_snapshot(self):
        g=apply(new('Goal'),[proposal('a')[0]])
        for _ in range(3):g=record(g,'backward','goal',[])
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json';save(p,g);cmd=[sys.executable,'-c','print('+repr(json.dumps([proposal('a')[1]]))+')'];run(p,cmd,1,5,2);h=read_json(p);self.assertEqual(h['edges'],{});self.assertTrue(list(Path(str(p)+'.runs').glob('*/rejected.txt')))
    def test_serial_dedup(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json';save(p,new('Goal'));cmd=[sys.executable,'-c','print('+repr(json.dumps(proposal('a')))+')'];run(p,cmd,2,5,2);h=read_json(p);self.assertEqual(len(h['nodes']),2);self.assertEqual(len(h['edges']),1);self.assertIn('elapsed_seconds',h['history'][0])
