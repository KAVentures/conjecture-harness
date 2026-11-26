import sys, unittest, tempfile, json, random
from pathlib import Path
from fractions import Fraction as F
from itertools import permutations
from harness import choose, target_load, prompt, parse, attempt, read_records, digest
from verify import packing, lih_wang, permanent
ROOT=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
    def test_packing(self):
        self.assertEqual(packing([[0],[7]])['size'],2)
        for x in ([[0],[1]],[[0],[0]],[[True]],[[10]]):
            with self.assertRaises(ValueError):packing(x)
    def test_permanent(self):
        a=[[F(1,3),F(2,3)],[F(2,3),F(1,3)]]
        self.assertEqual(permanent(a),F(5,9))
        for n in range(1,5):
            a=[[F(i+j+1,7) for j in range(n)] for i in range(n)]
            expected=sum((__import__('math').prod(a[i][p[i]] for i in range(n)) for p in permutations(range(n))),F(0))
            self.assertEqual(permanent(a),expected)
    def test_lih_wang(self):
        a=[[1,0,0],[0,1,0],[0,0,1]]
        self.assertFalse(lih_wang(a,'1/2')['verified_counterexample'])
        self.assertEqual(lih_wang(a,'1')['lhs_minus_rhs'],'0')
        for t in ('1/3',.5):
            with self.assertRaises(ValueError):lih_wang(a,t)
        with self.assertRaises(ValueError):lih_wang([[1,0,0]]*3,'1/2')
    def test_routes(self):
        routes=target_load('shannon')['routes']; result=choose(routes,[],random.Random(17),4)
        self.assertEqual(len(set(result)),4)
        self.assertEqual(result,choose(routes,[],random.Random(17),4))
    def test_blind(self):
        t=target_load('shannon'); prior=[{'route':'x','result':'SECRET'}]
        self.assertNotIn('SECRET',prompt(t,'x',1,True,prior)); self.assertIn('SECRET',prompt(t,'x',1,False,prior))
    def test_invalid_response(self):
        with self.assertRaises(ValueError):parse({'returncode':0,'stdout':'not json'})
        with self.assertRaises(ValueError):parse({'returncode':0,'stdout':'{"kind":"lemma"}'})
    def test_pipeline(self):
        t=target_load('shannon'); cmd=[sys.executable,str(ROOT/'mock_agent.py')]
        with tempfile.TemporaryDirectory() as d:
            base=Path(d); r=attempt(t,t['routes'][0],1,True,[],{'worker':cmd,'auditor':cmd,'timeout':10},base)
            self.assertEqual(r['status'],'GAP_OR_REJECTED'); self.assertEqual(r['target_sha256'],digest(t)); self.assertEqual(len(read_records(base,t)),1)
            t['statement']+=' changed'; self.assertEqual(read_records(base,t),[])
if __name__=='__main__':unittest.main()
