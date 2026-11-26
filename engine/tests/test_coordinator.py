import contextlib, io, json, random, sys, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from harness import coordinator_lock, run_rounds, read_records, target_load, choose

class CoordinatorTests(unittest.TestCase):
    def test_lock(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            with coordinator_lock(p):
                with self.assertRaises(RuntimeError):
                    with coordinator_lock(p): pass
            self.assertFalse((p/'.coordinator.lock').exists())

    def test_resume_and_budget(self):
        cmd=[sys.executable,str(Path(__file__).resolve().parent/'mock_agent.py')]
        a=SimpleNamespace(max_seconds=10,max_attempts=3,rounds=2,workers=2,seed=19)
        t=target_load('shannon')
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)
            with contextlib.redirect_stdout(io.StringIO()):
                run_rounds(t,base,{'worker':cmd,'auditor':cmd,'timeout':2},a)
            self.assertEqual([r['sequence'] for r in read_records(base,t)],[0,1,2])
            with contextlib.redirect_stdout(io.StringIO()):
                run_rounds(t,base,{'worker':cmd,'auditor':cmd,'timeout':2},a)
            self.assertEqual([r['sequence'] for r in read_records(base,t)],list(range(6)))

    def test_unreplayed_claim_not_rewarded(self):
        routes=['a','b']; rng=random.Random(5)
        records=[{'route':'a','valid':True,'exact':{'verified_counterexample':True}}, {'route':'b','valid':True}]
        self.assertEqual(choose(routes,records,rng,2),choose(routes,[{'route':'a','valid':True},{'route':'b','valid':True}],random.Random(5),2))
