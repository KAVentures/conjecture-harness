import unittest
from discovery import new
from proof_audit import audit
import tensor_sos_lab as sos
import indexed_algebra as ia

class TensorSOSLabTests(unittest.TestCase):
    def test_cauchy_schwarz(self):
        ts={'A':{'rank':1,'symmetry':'none'},'B':{'rank':1,'symmetry':'none'}}
        def t(c,fs):return dict(coefficient=c,n_power=0,factors=fs)
        spec=dict(tensors=ts,terms=[
            t(1,[['A',[0]],['A',[0]],['B',[1]],['B',[1]]]),
            t(-1,[['A',[0]],['B',[0]],['A',[1]],['B',[1]]])])
        r=sos.solve(spec)
        self.assertEqual(r['status'],'proved')
        self.assertEqual(sos.replay(spec,r['certificate']),'proved')
        self.assertIn('goal',audit(sos.auto_discharge(new(sos.statement(spec))))['proved'])
        self.assertIsNone(sos.replay(spec,{'squares':[]}))
        bad={'squares':[[-1,r['certificate']['squares'][0][1]]]}
        self.assertIsNone(sos.replay(spec,bad))
    def test_private_indices_independent(self):
        ts={'A':{'rank':2,'symmetry':'none'}}
        sq=dict(free=[0],outer_power=0,terms=[dict(coefficient=1,n_power=0,factors=[['A',[0,1]]])])
        out=sos.expanded(ts,sq)
        self.assertEqual(out['terms'][0]['factors'],[['A',[0,1]],['A',[0,2]]])
        sq['free']=[0,2]
        out=sos.expanded(ts,sq)
        self.assertEqual(out['terms'][0]['n_power'],1)
    def test_false_inequality(self):
        spec=dict(tensors={'A':{'rank':1,'symmetry':'none'}},
                  terms=[dict(coefficient=-1,n_power=0,factors=[['A',[0]],['A',[0]]])])
        r=sos.solve(spec)
        self.assertEqual(r['status'],'counterexample')
        self.assertEqual(sos.replay(spec,r['certificate']),'refuted')
        self.assertIn('goal',audit(sos.auto_discharge(new(sos.statement(spec))))['refuted'])
    def test_incomplete_square_scope(self):
        ts={'A':{'rank':3,'symmetry':'none'}}
        sq=dict(free=[],outer_power=0,terms=[dict(coefficient=1,n_power=0,factors=[['A',[0,1,2]]])])
        with self.assertRaises(ValueError):
            sos.expanded(ts,sq)

if __name__=='__main__':
    unittest.main()
