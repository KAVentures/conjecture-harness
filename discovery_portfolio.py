"""Bounded parallel proposal portfolio; deterministic, untrusted reconciliation."""
import argparse, concurrent.futures, copy, json, math, tempfile, time
from pathlib import Path
from discovery import ID, MODES, apply, check, fingerprint, frontier, key, plan, prompt, record, save
from discovery_run import auto_discharge
from equivalence import claim_key
from strategy import ranking
from harness import coordinator_lock
from runtime import invoke, read_json, strict_json

LENSES = ('algebraic invariants', 'combinatorial structure', 'duality and optimization',
          'probabilistic or analytic methods', 'extremal examples', 'different mathematical representation')


def assignments(g, count, profile=None, metareasoning=False):
    from metareasoning import select
    p = select(g,profile) if metareasoning else plan(g,profile)
    if 'stop' in p: return []
    out = [dict(mode='blind', focus='goal', bridge=None, routes=[]) if p['mode']=='blind' else p]
    # Reserve a target-only branch whenever multiple calls fit the budget.
    if count > 1 and p['mode'] != 'blind':
        out.append(dict(mode='blind', focus='goal', bridge=None, routes=[]))
    from strategy_profile import prior
    for mode in ranking(g['history'],MODES,prior(profile,g) if profile is not None else None):
        if len(out) >= count: break
        if mode in [a['mode'] for a in out]: continue
        q=dict(mode=mode, focus='goal' if mode=='reformulate' else p['focus'], bridge=None, routes=p['routes'])
        if metareasoning and mode!='blind' and 'diagnosis' in p:q['diagnosis']=p['diagnosis']
        out.append(q)
    return out[:count]


def reconcile(current, snapshot, ops, slot, blind=False):
    """Map local IDs and exact duplicate claims; never trust worker decisions.

    Each worker can reference only its snapshot (goal only when blind) or its
    own declared claims. All updates are atomic; raw responses remain on disk.
    """
    if not isinstance(ops, list) or len(ops)>64: raise ValueError('expected at most 64 operations')
    allowed={'goal'} if blind else set(snapshot['nodes'])
    local={}; pending=[]; seen=set(); existing={}
    for i,n in current['nodes'].items():existing.setdefault(claim_key(n['statement']),i)
    prefix='w-'+fingerprint(slot)[:16]+'-'
    def valid_id(i):return isinstance(i,str) and ID.fullmatch(i)
    def mapped(i):
        if i in local:return local[i]
        if i in allowed:return i
        raise ValueError('reference outside worker snapshot: '+str(i))
    def fresh(i):return prefix+fingerprint(i)[:24]
    for o in ops:
        if not isinstance(o,dict) or o.get('op') not in ('claim','derive','observe'):raise ValueError('untrusted operation')
        i=o.get('id');k=o['op']
        if isinstance(i,str) and i.startswith(('symbolic-','synthesis-','representation-','dynamics-','indexed-','simplex-','extremal-','conditional-','application-','knowledge-','bundle-','sturm-','sign-cell-','projective-','equational-','structure-')):raise ValueError('reserved core discovery ID')
        if not valid_id(i) or (k,i) in seen or i.startswith(('aff-','lab-','poly-','bridge-','equiv-','shift-','repair-','sum-','invent-','recursive-','capacity-','finite-power-','graph-reduction-','theorem-')):raise ValueError('invalid or duplicate local ID')
        seen.add((k,i))
        if k=='claim':
            if set(o)!={'op','id','statement'} or i in allowed or not isinstance(o['statement'],str) or not o['statement'].strip() or len(o['statement'].strip())>20000:raise ValueError('invalid local claim')
            s=claim_key(o['statement']);j=existing.get(s)
            if j is None:
                j=fresh(i);existing[s]=j;pending.append(dict(o,id=j))
            local[i]=j
    # Keep the source argument in raw logs even when its exact dependency set duplicates another edge.
    edges={(e['parent'],frozenset(e['premises'])) for e in current['edges'].values() if e['rule']!='rejected'}
    for o in ops:
        k=o['op'];i=o['id']
        if k=='claim':continue
        if k=='derive':
            if set(o)!={'op','id','parent','premises','argument'} or not isinstance(o['premises'],list) or not 1<=len(o['premises'])<=32 or not all(valid_id(x) for x in o['premises']) or not valid_id(o['parent']) or not isinstance(o['argument'],str) or not o['argument'].strip() or len(o['argument'].strip())>20000:raise ValueError('invalid derivation')
            p=mapped(o['parent']);ps=[mapped(x) for x in o['premises']]
            if p in ps or len(set(ps))!=len(ps):raise ValueError('circular or duplicate premise')
            sig=(p,frozenset(ps))
            if sig not in edges:pending.append(dict(o,id=fresh(i),parent=p,premises=ps));edges.add(sig)
        else:
            if set(o)!={'op','id','focus','kind','detail'} or not valid_id(o['focus']):raise ValueError('invalid observation')
            pending.append(dict(o,id=fresh(i),focus=mapped(o['focus'])))
    if pending: apply(current,pending) # validate entire batch before recording
    return pending


def run(path,commands,attempts,seconds,timeout,workers=3,profile=None,metareasoning=False):
    from metareasoning import select,research_prompt,annotate
    prompter=research_prompt if metareasoning else prompt
    path=Path(path).resolve()
    if not isinstance(commands,list) or not commands or not all(isinstance(c,list) and c and all(isinstance(x,str) and x for x in c) for c in commands):raise ValueError('expected trusted command arrays')
    if type(attempts) is not int or not 1<=attempts<=1000 or type(workers) is not int or not 1<=workers<=7 or not all(math.isfinite(x) and x>0 for x in (seconds,timeout)):raise ValueError('invalid limits')
    log=path.with_name(path.name+'.runs');log.mkdir(exist_ok=True)
    with coordinator_lock(log):
        g=check(read_json(path,limit=32*1024*1024));deadline=time.monotonic()+seconds;launched=0
        while launched<attempts and time.monotonic()<deadline:
            h=auto_discharge(g)
            if h!=g:save(path,h);g=h
            if time.monotonic()>=deadline:break
            ps=assignments(g,min(workers,attempts-launched),profile,metareasoning)
            if not ps:break
            snapshot=copy.deepcopy(g);jobs=[]
            for i,p in enumerate(ps):
                folder=Path(tempfile.mkdtemp(prefix='portfolio-',dir=log));slot=str(len(snapshot['history']))+'-'+str(i)
                lens=LENSES[(len(snapshot['history'])+i)%len(LENSES)]
                data=prompter(snapshot,p)+'\nExplore this lens if mathematically appropriate: '+lens
                (folder/'prompt.txt').write_text(data,encoding='utf-8')
                (folder/'assignment.json').write_text(json.dumps(dict(plan=p,lens=lens,slot=slot)),encoding='utf-8')
                jobs.append((p,folder,data,commands[(launched+i)%len(commands)],slot))
            def worker(job):
                _,folder,data,cmd,_=job
                left=deadline-time.monotonic()
                raw=invoke(cmd,data,min(timeout,left),folder) if left>0 else dict(returncode=124,stdout='',stderr='budget exhausted',termination='timeout')
                (folder/'raw.json').write_text(json.dumps(raw),encoding='utf-8');return raw
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(jobs)) as pool:
                fs=[pool.submit(worker,j) for j in jobs]
                launched+=len(jobs)
                # Reconcile by assignment order, not completion order.
                for (p,folder,_,_,slot),f in zip(jobs,fs):
                    raw=f.result()
                    try:
                        if raw['returncode']:raise ValueError('worker failed')
                        ops=reconcile(g,snapshot,strict_json(raw['stdout']),slot,p['mode']=='blind')
                        h=record(g,p['mode'],p['focus'],ops)
                        (folder/'merged.json').write_text(json.dumps(ops),encoding='utf-8')
                    except (ValueError,TypeError,KeyError,RecursionError) as e:
                        (folder/'rejected.txt').write_text(str(e),encoding='utf-8');h=record(g,p['mode'],p['focus'],[])
                    h['history'][-1]['elapsed_seconds']=raw.get('elapsed',0)
                    if metareasoning:annotate(h,p)
                    save(path,h);g=h
        if time.monotonic()<deadline:
            h=auto_discharge(g)
            if h!=g:save(path,h);g=h
    return dict(launched=launched,next=select(g,profile) if metareasoning else plan(g,profile))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('state',type=Path);p.add_argument('--config',type=Path,required=True);p.add_argument('--attempts',type=int,default=12);p.add_argument('--seconds',type=float,default=600);p.add_argument('--timeout',type=float,default=120);p.add_argument('--workers',type=int,default=3);p.add_argument('--strategy-profile',type=Path);p.add_argument('--metareasoning',action='store_true');a=p.parse_args()
    from strategy_profile import load
    cfg=read_json(a.config);cmds=cfg['workers'] if 'workers' in cfg else [cfg['worker']]
    print(json.dumps(run(a.state,cmds,a.attempts,a.seconds,a.timeout,a.workers,load(a.strategy_profile),a.metareasoning),indent=2))
if __name__=='__main__':main()
