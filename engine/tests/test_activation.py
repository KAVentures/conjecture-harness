import json
import tempfile
import unittest
from pathlib import Path
from activation_contract import ROOT, contract, digest, registry, suggest, worker_contract
from activate import plan, execute

class ActivationTests(unittest.TestCase):
    def test_routes_and_docs(self):
        for r in registry()['routes']:
            for doc in r['docs']:
                self.assertTrue((ROOT/doc).is_file(),doc)
        self.assertIn('matrix',[r['id'] for r in suggest('Lih–Wang permanent conjecture')])
        self.assertEqual([r['id'] for r in suggest('unclassified problem')],['general'])
        self.assertEqual(plan('a target')['contract_sha256'],digest(contract()))
        self.assertIn('proposal worker',worker_contract())
        from activation_contract import public_contract
        self.assertEqual(plan('a target')['public_contract_sha256'],digest(public_contract()))

    def test_shared_worker_prompt(self):
        from discovery import new, prompt
        g=new('a target')
        p=prompt(g,{'mode':'blind','focus':'goal'})
        self.assertIn(worker_contract(),p)
        self.assertIn('Return JSON list',p)

    def test_run_resume_and_no_fake_model(self):
        from polynomial import statement
        target=statement({'variables':['x'],'domain':'real','relation':'nonnegative','terms':[[[2],1]]})
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'run'
            a=execute(root,target,passes=1,seconds=10)
            self.assertEqual(a['exact_execution']['model_calls'],0)
            self.assertEqual(a['worker_logs'],[])
            self.assertIsNone(a['model_execution'])
            self.assertTrue((root/a['checkpoint']).is_file())
            b=execute(root,passes=1,seconds=10)
            self.assertEqual(a['state_sha256'],b['prior_state_sha256'])
            self.assertTrue((root/'receipt-0001.json').is_file())
            self.assertEqual(b['checkpoint_sha256'],digest((root/b['checkpoint']).read_bytes()))
            with self.assertRaises(FileExistsError):execute(root,target)
            initial=json.loads((root/'activation.json').read_text())
            initial['target_sha256']='bad'
            (root/'activation.json').write_text(json.dumps(initial))
            with self.assertRaises(ValueError):execute(root)

    def test_reject_bad_inputs(self):
        with self.assertRaises(ValueError):plan(' ')
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):execute(Path(d)/'run','x',worker='not an argv')
