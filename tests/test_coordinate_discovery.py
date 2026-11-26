import unittest
from discovery import new
from proof_audit import audit
import affine_face_lab as face
import affine_chart_lab as chart
import homogeneous_lab as hom

class CoordinateDiscoveryTests(unittest.TestCase):
    def test_affine_chart_proof(self):
        # -(x-y)^2 + (x-1/2)^2 >= 0 whenever x=y.
        s=dict(dimension=2,rows=[[1,-1]],rhs=[0],
               terms=[[[0,0],'1/4'],[[1,0],-1],[[1,1],2],[[0,2],-1]])
        r=chart.solve(s)
        self.assertEqual(r['status'],'proved')
        self.assertEqual(chart.replay(s,r['certificate']),'proved')
        g=chart.auto_discharge(new(face.statement(s)))
        self.assertIn('goal',audit(g)['proved'])
        self.assertIsNone(chart.replay(dict(s,rhs=['1/4']),r['certificate']))
        bad=dict(r['certificate'],order=[0,0])
        self.assertIsNone(chart.replay(s,bad))
    def test_eliminated_bounds_retained(self):
        # x+y=1/2; x*y>=0 follows from both original bounds.
        s=dict(dimension=2,rows=[[1,1]],rhs=['1/2'],terms=[[[1,1],1]])
        r=chart.solve(s)
        self.assertEqual(r['status'],'proved')
        self.assertEqual(chart.replay(s,r['certificate']),'proved')
        self.assertIsNone(chart.replay(dict(s,rhs=['-1/2']),r['certificate']))
    def test_homogeneous_real(self):
        s=dict(dimension=2,degree=2,domain='real',terms=[[[2,0],1],[[1,1],-2],[[0,2],1]])
        r=hom.solve(s)
        self.assertEqual(r['status'],'proved')
        self.assertEqual(hom.replay(s,r['certificate']),'proved')
        self.assertIn('goal',audit(hom.auto_discharge(new(hom.statement(s))))['proved'])
        self.assertIsNone(hom.replay(s,{'charts':r['certificate']['charts'][:-1]}))
    def test_homogeneous_signs(self):
        s=dict(dimension=2,degree=1,domain='nonnegative',terms=[[[1,0],1]])
        self.assertEqual(hom.solve(s)['status'],'proved')
        s['domain']='real';r=hom.solve(s)
        self.assertEqual(r['status'],'counterexample')
        self.assertEqual(hom.replay(s,r['certificate']),'refuted')
    def test_nonhomogeneous_rejected(self):
        with self.assertRaises(ValueError):
            hom.statement(dict(dimension=2,degree=2,domain='real',terms=[[[1,0],1]]))

if __name__=='__main__':unittest.main()
