import unittest
from discovery import new
from proof_audit import audit
import affine_face_lab as face
import inductive_lab as ind

class RecursiveDiscoveryTests(unittest.TestCase):
    def test_face_reduction(self):
        # x(1-x)-(x+y-1)^2 >= 0 on x+y=1. It is negative on parts of the box.
        s=dict(dimension=2,rows=[[1,1]],rhs=[1],
               terms=[[[0,0],-1],[[1,0],3],[[0,1],2],[[2,0],-2],[[0,2],-1],[[1,1],-2]])
        r=face.solve(s)
        self.assertEqual(r['status'],'proved')
        c=r['certificate']
        self.assertEqual(c['faces']['**']['kind'],'split')
        self.assertEqual(face.replay(s,c),'proved')
        self.assertIn('goal',audit(face.auto_discharge(new(face.statement(s))))['proved'])
        bad={'faces':dict(c['faces'])}
        del bad['faces'][next(k for k in bad['faces'] if k!='**')]
        self.assertIsNone(face.replay(s,bad))
    def test_infeasible_and_unique(self):
        s=dict(dimension=1,rows=[[1]],rhs=[2],terms=[[[0],-1]])
        self.assertEqual(face.solve(s)['status'],'proved')
        s['rhs']=[0]
        self.assertEqual(face.solve(s)['status'],'unknown')
    def test_recursion_two_dimensions(self):
        # Concave objective x+y-x^2-y^2, shifted by a vanishing affine term.
        s=dict(dimension=3,rows=[[1,1,1]],rhs=[1],
            terms=[[[0,0,0],-1],[[1,0,0],2],[[0,1,0],2],[[0,0,1],1],
                   [[2,0,0],-1],[[0,2,0],-1]])
        r=face.solve(s)
        self.assertEqual(r['status'],'proved')
        self.assertEqual(face.replay(s,r['certificate']),'proved')
    def test_induction_invents_auxiliary(self):
        # x'=x+y; y'=y; x,y start at 0,1. x>=0 needs auxiliary y>=0.
        s=dict(matrix=[[[1],[1]],[[],[1]]],offset=[[],[]],initial=[0,1],goal=[[],[1],[]])
        r=ind.solve(s)
        self.assertEqual(r['status'],'proved')
        self.assertTrue(r['certificate']['auxiliary'])
        self.assertEqual(ind.replay(s,r['certificate']),'proved')
        self.assertIn('goal',audit(ind.auto_discharge(new(ind.statement(s))))['proved'])
        bad=dict(r['certificate'],auxiliary=[])
        self.assertIsNone(ind.replay(s,bad))
    def test_false_induction(self):
        s=dict(matrix=[[[1]]],offset=[[-1]],initial=[0],goal=[[],[1]])
        self.assertEqual(ind.solve(s)['status'],'unknown')

if __name__=='__main__':
    unittest.main()
