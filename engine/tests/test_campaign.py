import json
import unittest
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory
import campaign

def audit(status='unverified', proved=None, checked=None, invalid=None, conflicts=None):
    return dict(status=status,proved=proved or {},refuted={},checked_edges=checked or {},
                invalid_observations=invalid or [],conflicts=conflicts or [])

class CampaignTests(unittest.TestCase):
    def test_completion_requires_clean_exact_root(self):
        self.assertFalse(campaign.verified(audit()))
        self.assertTrue(campaign.verified(audit('proved',{'goal':'certificate'})))
        self.assertTrue(campaign.verified(audit('refuted')))
        self.assertFalse(campaign.verified(audit('proved',invalid=['bad'])))
        self.assertEqual(campaign.disposition(audit('conflict',conflicts=['goal'])),'integrity_review_required')

    def test_detached_progress_not_rewarded(self):
        g={'edges':{'e':{'parent':'goal','premises':['a']}}}
        self.assertEqual(campaign.target_evidence(g,audit(proved={'a':'cert'}))[0],set())
        self.assertEqual(campaign.target_evidence(g,audit(proved={'a':'cert'},checked={'e':'cert'}))[0],{'a'})

    def test_candidate_not_ordinary_sketch(self):
        g={'target_sha256':'target','observations':{
            'a':{'focus':'goal','kind':'proof_sketch','detail':'routine lemma'},
            'b':{'focus':'goal','kind':'proof_sketch','detail':json.dumps({'complete_candidate':{'kind':'proof','argument':'candidate'}})},
            'c':{'focus':'sub','kind':'proof_sketch','detail':json.dumps({'complete_candidate':{'kind':'proof','argument':'other'}})}}}
        self.assertEqual([x['id'] for x in campaign.candidates(g)],['b'])
        self.assertFalse(campaign.verified(audit()))

    def test_review_schema_and_binding(self):
        r=dict(target_sha256='t',candidate_sha256='c',verdict='pass',critique='checked')
        raw=dict(returncode=0,stdout=json.dumps(r))
        self.assertEqual(campaign.parse_review(raw,'t','c')['verdict'],'pass')
        self.assertEqual(campaign.parse_review(raw,'t','wrong')['verdict'],'uncertain')
        self.assertEqual(campaign.parse_review(dict(returncode=1),'t','c')['verdict'],'uncertain')

    def test_waves_continue_and_resume_with_root_pivot(self):
        from discovery import new,save
        with TemporaryDirectory() as tmp:
            state=Path(tmp)/'state.json';save(state,new('Unresolved prose target'))
            calls=[]
            def fake(*args,**kwargs):
                calls.append(kwargs)
                return dict(launched=args[2],next={})
            with patch('discovery_portfolio.run',side_effect=fake),patch('proof_audit.audit',return_value=audit()):
                r=campaign.run(state,[['trusted']],4,10,1,1,2)
                self.assertEqual(r['launched'],4)
                self.assertEqual(r['stagnant_waves'],2)
                self.assertEqual(r['reason'],'attempt_limit')
                r=campaign.run(state,[['trusted']],2,10,1,1,2)
                self.assertTrue(calls[-1]['force_root'])
                self.assertEqual(r['waves'],3)
                self.assertEqual(r['disposition'],'unresolved')

    def test_no_launch_does_not_spin(self):
        from discovery import new,save
        with TemporaryDirectory() as tmp:
            state=Path(tmp)/'state.json';save(state,new('Unresolved prose target'))
            with patch('discovery_portfolio.run',return_value={'launched':0}),patch('proof_audit.audit',return_value=audit()):
                r=campaign.run(state,[['trusted']],100,10,1)
                self.assertEqual(r['reason'],'operator_review_required')
                self.assertEqual(r['waves'],1)

    def test_compact_stdout_no_partial_lemmas(self):
        r=campaign.public_result(dict(audit=audit(proved={'sub':'certificate'}),activation={'target':'T'},checkpoint='checkpoint.json',elapsed_seconds=2,campaign_execution={'reason':'attempt_limit','launched':10}))
        self.assertEqual(r['status'],'unresolved')
        self.assertNotIn('sub',json.dumps(r))

if __name__=='__main__':unittest.main()
