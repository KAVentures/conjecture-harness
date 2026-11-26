import unittest,copy,json
from fractions import Fraction as Q
import constrained_tensor_lab as ct
import transport_face_lab as tr
import sharp_ratio_lab as sr
import tensor_recombination as tc
import transport_moment_bridge as tm
import moment_chart_lab as mc
import tensor_sos_lab as ts
from discovery import new,apply,record,plan,prompt
from discovery_run import auto_discharge
from proof_audit import audit
from proof_bundle import export as bundle_export,replay as bundle_replay

def t(c,fs,power=0):return dict(coefficient=c,n_power=power,factors=fs)
def tensor(terms,nn=(),zz=None):
    return dict(tensors={'A':{'rank':2,'symmetry':'none'},'W':{'rank':2,'symmetry':'none'}},terms=terms,nonnegative=list(nn),centered=zz or {})
def ratio(bound):
    return dict(rows=[[1,0],[1,1]],equalities=[],numerator=[2,1],denominator=[1,0],bound=bound)

class DeepInventionTests(unittest.TestCase):
    def test_centered_contraction_identity(self):
        s=tensor([t(-1,[['A',[0,1]],['A',[0,2]]])],zz={'A':[1]})
        self.assertEqual(ct.solve(s)['status'],'proved')
        self.assertIsNone(ct.replay(dict(s,centered={}),{'atoms':[]}))
        # A repeated index is not a singleton; cannot erase sum A_ij^2.
        s=tensor([t(-1,[['A',[0,1]],['A',[0,1]]])],zz={'A':[1]})
        self.assertIsNone(ct.replay(s,{'atoms':[]}))

    def test_weighted_tensor_square(self):
        s=tensor([t(1,[['W',[0,1]],['A',[0,1]],['A',[0,1]]])],nn=['W'])
        atom=dict(free=[0,1],power=0,weight=[['W',[0,1]]],square=[t(1,[['A',[0,1]]])])
        cert=dict(atoms=[['1',atom]])
        self.assertEqual(ct.replay(s,cert),'proved')
        self.assertIsNone(ct.replay(dict(s,nonnegative=[]),cert))
        self.assertIsNone(ct.replay(s,dict(atoms=[['-1',atom]])))
        self.assertEqual(ct.solve(s)['status'],'proved')

    def test_delta_elimination_precedes_centering(self):
        s=tensor([t(1,[['A',[0,1]],['D',[0,1]]])],zz={'A':[1]})
        s['tensors']['D']=dict(rank=2,symmetry='delta')
        self.assertTrue(ct.normal(s))

    def test_tensor_context_transfer(self):
        # Unconstrained sum A^2 is a valid premise under extra constraints.
        fs=[['A',[0,1]],['A',[0,1]]]
        source=ts.statement(dict(tensors=tensor([])['tensors'],terms=[t(1,fs)]))
        goal=ct.statement(tensor([t(2,fs)],nn=['W'],zz={'A':[1]}))
        cert=dict(weights=['2'],atoms=[])
        self.assertTrue(tc.replay(goal,[source],cert))
        restricted=ct.statement(tensor([t(1,[['W',[0,1]]])],nn=['W']))
        free=ct.statement(tensor([t(1,[['W',[0,1]]])]))
        self.assertFalse(tc.replay(free,[restricted],dict(weights=['1'],atoms=[])))

    def test_sharp_signed_ratio(self):
        s=ratio(1);r=sr.solve(s)
        self.assertEqual(r['status'],'proved')
        self.assertTrue(sr.sharp(s,r['certificate'],r['attainment']))
        discovered=sr.discover(ratio(0))
        self.assertEqual(discovered['status'],'sharp')
        self.assertEqual(discovered['bound'],'1')
        self.assertEqual(sr.solve(ratio(2))['status'],'counterexample')
        self.assertIsNone(sr.replay(ratio(2),r['certificate']))
        self.assertFalse(sr.sharp(s,r['certificate'],['1','0']))

    def test_ratio_equality_and_zero_denominator(self):
        s=dict(rows=[],equalities=[[1,-1]],numerator=[1,0],denominator=[0,1],bound=1)
        self.assertEqual(sr.solve(s)['status'],'proved')
        self.assertEqual(sr.discover(s)['status'],'sharp')
        with self.assertRaises(ValueError):sr.normalize(dict(s,denominator=[0,0]))

    def test_transport_cycle_coverage(self):
        # 1-x11^2-x12^2 >=0 on each row of a 2x2 stochastic matrix.
        # The full box fails; curvature is nonpositive on exchange lines.
        s=dict(rows=[1,1],columns=[1,1],terms=[[[0,0,0,0],1],[[2,0,0,0],-1],[[0,2,0,0],-1]])
        r=tr.solve(s);self.assertEqual(r['status'],'proved')
        self.assertEqual(r['certificate']['faces']['****']['kind'],'cycle')
        self.assertEqual(tr.replay(s,r['certificate']),'proved')
        bad=copy.deepcopy(r['certificate']);bad['faces'].pop('0***')
        self.assertIsNone(tr.replay(s,bad))
        bad=copy.deepcopy(r['certificate']);bad['faces']['****']['direction']=['1','0','0','0']
        self.assertIsNone(tr.replay(s,bad))

    def test_transport_counterexample_and_long_cycle(self):
        s=dict(rows=[1,1],columns=[1,1],terms=[[[1,0,0,0],-1]])
        r=tr.solve(s);self.assertEqual(r['status'],'counterexample')
        self.assertIsNone(tr.replay(s,dict(point=['1','1','0','0'])))
        free=[0,1,4,5,6,8]
        dirs=list(tr.directions(3,3,free))
        self.assertTrue(any(sum(v!=0 for v in x)==6 for x in dirs))
        for x in dirs:
            for row in tr.transportation_equalities(3,3):
                self.assertEqual(sum(row[i]*v for i,v in zip(free,x)),0)

    def test_moment_transfer_and_scope(self):
        source=mc.statement(dict(domain='simplex',terms=[[[0,1,0],1],[[2,0,0],-1]]))
        # Non-unit margin: scaling by 1/2 must be accounted for exactly.
        s=dict(rows=['1/2'],columns=['1/4','1/4'],terms=[[[3,0],8],[[0,3],8],[[4,0],-16],[[2,2],-32],[[0,4],-16]])
        goal=tr.statement(s);hit=tm.discover(goal,[source])
        self.assertIsNotNone(hit)
        self.assertTrue(tm.replay(goal,hit['premises'],hit['certificate']))
        self.assertFalse(tm.replay(goal,[],hit['certificate']))
        bad=copy.deepcopy(hit['certificate']);bad['instances'][0][3]='2'
        self.assertFalse(tm.replay(goal,hit['premises'],bad))

    def test_moment_bridge_graph_and_bundle(self):
        source=mc.statement(dict(domain='simplex',terms=[[[0,1,0],1],[[2,0,0],-1]]))
        goal=tr.statement(dict(rows=[1],columns=['1/2','1/2'],terms=[[[3,0],1],[[0,3],1],[[4,0],-1],[[2,2],-2],[[0,4],-1]]))
        g=apply(new(goal),[dict(op='claim',id='source',statement=source)])
        # A source is an audited proof, not an accepted label alone.
        g0=apply(g,[dict(op='review_claim',id='source',decision='established',evidence='unsupported')],trusted=True)
        self.assertEqual(tm.auto_discharge(g0),g0)
        # Reconstruct a real source certificate via the actual solver.
        r=mc.solve(mc.parse_statement(source));self.assertEqual(r['status'],'proved')
        g=record(g,'forward','source',[dict(op='observe',id='moment-chart-source',focus='source',kind='proof_sketch',detail=json.dumps(r)),dict(op='review_claim',id='source',decision='established',evidence='exact source')],trusted=True)
        g=tm.auto_discharge(g)
        self.assertEqual(audit(g)['status'],'proved')
        self.assertTrue(bundle_replay(bundle_export(g),goal))

    def test_ratio_graph_audit(self):
        goal=sr.statement(ratio(1));g=auto_discharge(new(goal))
        self.assertEqual(audit(g)['status'],'proved')
        self.assertTrue(bundle_replay(bundle_export(g),goal))
        self.assertIn('Sharp cone ratio inequality',prompt(new(goal),plan(new(goal)))
        with self.assertRaises(ValueError):
            apply(new(goal),[dict(op='observe',id='transport-moment-fake',focus='goal',kind='transfer',detail='fake')])
