import json,unittest
import polynomial as p
import polynomial_lab
from discovery import new,record,apply,closure
from metareasoning import diagnose,select,research_prompt,strategies,annotate

def spec(t):return dict(variables=['x'],domain='real',relation='nonnegative',terms=t)
def claim(i,s):return dict(op='claim',id=i,statement=s)
def edge(i,parent,premises):return dict(op='derive',id=i,parent=parent,premises=premises,argument='candidate implication')
class MetareasoningTests(unittest.TestCase):
    def test_ready_bridge(self):
        x=spec([[[2],1]])
        g=record(new('Unencoded target'),'backward','goal',[claim('a',p.statement(x)),edge('e','goal',['a'])])
        g,_=polynomial_lab.discharge(g,'a',x)
        d=diagnose(g);self.assertEqual(d['ready_bridges'][0]['edge'],'e')
        plan=select(g);self.assertEqual(plan['bridge'],'e')
        self.assertEqual(plan['intervention'],'verify-ready-implication')
        self.assertNotIn('goal',closure(g))
    def test_manual_not_verified(self):
        g=apply(new('target'),[claim('a','manual lemma'),edge('e','goal',['a']),dict(op='review_claim',id='a',decision='established',evidence='manual')],trusted=True)
        self.assertEqual(diagnose(g)['recorded_only_claims'],['a'])
        self.assertFalse(diagnose(g)['ready_bridges'])
    def test_refuted_route(self):
        x=spec([[[2],-1]])
        g=record(new('target'),'backward','goal',[claim('a',p.statement(x)),edge('e','goal',['a'])])
        g,_=polynomial_lab.discharge(g,'a',x)
        self.assertEqual(diagnose(g)['failed_routes'][0]['exact_refutations'],['a'])
        self.assertEqual(select(g)['focus'],'goal')
    def test_card_used_once_and_blind(self):
        g=new('target');card=dict(research_strategy=dict(mode='reformulate',mechanism='new representation',test='derive identity',rationale='test a new invariant'))
        g=record(g,'backward','goal',[dict(op='observe',id='o',focus='goal',kind='refinement',detail=json.dumps(card))])
        g=record(g,'forward','goal',[])
        self.assertEqual(len(strategies(g)),1)
        plan=select(g);self.assertEqual(plan['intervention'],'proposed-strategy')
        h=annotate(record(g,plan['mode'],plan['focus'],[]),plan)
        self.assertFalse(strategies(h));blind=select(h)
        self.assertEqual(blind['mode'],'blind')
        self.assertNotIn('new representation',research_prompt(h,blind))
    def test_recorded_closure_requires_review(self):
        g=apply(new('target'),[dict(op='review_claim',id='goal',decision='established',evidence='manual')],trusted=True)
        self.assertIn('lacks independent replay',select(g)['stop'])
