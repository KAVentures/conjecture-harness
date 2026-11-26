import itertools,unittest
from graph_lemma import validate,statement,properties,independent,replay,search
from lemma_lab import falsify
from discovery import new,apply,plan

BAD=dict(min_n=1,properties=['connected'],coefficients={'alpha':1,'n':-1},constant=0)
TRUE=dict(min_n=1,properties=[],coefficients={'n':1,'alpha':-1},constant=0)

class GraphLabTests(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(statement(BAD),statement(dict(BAD,coefficients={'alpha':2,'n':-2})))
    def test_oracles(self):
        for n in range(1,5):
            ps=list(itertools.combinations(range(n),2))
            for mask in range(1<<len(ps)):
                e=[list(x) for i,x in enumerate(ps) if mask>>i&1]
                self.assertEqual(properties(n,e),independent(n,e))
    def test_counterexample(self):
        r=search(BAD);self.assertEqual(r['status'],'counterexample');self.assertEqual(r['witness'],{'n':2,'edges':[[0,1]]});self.assertTrue(replay(BAD,r['witness'])['counterexample'])
    def test_survival(self):
        r=search(TRUE,4);self.assertEqual(r['status'],'no_counterexample_in_scope');self.assertEqual(r['tested'],75);self.assertFalse(r['universal_proof'])
    def test_budget(self):
        r=search(TRUE,6,2);self.assertEqual(r['status'],'budget_exhausted');self.assertEqual(r['tested'],2);self.assertEqual(r['complete_through'],1)
    def test_empty(self):
        self.assertEqual(search(dict(TRUE,min_n=7))['status'],'empty_scope')
    def test_invalid(self):
        for s in (dict(TRUE,min_n=True),dict(TRUE,coefficients={'n':True}),dict(TRUE,properties=['bad']),dict(TRUE,constant=1.2)):
            with self.assertRaises(ValueError):validate(s)
        for e in ([[0,0]],[[1,0]],[[0,1],[0,1]],[[0,True]]):
            with self.assertRaises(ValueError):replay(BAD,{'n':2,'edges':e})
    def test_claim_binding(self):
        g=new('different mathematical statement')
        with self.assertRaises(ValueError):falsify(g,'goal',BAD)
        g=new(statement(BAD));h,r=falsify(g,'goal',BAD);self.assertEqual(h['nodes']['goal']['status'],'refuted');self.assertEqual(g['nodes']['goal']['status'],'open');self.assertTrue(plan(h).get('stop'))
    def test_survival_does_not_close(self):
        g=new(statement(TRUE));h,r=falsify(g,'goal',TRUE,4);self.assertEqual(h['nodes']['goal']['status'],'open');self.assertEqual(h['history'][-1]['reward'],0);self.assertEqual(falsify(h,'goal',TRUE,4)[0],h)
    def test_auxiliary_refutation(self):
        g=apply(new('Target'),[{'op':'claim','id':'aux','statement':statement(BAD)},{'op':'derive','id':'bridge','parent':'goal','premises':['aux'],'argument':'Candidate bridge'}]);h,r=falsify(g,'aux',BAD);self.assertEqual(h['nodes']['goal']['status'],'open');self.assertEqual(h['nodes']['aux']['status'],'refuted');self.assertEqual(plan(h)['mode'],'refine')
    def test_families_complete_and_unique(self):
        r=search(TRUE,4,40000,'families_first');self.assertEqual(r['tested'],75);self.assertEqual(r['complete_through'],4)
    def test_families_find_dense_witness(self):
        s=dict(min_n=5,properties=['connected'],coefficients={'omega':-1},constant=-3)
        self.assertNotEqual(search(s,5,16,'exhaustive')['status'],'counterexample');self.assertEqual(search(s,5,16,'families_first')['status'],'counterexample')
