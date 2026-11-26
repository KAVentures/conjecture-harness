import unittest
from copy import deepcopy
import polynomial as p
from lemma_invention import invent
from recursive_invention import search,replay,auto_recursive
from discovery import new,apply,closure
from discovery_run import auto_discharge


def target(a=4,b=2,c=1,d=4,e=2,f=1):
    s=dict(variables=['x','y','z','w'],domain='real',relation='nonnegative',terms=[])
    for i,j,A,B,C in [(0,1,a,b,c),(2,3,d,e,f)]:
        for u,v,k in [(4,0,A),(0,4,A),(2,2,B*B-2*A),(1,2,2*B*C),(0,2,C*C)]:
            ex=[0]*4;ex[i]=u;ex[j]=v;s['terms'].append([ex,k])
    return s

class RecursiveTests(unittest.TestCase):
    def test_multilevel(self):
        s=target();self.assertEqual(p.solve(s)['status'],'unknown');self.assertEqual(invent(s)['status'],'unknown');r=search(s);self.assertEqual(r['status'],'proved');self.assertTrue(replay(s,r['tree']));self.assertIn('parts',r['tree']['children'][1])
    def test_shallow_budget(self):
        self.assertEqual(search(target(),max_depth=1)['status'],'unknown');self.assertEqual(search(target(),budget=1)['tested'],1)
    def test_tamper_leaf(self):
        s=target();t=search(s)['tree'];t['children'][1]['children'][0]['certificate']['squares'][0][0]='-1';self.assertFalse(replay(s,t))
    def test_tamper_internal(self):
        s=target();t=search(s)['tree'];t['children'][1]['parts'][1]['terms'][0][1]='99';self.assertFalse(replay(s,t))
    def test_domain(self):
        s=target();t=search(s)['tree'];t['parts'][0]['domain']='nonnegative';self.assertFalse(replay(s,t))
    def test_point_not_proof(self):
        s=target();self.assertFalse(replay(s,{'certificate':{'kind':'point','point':['0']*4}}))
    def test_invalid_tree(self):
        for t in (None,[],{'parts':[], 'children':[]},{'certificate':[]},{'parts':[None,None],'children':[None,None]}):self.assertFalse(replay(target(),t))
    def test_false(self):
        s=target();s['terms'].append([[0]*4,-1]);self.assertEqual(search(s)['status'],'unknown');self.assertEqual(auto_discharge(new(p.statement(s)))['nodes']['goal']['status'],'refuted')
    def test_state_graph(self):
        s=target();g=new(p.statement(s));h=auto_discharge(g);self.assertIn('goal',closure(h));self.assertEqual(len(h['nodes']),5);self.assertEqual(len(h['edges']),2);self.assertEqual(h['nodes']['goal']['statement'],g['nodes']['goal']['statement']);self.assertEqual(auto_discharge(h),h)
        self.assertTrue(all(e['rule']=='accepted' for e in h['edges'].values()));self.assertEqual(sum(n['status']=='established' for n in h['nodes'].values()),3)
    def test_no_untriggered_search(self):
        g=new(p.statement(target()));self.assertEqual(auto_recursive(g),g)
    def test_limits(self):
        for kw in ({'budget':0},{'max_depth':5},{'width':True},{'width':65}):self.assertRaises(ValueError,search,target(),**kw)
    def test_reserved(self):
        self.assertRaises(ValueError,apply,new('target'),[dict(op='observe',id='recursive-fake',focus='goal',kind='experiment',detail='fake')])
