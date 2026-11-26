import unittest
from discovery import new, apply, record, closure, frontier, plan, prompt

def claim(i,s):return dict(op='claim',id=i,statement=s)
def edge(i,p,ps):return dict(op='derive',id=i,parent=p,premises=ps,argument='Candidate bridge')
def review(i,d,edge=False):return dict(op='review_edge' if edge else 'review_claim',id=i,decision=d,evidence='Reviewed derivation or exact counterexample: fixture')

class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.g=apply(new('Target'),[claim('a','Lemma A'),claim('b','Lemma B'),claim('c','Lemma C'),edge('ab','goal',['a','b']),edge('alt','goal',['c'])])
    def test_and_or(self):
        g=apply(self.g,[review('a','established'),review('ab','accepted',True)],trusted=True);self.assertNotIn('goal',closure(g))
        g=apply(g,[review('b','established')],trusted=True);self.assertIn('goal',closure(g))
        h=apply(self.g,[review('c','established'),review('alt','accepted',True)],trusted=True);self.assertIn('goal',closure(h))
    def test_untrusted(self):
        for x in (review('a','established'),review('ab','accepted',True),review('b','refuted')):
            with self.assertRaises(ValueError):apply(self.g,[x])
    def test_cycle_atomic(self):
        with self.assertRaises(ValueError):apply(self.g,[claim('d','New D'),edge('cycle','a',['goal'])])
        self.assertNotIn('d',self.g['nodes'])
    def test_duplicate(self):
        with self.assertRaises(ValueError):apply(self.g,[claim('d',' lemma  A ')])
        with self.assertRaises(ValueError):apply(self.g,[edge('new','goal',['b','a'])])
    def test_refutation(self):
        g=apply(self.g,[review('a','refuted')],trusted=True);self.assertEqual(frontier(g),['c','goal']);self.assertNotIn('goal',closure(g))
    def test_candidate_not_closed(self):
        g=apply(self.g,[review('a','established'),review('b','established')],trusted=True);self.assertNotIn('goal',closure(g))
    def test_stagnation(self):
        g=self.g
        for i in range(3):g=record(g,'backward','goal',[claim('x'+str(i),'Different '+str(i))])
        self.assertEqual(plan(g)['mode'],'blind');self.assertNotIn('Lemma A',prompt(g,plan(g)))
        g=record(g,'blind','goal',[]);self.assertEqual(plan(g)['mode'],'reformulate')
    def test_reward(self):
        g=record(self.g,'falsify','a',[review('a','refuted')],trusted=True);self.assertEqual(g['history'][-1]['reward'],1);self.assertEqual(plan(g)['stagnation'],0)
    def test_contradiction(self):
        g=apply(self.g,[review('goal','refuted'),review('a','established'),review('b','established')],trusted=True)
        with self.assertRaises(ValueError):apply(g,[review('ab','accepted',True)],trusted=True)
    def test_target_drift(self):
        self.g['nodes']['goal']['statement']='Changed'
        with self.assertRaises(ValueError):plan(self.g)
    def test_observation_is_not_proof(self):
        o=dict(op='observe',id='obs',focus='a',kind='counterexample',detail='candidate witness')
        g=record(self.g,'falsify','a',[o]);self.assertEqual(g['history'][-1]['reward'],0);self.assertEqual(g['nodes']['a']['status'],'open');self.assertIn('candidate witness',prompt(g,{'mode':'refine','focus':'a'}))
    def test_irrelevant_reward(self):
        g=apply(self.g,[claim('unrelated','Unrelated fact')]);g=record(g,'forward','a',[review('unrelated','established')],trusted=True);self.assertEqual(g['history'][-1]['reward'],0)
    def test_run(self):
        import tempfile,sys
        from pathlib import Path
        from discovery import save
        from runtime import read_json
        from discovery_run import run
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json';save(p,self.g)
            cmd=[sys.executable,'-c','print("[]")']
            result=run(p,cmd,3,10,2);self.assertEqual(result['mode'],'blind');self.assertEqual(len(read_json(p)['history']),3)
            cmd=[sys.executable,'-c','print(\'[ {"op":"review_claim","id":"goal","decision":"established","evidence":"fake"} ]\')']
            run(p,cmd,1,10,2);self.assertNotIn('goal',closure(read_json(p)));self.assertTrue(any(Path(str(p)+'.runs').glob('3-*/rejected.txt')))
    def test_counterexample_pivots(self):
        o=dict(op='observe',id='obs',focus='a',kind='counterexample',detail='candidate witness')
        g=record(self.g,'falsify','a',[o]);self.assertEqual(plan(g)['mode'],'refine')
    def test_reviewed_bridge_reward(self):
        g=record(self.g,'backward','goal',[review('ab','accepted',True)],trusted=True);self.assertEqual(g['history'][-1]['reward'],1);self.assertNotIn('goal',closure(g))
