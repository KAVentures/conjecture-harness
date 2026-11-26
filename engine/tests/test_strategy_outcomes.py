import unittest
from discovery import new,record,MODES,plan
from strategy import statistics,ranking,stagnation


def claim(i):return dict(op='claim',id=i,statement='Lemma '+i)
def edge(i):return dict(op='derive',id='e'+i,parent='goal',premises=[i],argument='candidate')
def review(i,d):return dict(op='review_claim',id=i,decision=d,evidence='synthetic review fixture')
def edge_review(i,d):return dict(op='review_edge',id='e'+i,decision=d,evidence='synthetic review fixture')
def proposed(g,m,i):return record(g,m,'goal',[claim(i),edge(i)])

class StrategyOutcomeTests(unittest.TestCase):
    def test_refuted_not_positive(self):
        g=proposed(new('Goal'),'backward','a');g=record(g,'falsify','a',[review('a','refuted')],trusted=True)
        s=statistics(g['history'],MODES);self.assertEqual(s['backward']['credits'],0);self.assertEqual(s['backward']['adverse'],1);self.assertEqual(s['falsify']['attempts'],0)
    def test_rejected_edge_not_positive(self):
        g=proposed(new('Goal'),'forward','a');g=record(g,'forward','goal',[edge_review('a','rejected')],trusted=True)
        s=statistics(g['history'],MODES);self.assertEqual(s['forward']['credits'],0);self.assertEqual(s['forward']['adverse'],1)
    def test_mixed_outcomes_capped(self):
        g=record(new('Goal'),'backward','goal',[claim('a'),edge('a'),claim('b'),edge('b'),claim('c'),edge('c')]);g=record(g,'forward','goal',[review('a','established'),review('b','refuted'),review('c','refuted')],trusted=True)
        s=statistics(g['history'],MODES)['backward'];self.assertEqual((s['credits'],s['adverse']),(1,1))
    def test_inferred_closure(self):
        g=proposed(new('Goal'),'reformulate','a');g=record(g,'forward','a',[claim('b'),dict(op='derive',id='ab',parent='a',premises=['b'],argument='candidate')]);g=record(g,'forward','a',[review('b','established'),dict(op='review_edge',id='ab',decision='accepted',evidence='fixture')],trusted=True)
        self.assertEqual(statistics(g['history'],MODES)['reformulate']['credits'],1)
    def test_rank_distinguishes_equal_review_counts(self):
        g=new('Goal')
        for i in range(3):
            a='a'+str(i);b='b'+str(i);g=proposed(g,'backward',a);g=proposed(g,'forward',b);g=record(g,'falsify','goal',[review(a,'refuted'),review(b,'established')],trusted=True)
        s=statistics(g['history'],MODES);self.assertEqual(s['forward']['credits'],3);self.assertEqual(s['backward']['adverse'],3);self.assertLess(ranking(g['history'],MODES).index('forward'),ranking(g['history'],MODES).index('backward'))
    def test_detached_negative_not_attributed(self):
        g=record(new('Goal'),'forward','goal',[claim('a')]);g=record(g,'falsify','a',[review('a','refuted')],trusted=True);self.assertEqual(statistics(g['history'],MODES)['forward']['adverse'],0)
    def test_unknown_edge_decision_no_credit(self):
        h=[dict(mode='forward',trusted_review=False,operations=[edge('a')]),dict(mode='forward',trusted_review=True,operations=[],verified_items=[['derive','ea']])]
        self.assertEqual(statistics(h,MODES)['forward']['credits'],0)
    def test_untrusted_fake_verified_items_ignored(self):
        g=proposed(new('Goal'),'forward','a');g['history'][0]['verified_items']=[['claim','a']];self.assertEqual(statistics(g['history'],MODES)['forward']['credits'],0)
    def test_checker_noise_does_not_skip_escape_modes(self):
        g=new('Goal')
        for _ in range(3):g=record(g,'backward','goal',[])
        self.assertEqual(plan(g)['mode'],'blind')
        for _ in range(5):g=record(g,'forward','goal',[],trusted=True)
        self.assertEqual(stagnation(g['history']),3);self.assertEqual(plan(g)['mode'],'blind')
        g=record(g,'blind','goal',[]);self.assertEqual(plan(g)['mode'],'reformulate')
    def test_verified_progress_resets_stagnation(self):
        g=proposed(new('Goal'),'backward','a')
        for _ in range(3):g=record(g,'forward','goal',[])
        self.assertEqual(stagnation(g['history']),4)
        g=record(g,'forward','a',[review('a','established')],trusted=True)
        self.assertEqual(stagnation(g['history']),0)
        g=record(g,'forward','goal',[],trusted=True);self.assertEqual(stagnation(g['history']),0)
