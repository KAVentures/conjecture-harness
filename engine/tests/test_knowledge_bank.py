import copy,unittest
import polynomial as p
import polynomial_lab
import knowledge_bank as k
import representation_transfer as rt
from discovery import new,apply,closure
from proof_audit import audit

def spec(terms,variables=None):return dict(variables=variables or ['x'],domain='real',relation='nonnegative',terms=terms)
class KnowledgeTests(unittest.TestCase):
    def source(self):
        s=spec([[[2],1]])
        g,_=polynomial_lab.discharge(new(p.statement(s)),'goal',s)
        return s,g
    def test_roundtrip(self):
        s,g=self.source();bank=k.export(g)
        self.assertEqual(len(bank['facts']),1)
        target,ids=k.import_facts(new(p.statement(s)),bank)
        self.assertEqual(ids,['goal'])
        self.assertEqual(audit(target)['status'],'proved')
        h,ids=k.import_facts(target,bank);self.assertEqual(h,target);self.assertFalse(ids)
    def test_cross_project_reuse(self):
        s,g=self.source();target=spec([[[2,0],1],[[1,1],2],[[0,2],1]],['u','v'])
        h,ids=k.import_facts(new(p.statement(target)),k.export(g))
        self.assertNotIn('goal',closure(h));self.assertEqual(len(ids),1)
        h=rt.auto_discharge(h)
        self.assertEqual(audit(h)['status'],'proved')
    def test_tampering(self):
        s,g=self.source();bank=k.export(g);bad=copy.deepcopy(bank)
        bad['facts'][0]['statement']=p.statement(spec([[[2],-1]]))
        with self.assertRaises(ValueError):k.import_facts(new('target'),bad)
    def test_manual_not_exported(self):
        g=apply(new('arbitrary assertion'),[dict(op='review_claim',id='goal',decision='established',evidence='manual')],trusted=True)
        self.assertEqual(k.export(g)['facts'],[])
    def test_merge_and_negative(self):
        s,g=self.source();b=k.export(g);self.assertEqual(len(k.merge([b,b])['facts']),1)
        s=spec([[[2],-1]])
        g,_=polynomial_lab.discharge(new(p.statement(s)),'goal',s)
        b=k.export(g)
        self.assertEqual(b['facts'][0]['outcome'],'refuted')
        h,ids=k.import_facts(new('unrelated'),b);self.assertFalse(ids)
        h,ids=k.import_facts(new(p.statement(s)),b);self.assertEqual(audit(h)['status'],'refuted')
