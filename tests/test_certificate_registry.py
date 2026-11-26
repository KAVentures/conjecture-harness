import copy,unittest
from importlib import import_module
from certificate_registry import TYPED,DIRECT,AUDIT_DIRECT,RESERVED
from discovery import new,apply,check
from discovery_portfolio import reconcile
from proof_audit import audit
import polynomial as p
import polynomial_lab
import knowledge_bank as k
import proof_bundle

class RegistryTests(unittest.TestCase):
    def test_registered_modules_and_namespaces(self):
        self.assertEqual(len(RESERVED),len(set(RESERVED)))
        self.assertEqual(DIRECT,k.DIRECT_PREFIXES)
        self.assertEqual(DIRECT,proof_bundle.DIRECT)
        self.assertIn('bundle-',AUDIT_DIRECT)
        self.assertNotIn('bundle-',DIRECT)
        for prefix,(parser,verifier,negative) in TYPED.items():
            self.assertTrue(callable(import_module(verifier).replay),prefix)
            if parser:self.assertTrue(callable(import_module(parser).parse_statement),prefix)
        g=new('target')
        for prefix in RESERVED:
            op=dict(op='observe',id=prefix+'fake',focus='goal',kind='proof_sketch',detail='untrusted')
            with self.assertRaises(ValueError):apply(g,[op])
            with self.assertRaises(ValueError):reconcile(g,g,[op],'test')
    def test_empty_premise_and_deep_graph(self):
        g=new('target')
        for i in range(998):
            j='a'+str(i);g['nodes'][j]=dict(statement='claim '+str(i),status='open')
        nodes=list(g['nodes'])
        for i,(a,b) in enumerate(zip(nodes,nodes[1:])):
            g['edges']['e'+str(i)]=dict(parent=a,premises=[b],argument='candidate',rule='candidate')
        self.assertIs(check(g),g)
        bad=copy.deepcopy(g);bad['edges']['e0']['premises']=[]
        with self.assertRaises(ValueError):check(bad)
        bad=copy.deepcopy(g);bad['edges']['cycle']=dict(parent=nodes[-1],premises=['goal'],argument='candidate',rule='candidate')
        with self.assertRaises(ValueError):check(bad)
    def test_mislabeled_direct_certificate(self):
        s=dict(variables=['x'],domain='real',relation='nonnegative',terms=[[[2],1]])
        g,_=polynomial_lab.discharge(new(p.statement(s)),'goal',s)
        oid=next(iter(g['observations']))
        g['observations'][oid]['kind']='counterexample'
        r=audit(g)
        self.assertEqual(r['status'],'unverified')
        self.assertIn(oid,r['invalid_observations'])
    def test_knowledge_export_limit(self):
        from unittest.mock import patch
        s=dict(variables=['x'],domain='real',relation='nonnegative',terms=[[[2],1]])
        g,_=polynomial_lab.discharge(new(p.statement(s)),'goal',s)
        with patch.object(k,'MAX_FACTS',0):
            with self.assertRaises(ValueError):k.export(g)


    def test_deep_route_planning(self):
        from proof_frontier import routes,choose_focus
        g=new('target')
        for i in range(999):
            g['nodes']['a'+str(i)]=dict(statement='claim '+str(i),status='open')
        nodes=list(g['nodes'])
        for i,(a,b) in enumerate(zip(nodes,nodes[1:])):
            g['edges']['e'+str(i)]=dict(parent=a,premises=[b],argument='candidate',rule='candidate')
        check(g)
        r=routes(g,set())
        self.assertEqual(r[0]['claims'],[nodes[-1]])
        self.assertEqual(len(r[0]['bridges']),999)
        self.assertEqual(r[0]['estimated_cost'],1000)
        self.assertEqual(choose_focus(g,r[0],nodes,'goal'),(nodes[-1],None))
