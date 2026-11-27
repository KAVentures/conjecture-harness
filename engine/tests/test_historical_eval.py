import tempfile,unittest,sys
from pathlib import Path
from unittest.mock import patch
import historical_eval as h
from runtime import read_json

class HistoricalTests(unittest.TestCase):
    def setUp(self):
        self.tasks=[dict(id='case',statement='For all integers n, n+n=2n.')]
        self.refs={'case':dict(expected='proved',source='Synthetic test control, not historical',reference='SECRET_REFERENCE')}
    def test_freeze_and_blind(self):
        d=h.freeze(self.tasks,self.refs)
        self.assertNotIn('SECRET_REFERENCE',str(d))
        self.assertNotIn('previous',h.prompt(self.tasks[0],'blind',{'argument':'previous'},1))
        self.assertIn('previous',h.prompt(self.tasks[0],'adaptive',{'argument':'previous'},1))
    def test_run_and_score(self):
        raw=dict(returncode=0,stdout='{"status":"candidate","argument":"By distributivity."}')
        with tempfile.TemporaryDirectory() as td,patch.object(h,'invoke',return_value=raw) as inv:
            out=Path(td)/'run'
            r=h.run(self.tasks,h.freeze(self.tasks,self.refs),[sys.executable],out,calls=2)
            self.assertEqual(r['attempts'],4)
            self.assertEqual(inv.call_count,4)
            self.assertTrue(all('SECRET_REFERENCE' not in c.args[1] for c in inv.call_args_list))
            meta,packet,key,manifest=[read_json(out/x) for x in ('design.json','review-packet.json','private-key.json','run-manifest.json')]
            self.assertTrue(all(set(p)=={'id','statement','answer'} for p in packet))
            reviews=[dict(id=p['id'],sha256=h.digest(p),verdict='proved',reviewer='test fixture',rationale='test only') for p in packet]
            args=(self.tasks,self.refs,meta,packet,key,manifest)
            self.assertEqual(h.score(*args,reviews)['paired']['both'],1)
            with self.assertRaises(ValueError):h.score(*args,reviews[:-1])
            wrong=[dict(reviews[0],verdict='refuted')]+reviews[1:]
            with self.assertRaises(ValueError):h.score(*args,wrong)
    def test_full_engine_final_review(self):
        raw=dict(returncode=0,stdout='{"status":"candidate","argument":"By distributivity."}')
        with tempfile.TemporaryDirectory() as td,patch.object(h,'invoke',return_value=raw) as inv,patch('discovery_run.run') as engine:
            out=Path(td)/'full'
            r=h.run(self.tasks,h.freeze(self.tasks,self.refs),[sys.executable],out,calls=2,full_engine=True)
            self.assertEqual(r['attempts'],3)
            self.assertEqual(inv.call_count,5)
            self.assertEqual(engine.call_count,1)
            meta,packet,key,manifest=[read_json(out/x) for x in ('design.json','review-packet.json','private-key.json','run-manifest.json')]
            self.assertEqual({k['step'] for k in key.values()},{1})
            self.assertEqual({k['arm'] for k in key.values()},set(h.FULL_ARMS))
            reviews=[dict(id=p['id'],sha256=h.digest(p),verdict='proved',reviewer='test fixture',rationale='test only') for p in packet]
            scored=h.score(self.tasks,self.refs,meta,packet,key,manifest,reviews)
            self.assertEqual(scored['summary']['engine']['solved'],1)
            self.assertEqual(scored['engine_pairs']['blind']['both'],1)
            self.assertEqual(len(read_json(out/'usage.json')),3)
    def test_validation(self):
        with self.assertRaises(ValueError):h.freeze(self.tasks,{})
        with self.assertRaises(ValueError):h.validate_tasks([dict(self.tasks[0],solution='leak')])
        self.assertEqual(h.parse_answer(dict(returncode=0,stdout='garbage'))['status'],'abstained')
