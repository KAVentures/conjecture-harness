import unittest
import critical_pairs as c
import equational as e

class CriticalPairTests(unittest.TestCase):
    def spec(self):
        return dict(variables=['x','y','z'],operations={'f':1,'m':2},axioms=[[['f',['f','x']],'x'],[['f',['m','x','y']],['m',['f','y'],['f','x']]]],conclusion=[['f',['f',['m','x','y']]],['m','x','y']])
    def test_occurs_check(self):
        self.assertIsNone(c.unify('x',('f','x')))
        env=c.unify(('m','x','y'),('m','y',('f','z')))
        self.assertEqual(c.apply('x',env),('f','z'))
    def test_lemmas_and_macro_expansion(self):
        s=self.spec();ls=c.lemmas(s);self.assertTrue(ls)
        for j,x in enumerate(ls):
            self.assertEqual(e.replay(dict(s,conclusion=x['conclusion']),x['certificate']),'proved')
            for d in (0,1):
                target=dict(s,conclusion=x['conclusion'][::(-1 if d else 1)])
                vs=set().union(*(e.variables(e.parse_term(t,s['variables'],s['operations'])) for t in x['conclusion']))
                macro=dict(kind='rewrite-chain',steps=[dict(axiom=len(s['axioms'])+j,direction=d,path=[],substitution={v:v for v in vs})])
                cert=c.expand(target,ls,macro)
                self.assertIsNotNone(cert)
                self.assertEqual(e.replay(target,cert),'proved')
                self.assertTrue(all(st['axiom']<len(s['axioms']) for st in cert['steps']))
    def test_budget(self):
        with self.assertRaises(ValueError):c.lemmas(self.spec(),budget=0)
        self.assertLessEqual(len(c.lemmas(self.spec(),limit=1)),1)
