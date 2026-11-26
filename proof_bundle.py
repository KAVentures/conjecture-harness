"""Portable multi-step proof DAGs, with independent replay and no nested bundles."""
import argparse,json,re
from pathlib import Path
from discovery import check,record,fingerprint,closure,save,ID
from runtime import read_json
from equivalence import equivalent

MAX_STEPS=32
MAX_BYTES=18000
DIRECT=('aff-','poly-','shift-','capacity-','graph-reduction-','finite-power-','lab-','invent-','recursive-','symbolic-','dynamics-','indexed-','simplex-','conditional-','sturm-','sign-cell-','projective-','equational-','structure-','graph-linear-','ideal-consequence-')

def size(obj):return len(json.dumps(obj,sort_keys=True,ensure_ascii=True))
def valid_id(x):return isinstance(x,str) and ID.fullmatch(x) is not None
def valid_text(x):return isinstance(x,str) and 0<len(x.strip())<=20000

def replay(bundle,expected=None):
    """Check all steps topologically; use the existing independent checkers."""
    from proof_audit import direct,bridge
    try:
        if not isinstance(bundle,dict) or set(bundle)!={'schema','root','steps'} or type(bundle['schema']) is not int or bundle['schema']!=1 or size(bundle)>MAX_BYTES:return False
        steps=bundle['steps'];root=bundle['root']
        if not isinstance(steps,list) or not 1<=len(steps)<=MAX_STEPS or not valid_id(root):return False
        nodes={};proved=set();used={}
        for step in steps:
            if not isinstance(step,dict) or set(step)!={'id','statement','proof'}:return False
            i=step['id'];text=step['statement'];proof=step['proof']
            if not valid_id(i) or i in nodes or not valid_text(text) or not isinstance(proof,dict):return False
            nodes[i]=dict(statement=text);kind=proof.get('kind')
            if kind=='direct':
                if set(proof)!={'kind','oid','observation'}:return False
                oid=proof['oid'];o=proof['observation']
                if not valid_id(oid) or not oid.startswith(DIRECT) or not isinstance(o,dict) or set(o)!={'focus','kind','detail'} or o['focus']!=i or o['kind']!='proof_sketch' or not valid_text(o['detail']):return False
                if direct(text,oid,o)!='proved':return False
                used[i]=[]
            elif kind=='equivalent':
                if set(proof)!={'kind','premise'} or proof['premise'] not in proved:return False
                j=proof['premise']
                if not equivalent(text,nodes[j]['statement']):return False
                used[i]=[j]
            elif kind=='bridge':
                if set(proof)!={'kind','edge_id','premises','observations'}:return False
                eid=proof['edge_id'];ps=proof['premises'];obs=proof['observations']
                if not valid_id(eid) or not isinstance(ps,list) or not 1<=len(ps)<=32 or any(j not in proved for j in ps) or len(set(ps))!=len(ps):return False
                if not isinstance(obs,list) or len(obs)>4:return False
                pairs=[]
                for pair in obs:
                    if not isinstance(pair,list) or len(pair)!=2:return False
                    oid,o=pair
                    if not valid_id(oid) or not isinstance(o,dict) or set(o)!={'focus','kind','detail'} or o['focus']!=i or o['kind'] not in ('proof_sketch','transfer') or not valid_text(o['detail']):return False
                    pairs.append((oid,o))
                if not bridge(dict(nodes=nodes),eid,dict(parent=i,premises=ps),pairs):return False
                used[i]=ps
            else:return False
            proved.add(i)
        if root not in proved or steps[-1]['id']!=root:return False
        reachable=set();todo=[root]
        while todo:
            i=todo.pop()
            if i not in reachable:reachable.add(i);todo.extend(used[i])
        return reachable==proved and (expected is None or nodes[root]['statement']==expected)
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,RecursionError):return False

def export(g,root='goal'):
    """Extract only the proof actually replayed by the audit; no review labels."""
    from proof_audit import audit
    check(g);r=audit(g)
    if r['conflicts'] or root not in r['proved']:raise ValueError('root has no conflict-free verified proof')
    steps=[];done=set();active=set()
    def visit(i):
        if i in done:return
        if i in active or len(done)+len(active)>=MAX_STEPS:raise ValueError('proof depth or size limit')
        active.add(i);w=r['proved'][i]
        if w in g['observations'] and g['observations'][w]['focus']==i and w.startswith(DIRECT):
            proof=dict(kind='direct',oid=w,observation=g['observations'][w])
        elif w.startswith('equivalent:'):
            j=w.split(':',1)[1];visit(j);proof=dict(kind='equivalent',premise=j)
        elif w in r['checked_edges']:
            e=g['edges'][w];ps=e['premises']
            if e['parent']!=i:raise ValueError('edge mismatch')
            for j in ps:visit(j)
            locator=r['checked_edges'][w];obs=[]
            if locator in g['observations']:obs=[[locator,g['observations'][locator]]]
            proof=dict(kind='bridge',edge_id=w,premises=ps,observations=obs)
        else:raise ValueError('unsupported proof locator (nested bundles must be flattened externally)')
        steps.append(dict(id=i,statement=g['nodes'][i]['statement'],proof=proof));active.remove(i);done.add(i)
    visit(root);bundle=dict(schema=1,root=root,steps=steps)
    if not replay(bundle,g['nodes'][root]['statement']):raise ValueError('export exceeds limits or replay failed')
    return bundle

def import_bundle(g,bundle):
    check(g)
    if not replay(bundle):raise ValueError('invalid proof bundle')
    text=bundle['steps'][-1]['statement']
    i=next((k for k,n in sorted(g['nodes'].items()) if n['statement']==text),None)
    if i is not None and g['nodes'][i]['status']=='refuted':raise ValueError('bundle contradicts recorded claim')
    i=i or 'bundle-node-'+fingerprint(text)[:24]
    detail=json.dumps(dict(status='proved',certificate=bundle),sort_keys=True)
    if len(detail)>20000:raise ValueError('encoded bundle exceeds observation limit')
    oid='bundle-'+fingerprint(i+'\n'+detail)[:32]
    if oid in g['observations']:return g,i
    ops=[]
    if i not in g['nodes']:ops.append(dict(op='claim',id=i,statement=text))
    ops.append(dict(op='observe',id=oid,focus=i,kind='proof_sketch',detail=detail))
    if i not in g['nodes'] or g['nodes'][i]['status']=='open':ops.append(dict(op='review_claim',id=i,decision='established',evidence='Replayed portable proof '+oid))
    return record(g,'forward','goal',ops,trusted=True),i

def main():
    from harness import coordinator_lock
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    a=sub.add_parser('export');a.add_argument('state');a.add_argument('output');a.add_argument('--root',default='goal')
    a=sub.add_parser('verify');a.add_argument('bundle')
    a=sub.add_parser('import');a.add_argument('state');a.add_argument('bundle')
    a=p.parse_args()
    if a.action=='verify':
        ok=replay(read_json(a.bundle));print(json.dumps(dict(verified=ok)))
        if not ok:p.exit(1)
    elif a.action=='export':
        b=export(read_json(a.state,limit=32*1024*1024),a.root)
        with Path(a.output).open('x',encoding='utf-8') as f:json.dump(b,f,indent=2);f.write('\n')
        print(json.dumps(dict(steps=len(b['steps']))))
    else:
        path=Path(a.state).resolve();log=path.with_name(path.name+'.runs');log.mkdir(exist_ok=True)
        with coordinator_lock(log):
            g=check(read_json(path,limit=32*1024*1024));h,i=import_bundle(g,read_json(a.bundle))
            if h!=g:save(path,h)
        print(json.dumps(dict(imported=i)))
if __name__=='__main__':main()
