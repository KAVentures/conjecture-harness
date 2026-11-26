import itertools, random, sys, tempfile, unittest
from pathlib import Path
from fractions import Fraction as F
from runtime import strict_json, invoke
from harness import target_load, parse, attempt, digest
from verify import packing, lih_wang
from certificates import replay
from benchmarks import max_clique, run

class Hardening(unittest.TestCase):
    def test_strict_json(self):
        for text in ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '[1,]']:
            with self.assertRaises(ValueError): strict_json(text)

    def test_timeout(self):
        with tempfile.TemporaryDirectory() as d:
            r=invoke([sys.executable,'-c','import time; time.sleep(30)'],'',.1,d)
            self.assertEqual(r['termination'],'timeout'); self.assertEqual(r['returncode'],124)
            self.assertLess(r['elapsed'],2)

    def test_output_limit(self):
        with tempfile.TemporaryDirectory() as d:
            r=invoke([sys.executable,'-c','print("X"*100000)'],'',2,d,4096)
            self.assertEqual(r['termination'],'output_limit'); self.assertLessEqual(len(r['stdout']),4096)

    def test_spawn_error(self):
        with tempfile.TemporaryDirectory() as d:
            r=invoke(['/definitely-not-a-command'],'',1,d)
            self.assertEqual(r['termination'],'spawn_error')

    def test_target_custom_and_mismatch(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'target.json'; t=target_load('shannon'); t['statement']='A changed theorem'; p.write_text(json.dumps(t))
            with self.assertRaises(ValueError):target_load('shannon',p)
            t['id']='custom'; p.write_text(json.dumps(t)); self.assertEqual(target_load('custom',p),t)
            t['routes']=['a','a']; p.write_text(json.dumps(t))
            with self.assertRaises(ValueError):target_load('custom',p)
        with self.assertRaises(ValueError):target_load('../shannon')

    def test_witness_tampering(self):
        w={'words':[[0],[7]]}; r=packing(w['words']); self.assertTrue(replay('shannon',w,r)['replayed'])
        self.assertFalse(replay('shannon',{'words':[[0],[1]]},r)['replayed'])
        self.assertFalse(replay('shannon',w,{**r,'size':3})['replayed'])
        w={'matrix':[[1,0,0],[0,1,0],[0,0,1]],'t':'1/2'}; r=lih_wang(**w)
        self.assertTrue(replay('lih-wang',w,r)['replayed'])
        self.assertFalse(replay('lih-wang',w,{**r,'lhs_minus_rhs':'123'})['replayed'])

    def test_random_clique_oracle(self):
        rng=random.Random(338)
        for n in range(1,10):
            for _ in range(15):
                adj=[0]*n
                for i,j in itertools.combinations(range(n),2):
                    if rng.random()<rng.random(): adj[i]|=1<<j; adj[j]|=1<<i
                result,_=max_clique(adj)
                expected=max(len(c) for k in range(n+1) for c in itertools.combinations(range(n),k) if all(adj[i]>>j&1 for i,j in itertools.combinations(c,2)))
                self.assertEqual(len(result),expected)
                self.assertTrue(all(adj[i]>>j&1 for i,j in itertools.combinations(result,2)))

    def test_exact_known_powers(self):
        self.assertTrue(all(r['passed'] for r in run()['results']))

    def test_resource_limits(self):
        for words in [[[0]*65], [[0]]*2001]:
            with self.assertRaises(ValueError):packing(words)
        with self.assertRaises(ValueError):lih_wang([['1'*129,0,0],[0,1,0],[0,0,1]],'1/2')

    def test_exact_rational_replay(self):
        rng=random.Random(53)
        for n in range(3,7):
            for _ in range(4):
                a=[[0]*n for _ in range(n)]
                for i in range(3):
                    for r,c in enumerate(rng.sample(range(n),n)): a[r][c]+=1
                w={'matrix':[[str(F(x,3)) for x in row] for row in a],'t':'3/4'}
                self.assertTrue(replay('lih-wang',w,lih_wang(**w))['replayed'])

    def test_reviewer_cannot_solve(self):
        import json
        worker={'kind':'candidate_proof','claim':'False proof','derivation':'Trust me','gaps':[],'next':'none','sources':[],'witness':None}
        audit={'verdict':'survives_review','first_issue':'','tests':[],'unresolved':[]}
        with tempfile.TemporaryDirectory() as d:
            cmd=lambda data:[sys.executable,'-c',f'print({json.dumps(json.dumps(data))})']
            t=target_load('shannon'); r=attempt(t,t['routes'][0],1,True,[],{'worker':cmd(worker),'auditor':cmd(audit),'timeout':2},Path(d))
            self.assertEqual(r['status'],'CANDIDATE_PENDING_FORMAL_OR_EXPERT_CHECK')

if __name__=='__main__':unittest.main()
