import unittest
from fractions import Fraction as Q
from combinatorial_invention import centered_contractions,matching_coefficients,recurrence_residual
from inequality_invention import discover,replay,replay_gram,gram_squares
from affine_extremal_invention import nullspace,discover_directions,verify_direction,endpoints
from theorem_network import plan,evaluate

class GeneralInventionTests(unittest.TestCase):
    def test_grouped_second_third(self):
        self.assertEqual(centered_contractions(2),{((2,),):1})
        self.assertEqual(centered_contractions(3),{((3,),):4})
    def test_sixth_order(self):
        c=centered_contractions(6)
        self.assertEqual(c[((6,),)],14400)
        self.assertGreater(len(c),5)
    def test_matching(self):
        a=[[1,2],[3,4]]
        self.assertEqual(matching_coefficients(a),[1,10,10])
        self.assertEqual(recurrence_residual(a),[0,0,0])
        self.assertEqual(matching_coefficients([[1,-1,2]]),[1,2])
    def test_cone_and_tamper(self):
        x={(1,):1}; y={(0,):1,(1,):-1}; t={(1,):1,(2,):-1}
        c=discover(t,1,[x,y],[])
        self.assertIsNotNone(c)
        self.assertTrue(replay(t,1,[x,y],[],c))
        self.assertFalse(replay(t,1,[x,y],[],[((),None,1)]))
    def test_square_with_constraint(self):
        x={(1,):1}; q={(0,):1,(1,):-1}
        p={(1,):1,(2,):-2,(3,):1}
        c=discover(p,1,[x],[q])
        self.assertIsNotNone(c)
        self.assertTrue(replay(p,1,[x],[q],c))
    def test_gram(self):
        b=[(1,0),(0,1)]
        p={(2,0):1,(0,2):1,(1,1):-2}
        self.assertTrue(replay_gram(p,b,[[1,-1],[-1,1]]))
        self.assertIsNone(gram_squares(b,[[0,1],[1,1]]))
        self.assertFalse(replay_gram(p,b,[[1,0],[0,1]]))
    def test_extremal(self):
        p={(2,0):-1,(0,2):-1}
        rows=[[1,1]]
        self.assertEqual(nullspace(rows,2),[[-1,1]])
        leads=discover_directions(p,rows,2)
        self.assertTrue(leads)
        d,c=leads[0]
        self.assertTrue(verify_direction(p,rows,2,d,[],c))
        self.assertFalse(verify_direction(p,rows,2,[1,1],[],c))
        self.assertEqual(endpoints([Q(1,3),Q(2,3)],d),(Q(-2,3),Q(1,3)))
    def test_theorem_composition(self):
        rules=[("goal",["a","b"],"r"),("a",["c"],"ra"),("b",["c"],"rb")]
        self.assertIn(["c"],plan("goal",rules,["r","ra","rb"])["routes"])
        self.assertIn([],plan("goal",rules,["r","ra","rb","c"])["routes"])
        self.assertNotIn([],plan("goal",rules,["c"])["routes"])
    def test_cycle(self):
        self.assertNotIn([],plan("a",[("a",["b"],"r"),("b",["a"],"r")],["r"])["routes"])
    def test_matched(self):
        r=dict(task="x",budget=4,calls=3,verdict="proved")
        self.assertEqual(evaluate({"a":[r],"b":[dict(r,verdict="partial")]})["a"]["solved"],1)
        with self.assertRaises(ValueError):
            evaluate({"a":[r],"b":[dict(r,budget=5)]})

    def test_graph_dispatch(self):
        import conditional_theorems as ct
        from general_inequality_lab import solve,replay,auto_discharge
        from discovery import new
        from proof_audit import audit
        # x(1-x)^2 >= 0 given x >= 0, on the real line.
        spec=dict(variables=["x"],domain="real",
                  assumptions=[dict(relation="nonnegative",terms=[[[1],1]])],
                  conclusion=[[[1],1],[[2],-2],[[3],1]])
        result=solve(spec)
        self.assertEqual(result["status"],"proved")
        self.assertEqual(replay(spec,result["certificate"]),"proved")
        g=auto_discharge(new(ct.statement(spec)))
        self.assertIn("goal",audit(g)["proved"])
        from theorem_network import graph_routes
        self.assertIn([],graph_routes(g)["routes"])
    def test_numerical_recovery_requires_exact(self):
        from sdp_discovery import recover,replay_result
        p={(2,0):1,(0,2):1,(1,1):-2}
        b=[(1,0),(0,1)]
        self.assertEqual(recover(p,b,[[1.00001,-0.99999],[-0.99999,1.00001]]),[[1,-1],[-1,1]])
        self.assertIsNone(recover(p,b,[[1,0],[0,1]]))
        self.assertTrue(replay_result(p,dict(status='proved',basis=[[1,0],[0,1]],matrix=[['1','-1'],['-1','1']])))

if __name__=="__main__":
    unittest.main()
