import unittest
from discovery import new,apply,closure,plan,prompt,record
from proof_frontier import routes


def claim(i,s):return dict(op='claim',id=i,statement=s)
def edge(i,p,ps):return dict(op='derive',id=i,parent=p,premises=ps,argument='Conditional bridge')
def review(i,d,edge=False):return dict(op='review_edge' if edge else 'review_claim',id=i,decision=d,evidence='Test fixture')

class FrontierTests(unittest.TestCase):
    def test_case_sensitive_math(self):
        g=apply(new('Goal'),[claim('a','delta >= 2'),claim('b','Delta >= 2')]);self.assertEqual(len(g['nodes']),3)
    def test_shorter_reviewed_route(self):
        g=apply(new('Goal'),[claim('a','A'),claim('b','B'),claim('c','C'),edge('long','goal',['a','b']),edge('short','goal',['c'])]);g=apply(g,[review('short','accepted',True)],trusted=True)
        self.assertEqual(routes(g,closure(g))[0]['edge'],'short');self.assertEqual(plan(g)['focus'],'c')
    def test_ready_bridge(self):
        g=apply(new('Goal'),[claim('a','A'),edge('bridge','goal',['a'])]);g=apply(g,[review('a','established')],trusted=True)
        p=plan(g);self.assertEqual(p['bridge'],'bridge');self.assertIn('derive or challenge',prompt(g,p));self.assertNotIn('goal',closure(g))
    def test_shared_claim_counts_once(self):
        g=apply(new('Goal'),[claim('a','A'),claim('b','B'),claim('c','C'),edge('both','goal',['a','b']),edge('ac','a',['c']),edge('bc','b',['c'])]);r=routes(g,closure(g))[0];self.assertEqual(r['claims'],['c']);self.assertEqual(r['estimated_cost'],4)
    def test_refuted_route_removed(self):
        g=apply(new('Goal'),[claim('a','A'),claim('b','B'),edge('first','goal',['a']),edge('second','goal',['b'])]);g=record(g,'falsify','a',[review('a','refuted')],trusted=True);self.assertEqual([r['edge'] for r in routes(g,closure(g))],['second']);self.assertEqual(plan(g)['focus'],'goal')
    def test_visit_penalty(self):
        g=apply(new('Goal'),[claim('a','A'),claim('b','B'),edge('first','goal',['a']),edge('second','goal',['b'])]);g=record(g,'backward','a',[]);self.assertEqual(routes(g,closure(g))[0]['edge'],'second')
