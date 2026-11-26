import tempfile,unittest,sys
from pathlib import Path
from unittest.mock import patch
import engine_eval as e
import polynomial as p
from historical_eval import digest
from runtime import read_json

class EngineEvalTests(unittest.TestCase):
    def setUp(self):
        self.tasks=[dict(id='control',statement=p.statement(dict(variables=['x'],domain='real',relation='nonnegative',terms=[[[2],1]])))]
        self.refs={'control':dict(expected='proved',source='Synthetic test control',reference='PRIVATE_REFERENCE')}
    def test_matched_and_replayed(self):
        d=e.design(self.tasks,self.refs,calls=2,timeout=2,seconds=10)
        raw=dict(returncode=0,stdout='{"status":"candidate","argument":"A real square is nonnegative."}',stderr='',termination=None)
        with tempfile.TemporaryDirectory() as td,patch.object(e,'invoke',return_value=raw) as inv:
            root=Path(td)/'run'
            r=e.run(self.tasks,d,[sys.executable,'-c','print("[]")'],root)
            self.assertEqual(r['cells'],3)
            # Exact engine closes the control before a proposal call.
            self.assertEqual(inv.call_count,5)
            self.assertTrue(all('PRIVATE_REFERENCE' not in x.args[1] for x in inv.call_args_list))
            packet=read_json(root/'review-packet.json')
            self.assertTrue(all(set(x)=={'id','statement','answer'} for x in packet))
            reviews=[dict(id=x['id'],sha256=digest(x),verdict='proved',reviewer='test fixture',rationale='test only') for x in packet]
            s=e.score(self.tasks,self.refs,root,reviews)
            self.assertEqual(s['summary']['engine']['machine_verified'],1)
            self.assertEqual(s['summary']['engine']['calls'],1)
            self.assertEqual(s['summary']['independent']['calls'],2)
            self.assertEqual(s['paired']['iterative']['both'],1)
            with self.assertRaises(ValueError):e.score(self.tasks,self.refs,root,reviews[:-1])
            k=read_json(root/'private-key.json')
            j=next(v['cell'] for v in k.values() if v['arm']=='engine')
            path=root/'cells'/f'{j:04d}'/'state.json'
            g=read_json(path);g['history'].append({});e.write(path,g)
            with self.assertRaises(ValueError):e.score(self.tasks,self.refs,root,reviews)
    def test_design_validation(self):
        with self.assertRaises(ValueError):e.design(self.tasks,self.refs,calls=1)
        d=e.design(self.tasks,self.refs)
        with self.assertRaises(ValueError):e.validate_design([dict(id='other',statement='different')],d)
    def test_prompt_final(self):
        self.assertIn('final answer',e.worker_prompt('test',[],True))
        self.assertNotIn('old',e.worker_prompt('test'))
        self.assertIn('old',e.worker_prompt('test',{'old':'argument'}))
