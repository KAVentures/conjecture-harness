import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import lean_bridge as l
import polynomial as p,conditional_theorems as ct,simplex_discovery as sx,affine

def poly(domain='real',relation='nonnegative'):
    return p.statement(dict(variables=['x','y'],domain=domain,relation=relation,terms=[[[2,0],'1/2'],[[1,1],-1],[[0,2],'1/2']]))
class LeanBridgeTests(unittest.TestCase):
    def test_translation(self):
        src=l.render(poly('nonnegative'),'nlinarith-squares')
        self.assertIn('(x0 x1 : ℝ)',src)
        self.assertIn('(h0 : 0 ≤ x0) (h1 : 0 ≤ x1)',src)
        self.assertIn('((1 : ℝ) / (2 : ℝ))',src)
        self.assertIn('nlinarith [sq_nonneg x0, sq_nonneg x1]',src)
        self.assertIn('#print axioms harness_checked',src)
        with self.assertRaises(ValueError):l.render(poly(),'sorry')
        with self.assertRaises(ValueError):l.render('Informal claim','ring')
    def test_conditional_and_simplex(self):
        s=ct.statement(dict(variables=['x'],domain='real',assumptions=[dict(relation='zero',terms=[[[1],1]])],conclusion=[[[2],1]]))
        self.assertEqual(len(l.formalize(s)['hypotheses']),1)
        self.assertTrue(l.formalize(s)['hypotheses'][0].endswith(' = 0'))
        s=sx.statement(dict(variables=['x','y'],terms=[[[1,0],1]]))
        self.assertEqual(l.formalize(s)['hypotheses'],['0 ≤ x0','0 ≤ x1','x0 + x1 = 1'])
    def test_affine(self):
        s=affine.statement(dict(variables=['x'],assumptions=[[0,1]],conclusion=[0,2]))
        self.assertEqual(len(l.formalize(s)['hypotheses']),1)
    def test_axiom_allowlist(self):
        self.assertEqual(l.axioms("'harness_checked' depends on axioms: [propext, Classical.choice, Quot.sound]"),['Classical.choice','Quot.sound','propext'])
        self.assertEqual(l.axioms("'harness_checked' does not depend on any axioms"),[])
        for x in ("'harness_checked' depends on axioms: [sorryAx]","'harness_checked' depends on axioms: [custom]","'other' does not depend on any axioms",''):
            self.assertIsNone(l.axioms(x))
    def test_verification_mock_only(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'lean-toolchain').write_text('fixture');(root/'lake-manifest.json').write_text('{}')
            result=dict(returncode=0,stdout="'harness_checked' depends on axioms: [propext]",stderr='',termination=None)
            with patch.object(l,'invoke',return_value=result) as m:
                r=l.verify(poly(),root,tactics=['ring'])
                self.assertEqual(r['status'],'lean-verified')
                self.assertEqual(m.call_args.args[0][:3],['lake','env','lean'])
            with patch.object(l,'invoke',return_value=dict(result,stderr='warning: declaration uses sorry')):
                self.assertEqual(l.verify(poly(),root,tactics=['ring'])['status'],'unknown')
            with patch.object(l,'invoke',return_value=dict(result,returncode=1)):
                self.assertEqual(l.verify(poly(),root,tactics=['ring'])['status'],'unknown')
