import unittest,copy,tempfile,json
from pathlib import Path
from fractions import Fraction as Q
from math import comb,factorial
import rational_gf_lab as gf
import beta_integral_lab as bi
import binomial_expectation_lab as be
import stationary_transport_lab as st
import transport_face_lab as tr
import proof_compression as pc
import constrained_tensor_lab as ct
import tensor_witness_repair as tw
from discovery import new,apply,record
from proof_audit import audit
from proof_bundle import export as bundle_export,replay as bundle_replay

class GlobalInventionTests(unittest.TestCase):
    def test_signed_gf_infinite_induction(self):
        s=dict(numerator=[1],denominator=[1,-3,2])
        r=gf.solve(s);self.assertEqual(r['status'],'proved')
        self.assertEqual(gf.replay(s,r['certificate']),'proved')
        self.assertEqual(gf.coeffs(*gf.data(s),20),[Q(2**(n+1)-1) for n in range(21)])
        bad=copy.deepcopy(r['certificate']);bad['steps'][0]=['0']*len(bad['rows'])
        self.assertIsNone(gf.replay(s,bad))

    def test_gf_refutation_and_scope(self):
        s=dict(numerator=[1],denominator=[1,1])
        r=gf.solve(s);self.assertEqual(r['status'],'counterexample')
        self.assertEqual(gf.replay(s,r['certificate']),'refuted')
        self.assertIsNone(gf.replay(s,dict(index=0)))
        self.assertIsNone(gf.replay(dict(numerator=[1],denominator=[1,-1]),r['certificate']))

    def test_beta_integrals_exact_factorials(self):
        for a,b in (([0,1],[0,1]),([0,2],[0,1]),([0,1],[0,2])):
            s=dict(left=a,right=b,polynomial=['-1/2',1],start=0)
            q=bi.numerator(s)
            for n in range(10):
                u=a[0]+a[1]*n;v=b[0]+b[1]*n
                beta=lambda j:Q(factorial(u+j)*factorial(v),factorial(u+v+j+1))
                self.assertEqual(sum(w*n**i for i,w in enumerate(q)),(beta(1)-beta(0)/2)/beta(0)*(u+v+2))
            r=bi.solve(s);expected='counterexample' if b[1]>a[1] else 'proved'
            self.assertEqual(r['status'],expected)
            self.assertEqual(bi.replay(s,r['certificate']),'refuted' if expected=='counterexample' else 'proved')

    def test_binomial_expectation_exact_transform(self):
        s=dict(start=0,terms=[[[0,2],1],[[0,1],-1]])
        q=be.transformed(s)
        self.assertEqual(q,{(2,2):Q(1),(1,2):Q(-1)})
        for n in range(9):
            for t in (Q(0),Q(1,3),Q(1)):
                expected=sum(comb(n,k)*t**k*(1-t)**(n-k)*k*(k-1) for k in range(n+1))
                self.assertEqual(sum(v*n**a*t**b for (a,b),v in q.items()),expected)
        r=be.solve(s);self.assertEqual(r['status'],'proved')
        self.assertEqual(be.replay(s,r['certificate']),'proved')
        bad=dict(start=0,terms=[[[0,1],-1]])
        r=be.solve(bad);self.assertEqual(r['status'],'counterexample')
        self.assertEqual(be.replay(bad,r['certificate']),'refuted')

    def test_stationarity_not_concavity(self):
        s=dict(rows=[1,1],columns=[1,1],terms=[[[2,0,0,0],1],[[1,1,0,0],-2],[[0,2,0,0],1]])
        r=st.solve(s);self.assertEqual(r['status'],'proved')
        self.assertEqual(st.replay(s,r['certificate']),'proved')
        self.assertEqual(r['certificate']['stationary-faces']['****']['kind'],'stationary')
        bad=copy.deepcopy(r['certificate'])
        child=next(k for k in bad['stationary-faces'] if k!='****');del bad['stationary-faces'][child]
        self.assertIsNone(st.replay(s,bad))

    def test_symmetry_requires_objective_and_margin(self):
        s=dict(rows=[1,1],columns=[1,1],terms=[[[1,0,0,0],1],[[0,1,0,0],1]])
        self.assertEqual(st.quotient(s)('0***'),st.quotient(s)('*0**'))
        s['terms']=[[[1,0,0,0],1]]
        self.assertNotEqual(st.quotient(s)('0***'),st.quotient(s)('*0**'))

    def test_audit_aware_compression(self):
        g=apply(new('target'),[dict(op='claim',id=i,statement=i) for i in ('a','b','c')]+[
            dict(op='derive',id='ab',parent='goal',premises=['a','b'],argument='candidate'),
            dict(op='derive',id='ac',parent='a',premises=['c'],argument='candidate'),
            dict(op='derive',id='bc',parent='b',premises=['c'],argument='candidate')])
        g=apply(g,[dict(op='review_claim',id='c',decision='established',evidence='manual only')],trusted=True)
        r=pc.compress(g,audit(g))
        self.assertTrue(any(x['claims']==['c'] and set(x['bridges'])=={'ab','ac','bc'} for x in r))
        self.assertTrue(any(x['claims']==['goal'] for x in r))
        self.assertFalse(any(not x['claims'] and not x['bridges'] for x in r))

    def test_integrated_run_and_portable_audit(self):
        from research_run import execute
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'result';target=gf.statement(dict(numerator=[1],denominator=[1,-1]))
            result=execute(target,out,passes=2,seconds=30)
            self.assertEqual(result['audit']['status'],'proved')
            self.assertEqual(result['proof_bundle'],'proof-bundle.json')
            self.assertTrue(bundle_replay(json.loads((out/'proof-bundle.json').read_text()),target))
            self.assertTrue((out/'state.json').is_file())

    def test_tensor_repair_does_not_close_premises(self):
        # T = sum A_i^2 + sum W_i^2, F = sum A_i^2 - sum W_i^2.
        ts={'A':dict(rank=1,symmetry='none'),'W':dict(rank=1,symmetry='none')}
        def term(c,name):return dict(coefficient=c,n_power=0,factors=[[name,[0]],[name,[0]]])
        def spec(terms):return dict(tensors=ts,centered={},nonnegative=[],terms=terms)
        target=ct.statement(spec([term(1,'A'),term(1,'W')]))
        failed=ct.statement(spec([term(1,'A'),term(-1,'W')]))
        w=dict(n=1,arrays={'A':['0'],'W':['1']})
        self.assertEqual(ct.replay(ct.parse_statement(failed),w),'refuted')
        hits=tw.repair(target,failed,w)
        self.assertTrue(hits)
        from tensor_recombination import replay
        self.assertTrue(all(replay(target,h['premises'],h['certificate']) for h in hits))
        self.assertFalse(tw.repair(target,failed,dict(n=1,arrays={'A':['1'],'W':['0']})))

    def test_exact_root_structure(self):
        import root_structure_lab as rs
        s=dict(kind='nonpositive-roots',p=[0,1,2,1])
        r=rs.solve(s);self.assertEqual(r['status'],'proved')
        self.assertEqual(rs.replay(s,r['certificate']),'proved')
        self.assertIsNone(rs.replay(dict(kind='nonpositive-roots',p=[1,0,1]),r['certificate']))
        self.assertIsNone(rs.replay(dict(kind='nonpositive-roots',p=[-1,1]),r['certificate']))
        s=dict(kind='strict-interlacing',p=[-1,0,1],q=[0,1])
        r=rs.solve(s);self.assertEqual(r['status'],'proved')
        self.assertIsNone(rs.replay(dict(s,q=[-2,1]),r['certificate']))
        self.assertEqual(rs.solve(dict(s,p=[0,0,1]))['status'],'unknown')
