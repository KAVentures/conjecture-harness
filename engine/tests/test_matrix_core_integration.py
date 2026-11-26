"""Ensure the matrix adapter survives integration with the core engine."""
import unittest
import matrix_permanent as m
from certificate_registry import DIRECT, RESERVED
from discovery import new, apply, prompt, plan
from discovery_run import auto_discharge
from proof_audit import audit
from knowledge_bank import export, import_facts
from proof_bundle import export as bundle_export, replay as bundle_replay

class MatrixCoreIntegrationTests(unittest.TestCase):
    def test_matrix_pipeline_and_portable_proof(self):
        text=m.statement(dict(kind='lih-wang',matrix=[[1,0,0],[0,'1/2','1/2'],[0,'1/2','1/2']]))
        g=auto_discharge(new(text))
        self.assertEqual(audit(g)['status'],'proved')
        self.assertIn('matrix-',DIRECT)
        self.assertIn('matrix-',RESERVED)
        b=export(g)
        self.assertTrue(any(f['prefix']=='matrix-' for f in b['facts']))
        h,_=import_facts(new(text),b)
        self.assertEqual(audit(h)['status'],'proved')
        self.assertTrue(bundle_replay(bundle_export(g),text))
    def test_matrix_bridge_without_verified_premise(self):
        text=m.statement(dict(kind='lih-wang'))
        premise=m.statement(dict(kind='signed-prefix'))
        g=apply(new(text),[dict(op='claim',id='prefix',statement=premise),dict(op='derive',id='abel',parent='goal',premises=['prefix'],argument='Typed Abel summation'),dict(op='review_edge',id='abel',decision='accepted',evidence='Typed sufficient condition')],trusted=True)
        a=audit(g)
        self.assertEqual(a['checked_edges']['abel'],'typed Abel summation')
        self.assertEqual(a['status'],'unverified')
        self.assertIn('signed-prefix',prompt(new(text),plan(new(text))))
