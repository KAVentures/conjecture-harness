import json,sys,tempfile,unittest
from pathlib import Path
from discovery import new,apply,save,closure,record
from discovery_portfolio import assignments,reconcile,run
from runtime import read_json


def c(i,s):return dict(op='claim',id=i,statement=s)
def e(i,p,ps):return dict(op='derive',id=i,parent=p,premises=ps,argument='candidate argument')

class PortfolioTests(unittest.TestCase):
    def test_diversity(self):
        ps=assignments(new('Goal'),7);self.assertEqual(len(ps),7);self.assertEqual(len({p['mode'] for p in ps}),7);self.assertIn('blind',{p['mode'] for p in ps})
    def test_same_local_ids(self):
        g=new('Goal');a=reconcile(g,g,[c('a','First'),e('b','goal',['a'])],'0');h=apply(g,a);b=reconcile(h,g,[c('a','Second'),e('b','goal',['a'])],'1');h=apply(h,b);self.assertEqual(len(h['nodes']),3);self.assertEqual(len(h['edges']),2)
    def test_same_claim(self):
        g=new('Goal');a=reconcile(g,g,[c('a','Same'),e('b','goal',['a'])],'0');h=apply(g,a);self.assertEqual(reconcile(h,g,[c('z','Same'),e('b','goal',['z'])],'1'),[])
    def test_forward_local_refs(self):
        g=new('Goal');ops=reconcile(g,g,[e('b','goal',['a']),c('a','New')],'0');self.assertEqual(len(apply(g,ops)['edges']),1)
    def test_blind_and_snapshot(self):
        g=apply(new('Goal'),[c('a','Hidden')]);
        with self.assertRaises(ValueError):reconcile(g,g,[e('b','goal',['a'])],'0',True)
        with self.assertRaises(ValueError):reconcile(g,new('Goal'),[e('b','goal',['a'])],'0')
    def test_untrusted(self):
        g=new('Goal')
        for ops in ([dict(op='review_claim',id='goal',decision='established',evidence='fake')],[dict(op='observe',id='poly-fake',focus='goal',kind='experiment',detail='fake')],[c('a','A'),e('b','a',['a'])],[c('goal','replacement')]):
            with self.assertRaises(ValueError):reconcile(g,g,ops,'0')
        self.assertEqual(len(g['nodes']),1)
    def test_deterministic(self):
        g=new('Goal');ops=[c('a','New')];self.assertEqual(reconcile(g,g,ops,'0'),reconcile(g,g,ops,'0'))
    def test_parallel_and_budget(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json';save(p,new('Goal'))
            code='import sys,json,time; s=sys.stdin.read();time.sleep(0.1);print(json.dumps([{"op":"claim","id":"a","statement":"New"}]))'
            result=run(p,[[sys.executable,'-c',code]],4,10,2,3);self.assertEqual(result['launched'],4)
            g=read_json(p);self.assertEqual(len(g['history']),4);self.assertEqual(len(g['nodes']),2);self.assertNotIn('goal',closure(g));self.assertEqual(len(list(Path(str(p)+'.runs').glob('*/raw.json'))),4)
            result=run(p,[[sys.executable,'-c','print("[]")']],1,10,2,3);self.assertEqual(result['launched'],1);self.assertEqual(len(read_json(p)['history']),5)
    def test_solver_without_worker(self):
        from polynomial import statement
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json';save(p,new(statement(dict(variables=['x'],domain='real',relation='nonnegative',terms=[[[2],1]]))))
            r=run(p,[[sys.executable,'-c','raise SystemExit(99)']],2,10,2);self.assertEqual(r['launched'],0);self.assertTrue(r['next']['derived'])
    def test_rejected_batch(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json';save(p,new('Goal'));cmd=[sys.executable,'-c','print(\'[ {"op":"review_claim","id":"goal","decision":"established","evidence":"fake"} ]\')']
            run(p,[cmd],2,10,2);self.assertEqual(len(list(Path(str(p)+'.runs').glob('*/rejected.txt'))),2);self.assertNotIn('goal',closure(read_json(p)))
    def test_workers_overlap(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json';save(p,new('Goal'));barrier=Path(d)/'barrier';barrier.mkdir()
            code='import pathlib,os,time,sys; p=pathlib.Path(sys.argv[1]);(p/str(os.getpid())).touch(); deadline=time.monotonic()+2\nwhile len(list(p.iterdir()))<2 and time.monotonic()<deadline: time.sleep(.02)\nif len(list(p.iterdir()))<2: raise SystemExit(9)\nprint("[]")'
            run(p,[[sys.executable,'-c',code,str(barrier)]],2,10,4,2)
            raws=[json.loads(x.read_text()) for x in Path(str(p)+'.runs').glob('*/raw.json')];self.assertEqual(len(raws),2);self.assertTrue(all(r['returncode']==0 for r in raws))
    def test_worker_failure_does_not_discard_peer(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json';save(p,new('Goal'))
            good=[sys.executable,'-c','print(\'[{"op":"claim","id":"a","statement":"New"}]\')'];bad=[sys.executable,'-c','raise SystemExit(3)']
            run(p,[bad,good],2,10,2,2);self.assertEqual(len(read_json(p)['nodes']),2);self.assertEqual(len(list(Path(str(p)+'.runs').glob('*/rejected.txt'))),1)
    def test_planner_blind_metadata_is_minimal(self):
        g=apply(new('Goal'),[c('a','Hidden'),e('b','goal',['a'])])
        for _ in range(3):g=record(g,'backward','goal',[])
        p=assignments(g,2)[0];self.assertEqual(p,dict(mode='blind',focus='goal',bridge=None,routes=[]))
