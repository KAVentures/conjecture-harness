"""Portable, replayable mathematical knowledge across research projects.

Only directly replayable certificates are exported/imported as facts.
Literature leads and composite/manual proofs are not silently promoted.
"""
import argparse,json,re
from pathlib import Path
from discovery import check,record,fingerprint,frontier,closure,save
from runtime import read_json
from proof_audit import audit,direct

DIRECT_PREFIXES=('aff-','poly-','shift-','capacity-','graph-reduction-','finite-power-','lab-','invent-','recursive-','symbolic-','dynamics-','indexed-','simplex-','conditional-','sturm-')

def prefix(oid):
    return next((p for p in DIRECT_PREFIXES if oid.startswith(p)),None)

def verify_fact(f):
    if not isinstance(f,dict) or set(f)!={'statement','outcome','prefix','kind','detail','origin'}:return False
    if not isinstance(f['statement'],str) or not 0<len(f['statement'])<=20000 or f['outcome'] not in ('proved','refuted') or f['prefix'] not in DIRECT_PREFIXES or f['kind'] not in ('proof_sketch','counterexample') or not isinstance(f['detail'],str) or not 0<len(f['detail'])<=20000:return False
    if f['kind']!=('proof_sketch' if f['outcome']=='proved' else 'counterexample'):return False
    o=f['origin']
    if not isinstance(o,dict) or set(o)!={'target_sha256','claim','observation'} or not isinstance(o['target_sha256'],str) or not re.fullmatch(r'[0-9a-f]{64}',o['target_sha256']) or any(not isinstance(o[k],str) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}',o[k]) for k in ('claim','observation')):return False
    if not o['observation'].startswith(f['prefix']):return False
    try:return direct(f['statement'],f['prefix']+'replay',dict(kind=f['kind'],detail=f['detail']))==f['outcome']
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,RecursionError):return False

def export(g):
    check(g);report=audit(g)
    if report['conflicts']:raise ValueError('conflicting evidence; resolve before export')
    facts=[];seen=set()
    for oid,o in sorted(g['observations'].items()):
        pre=prefix(oid)
        if pre is None or o['kind'] not in ('proof_sketch','counterexample'):continue
        i=o['focus'];text=g['nodes'][i]['statement']
        outcome='proved' if o['kind']=='proof_sketch' else 'refuted'
        f=dict(statement=text,outcome=outcome,prefix=pre,kind=o['kind'],detail=o['detail'],origin=dict(target_sha256=g['target_sha256'],claim=i,observation=oid))
        key=(text,outcome)
        if key in seen or not verify_fact(f):continue
        seen.add(key);facts.append(f)
    return dict(schema=1,facts=facts,scope='direct exact certificates only; origin metadata is not authenticated')

def validate(bank):
    if not isinstance(bank,dict) or bank.get('schema')!=1 or not isinstance(bank.get('facts'),list) or len(bank['facts'])>256:raise ValueError('knowledge bank shape')
    seen={}
    for f in bank['facts']:
        if not verify_fact(f):raise ValueError('invalid knowledge certificate')
        t=f['statement'];o=f['outcome']
        if t in seen and seen[t]!=o:raise ValueError('contradictory knowledge')
        seen[t]=o
    return bank

def merge(banks):
    facts={}
    for b in banks:
        validate(b)
        for f in b['facts']:
            t=f['statement']
            if t in facts and facts[t]['outcome']!=f['outcome']:raise ValueError('contradictory knowledge')
            facts.setdefault(t,f)
    out=dict(schema=1,facts=[facts[k] for k in sorted(facts)],scope='direct exact certificates only; origin metadata is not authenticated')
    return validate(out)

def candidate_score(text,f):
    """Retrieval is only prioritization; exact checks decide every import."""
    if text==f['statement']:return 1000
    a=set(re.findall(r'[A-Za-z][A-Za-z0-9_-]*',text.lower()))
    b=set(re.findall(r'[A-Za-z][A-Za-z0-9_-]*',f['statement'].lower()))
    return len(a&b)/max(1,len(a|b))

def import_facts(g,bank,limit=8):
    check(g);validate(bank)
    if type(limit) is not int or not 1<=limit<=32:raise ValueError('import limit')
    candidates=sorted(bank['facts'],key=lambda f:(-max((candidate_score(g['nodes'][i]['statement'],f) for i in frontier(g)),default=0),f['statement']))
    count=0;used=[]
    for f in candidates:
        if count>=limit:break
        text=f['statement'];decision='established' if f['outcome']=='proved' else 'refuted'
        i=next((k for k,v in sorted(g['nodes'].items()) if v['statement']==text),None)
        # Reuse refutations only for identical existing claims; unrelated
        # negative facts must not pollute the active proof graph.
        if i is None and decision=='refuted':continue
        if i is not None:
            current=g['nodes'][i]['status']
            if current!='open' and current!=decision:raise ValueError('knowledge conflicts with recorded review')
            if decision=='refuted' and i in closure(g):raise ValueError('knowledge contradicts recorded derivation')
        else:
            # Import proved typed facts as a reusable lemma pool; existing
            # application/representation/synthesis passes decide relevance.
            i='knowledge-node-'+fingerprint(text)[:24]
        oid=f['prefix']+fingerprint(i+'\n'+f['detail'])[:32]
        provenance='knowledge-'+fingerprint(i+'\n'+json.dumps(f['origin'],sort_keys=True))[:32]
        if oid in g['observations']:continue
        ops=[]
        if i not in g['nodes']:ops.append(dict(op='claim',id=i,statement=text))
        ops.append(dict(op='observe',id=oid,focus=i,kind=f['kind'],detail=f['detail']))
        if provenance not in g['observations']:ops.append(dict(op='observe',id=provenance,focus=i,kind='transfer',detail=json.dumps(dict(replayed_observation=oid,origin=f['origin']),sort_keys=True)))
        if i not in g['nodes'] or g['nodes'][i]['status']=='open':
            ops.append(dict(op='review_claim',id=i,decision=decision,evidence='Replayed imported exact certificate '+oid))
        g=record(g,'forward','goal',ops,trusted=True);count+=1;used.append(i)
    return g,used

def main():
    from harness import coordinator_lock
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    a=sub.add_parser('export');a.add_argument('state');a.add_argument('output')
    a=sub.add_parser('merge');a.add_argument('output');a.add_argument('banks',nargs='+')
    a=sub.add_parser('import');a.add_argument('state');a.add_argument('bank');a.add_argument('--limit',type=int,default=8)
    a=p.parse_args()
    if a.action=='export':
        bank=export(read_json(a.state,limit=32*1024*1024));Path(a.output).write_text(json.dumps(bank,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(dict(facts=len(bank['facts']))))
    elif a.action=='merge':
        bank=merge([read_json(x,limit=16*1024*1024) for x in a.banks]);Path(a.output).write_text(json.dumps(bank,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(dict(facts=len(bank['facts']))))
    else:
        path=Path(a.state).resolve();log=path.with_name(path.name+'.runs');log.mkdir(exist_ok=True)
        with coordinator_lock(log):
            g=check(read_json(path,limit=32*1024*1024));h,used=import_facts(g,read_json(a.bank,limit=16*1024*1024),a.limit)
            if h!=g:save(path,h)
        print(json.dumps(dict(imported=used)))
if __name__=='__main__':main()
