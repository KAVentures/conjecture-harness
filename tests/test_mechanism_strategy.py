import unittest
from discovery import new,record
from proof_audit import audit
from mechanism_strategy import rank,statistics,witnesses
from metareasoning import select,research_prompt,annotate
import polynomial as p
import polynomial_lab

def spec(c):
    return dict(variables=['x'],domain='real',relation='nonnegative',terms=[[[2],c]])

class MechanismStrategyTests(unittest.TestCase):
    def test_exact_credit_only(self):
        g=new('unencoded target')
        g=record(g,'reformulate','goal',[dict(op='claim',id='a',statement=p.statement(spec(1))),
            dict(op='derive',id='e',parent='goal',premises=['a'],argument='candidate')])
        g['history'][-1]['research_mechanism']='coordinate-reduction'
        self.assertEqual(statistics(g,audit(g))['coordinate-reduction']['positive'],0)
        g,_=polynomial_lab.discharge(g,'a',spec(1))
        self.assertEqual(statistics(g,audit(g))['coordinate-reduction']['positive'],1)
        self.assertEqual(statistics(g,audit(g))['coordinate-reduction']['negative'],0)
    def test_refutation_witness(self):
        g=new('target')
        g=record(g,'falsify','goal',[dict(op='claim',id='a',statement=p.statement(spec(-1))),
            dict(op='derive',id='e',parent='goal',premises=['a'],argument='candidate')])
        g['history'][-1]['research_mechanism']='equality-analysis'
        g,_=polynomial_lab.discharge(g,'a',spec(-1));r=audit(g)
        self.assertEqual(statistics(g,r)['equality-analysis']['negative'],1)
        self.assertEqual(witnesses(g,r,'goal')[0]['claim'],'a')
        self.assertTrue(rank(g,r,'goal'))
    def test_blind_is_preserved(self):
        g=new('target')
        for _ in range(3):g=record(g,'backward','goal',[])
        p=select(g)
        self.assertEqual(p['mode'],'blind')
        self.assertNotIn('mechanism',p)
        self.assertNotIn('Mechanism:',research_prompt(g,p))

if __name__=='__main__':unittest.main()
