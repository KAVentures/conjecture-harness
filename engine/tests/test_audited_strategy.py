import unittest
import polynomial as p
import polynomial_lab,proof_synthesis
from discovery import new,record
from audited_strategy import statistics
from strategy_profile import build

def spec(t):return dict(variables=['x','y'],domain='real',relation='nonnegative',terms=t)
class AuditedStrategyTests(unittest.TestCase):
    def test_manual_not_credited(self):
        g=record(new('goal'),'forward','goal',[dict(op='claim',id='a',statement='unverified'),dict(op='derive',id='e',parent='goal',premises=['a'],argument='candidate')])
        g=record(g,'forward','a',[dict(op='review_claim',id='a',decision='established',evidence='manual')],trusted=True)
        self.assertEqual(statistics(g)['forward']['credits'],0)
        self.assertEqual(next(iter(build([g],audited=True)['targets'].values()))['modes']['forward']['credits'],0)
    def test_verified_goal_route(self):
        x=spec([[[2,0],1]]);y=spec([[[0,2],1]]);goal=spec([[[2,0],2],[[0,2],3]])
        g=record(new(p.statement(goal)),'recombine','goal',[dict(op='claim',id='x',statement=p.statement(x)),dict(op='claim',id='y',statement=p.statement(y)),dict(op='derive',id='e',parent='goal',premises=['x','y'],argument='weighted sum')])
        g,_=polynomial_lab.discharge(g,'x',x)
        g,_=polynomial_lab.discharge(g,'y',y)
        g=proof_synthesis.auto_discharge(g)
        self.assertEqual(statistics(g)['recombine'],dict(attempts=1,credits=1,adverse=0))
    def test_exact_refutation(self):
        x=spec([[[2,0],-1]])
        g=record(new('target'),'backward','goal',[dict(op='claim',id='x',statement=p.statement(x)),dict(op='derive',id='e',parent='goal',premises=['x'],argument='candidate')])
        g,_=polynomial_lab.discharge(g,'x',x)
        self.assertEqual(statistics(g)['backward']['adverse'],1)
        self.assertEqual(statistics(g)['backward']['credits'],0)
