import copy,unittest,random
import equational as e
import equational_lab as lab
from discovery import new,closure,apply
from proof_audit import audit

ASSOC=[['m',['m','x','y'],'z'],['m','x',['m','y','z']]]
COMM=[['m','x','y'],['m','y','x']]
def spec(axioms,conclusion,ops=None):
    return dict(variables=['x','y','z'],operations=ops or {'m':2},axioms=axioms,conclusion=conclusion)

class EquationalTests(unittest.TestCase):
    def test_derivation(self):
        s=spec([ASSOC,COMM],[['m',['m','x','y'],'z'],['m','z',['m','y','x']]])
        r=e.solve(s);self.assertEqual(r['status'],'proved')
        self.assertEqual(e.replay(s,r['certificate']),'proved')
        bad=copy.deepcopy(r['certificate']);bad['steps'][0]['path']=[99]
        self.assertIsNone(e.replay(s,bad))
        self.assertIsNone(e.replay(dict(s,axioms=[]),r['certificate']))
        g=lab.auto_discharge(new(e.statement(s)))
        self.assertIn('goal',closure(g));self.assertEqual(audit(g)['status'],'proved')
    def test_countermodel(self):
        s=spec([ASSOC],COMM);r=e.solve(s)
        self.assertEqual(r['status'],'refuted')
        self.assertEqual(e.replay(s,r['certificate']),'refuted')
        self.assertIsNone(e.replay(spec([ASSOC,COMM],COMM),r['certificate']))
        bad=copy.deepcopy(r['certificate']);bad['assignment']['x']=3
        self.assertIsNone(e.replay(s,bad))
        self.assertEqual(audit(lab.auto_discharge(new(e.statement(s))))['status'],'refuted')
    def test_constants_and_erasing_variables(self):
        s=spec([[['m','x','y'],'x']],[['m','x',['e']],'x'],{'m':2,'e':0})
        r=e.solve(s);self.assertEqual(r['status'],'proved')
        self.assertEqual(e.replay(s,r['certificate']),'proved')
    def test_empty_chain_and_budget(self):
        s=spec([],['x','x']);self.assertEqual(e.solve(s)['certificate'],dict(kind='rewrite-chain',steps=[]))
        r=e.solve(spec([ASSOC],COMM),rewrite_budget=1,model_budget=1)
        self.assertEqual(r['status'],'unknown')
    def test_random_commutative_semigroup_identities(self):
        rng=random.Random(341)
        for _ in range(40):
            xs=[rng.choice(['x','y','z']) for _ in range(3)]
            ys=xs[:];rng.shuffle(ys)
            s=spec([ASSOC,COMM],[['m',['m',xs[0],xs[1]],xs[2]],['m',ys[0],['m',ys[1],ys[2]]]])
            r=e.solve(s,rewrite_budget=64,model_budget=16)
            self.assertEqual(r['status'],'proved')
            self.assertEqual(e.replay(s,r['certificate']),'proved')
    def test_reserved_and_validation(self):
        with self.assertRaises(ValueError):e.normalize(spec([],['x',['m','x']]))
        with self.assertRaises(ValueError):apply(new('x'),[dict(op='observe',id='equational-fake',focus='goal',kind='proof_sketch',detail='fake')])
