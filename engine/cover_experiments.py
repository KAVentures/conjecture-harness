"""Declarative, deterministic experiments: bounded finite hypothesis search.

No eval, subprocess, arbitrary code, network or worker-supplied imports.
The report is research evidence, not a proof of an arbitrary-order statement.
"""
import argparse, hashlib, itertools, json
from pathlib import Path
import combinatorial_cover as cc
from runtime import read_json

def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def validate(s):
    if not isinstance(s,dict) or set(s)!={"min_n","max_n","connected","min_degree","bound","graph_budget","state_budget"}:
        raise ValueError("experiment shape")
    if (not cc.integer(s["min_n"],1,6) or not cc.integer(s["max_n"],s["min_n"],6)
        or type(s["connected"]) is not bool or not cc.integer(s["min_degree"],0,5)
        or not cc.integer(s["graph_budget"],1,4096) or not cc.integer(s["state_budget"],1,cc.MAX_STATES)):
        raise ValueError("experiment limits")
    b=s["bound"]
    if not isinstance(b,list) or len(b)!=3 or not cc.integer(b[0],0,4) or not cc.integer(b[1],1,4) or not cc.integer(b[2],-4,4):
        raise ValueError("bound [numerator, denominator, offset]")
    return dict(s)

def eligible(n,es,s):
    adj=[set() for _ in range(n)]
    for u,v in es:adj[u].add(v);adj[v].add(u)
    if min(map(len,adj))<s["min_degree"]:return False
    if not s["connected"]:return True
    seen={0};todo=[0]
    while todo:
        for v in adj[todo.pop()]-seen:seen.add(v);todo.append(v)
    return len(seen)==n

def run(spec):
    s=validate(spec);counts=dict(proved=0,refuted=0,unknown=0,skipped=0)
    scanned=0;witnesses=[];examples=[];complete=True;trace=hashlib.sha256()
    a,b,c=s["bound"]
    for n in range(s["min_n"],s["max_n"]+1):
        possible=list(itertools.combinations(range(n),2))
        for mask in range(1<<len(possible)):
            if scanned>=s["graph_budget"]:complete=False;break
            scanned+=1
            es=[list(e) for i,e in enumerate(possible) if (mask>>i)&1]
            if not eligible(n,es,s):counts["skipped"]+=1;continue
            k=(a*n+b-1)//b+c
            if not 0<=k<=cc.MAX_ITEMS:counts["unknown"]+=1;continue
            instance=dict(kind="paths",n=n,edges=es,endpoints=None,max_pieces=k)
            r=cc.solve(instance,s["state_budget"])
            status=r["status"];counts[status]+=1
            trace.update((digest([instance,r])+"\n").encode())
            if status!="unknown" and cc.replay(instance,r["certificate"])!=status:raise ArithmeticError("experiment replay")
            if status=="refuted" and len(witnesses)<8:witnesses.append(dict(instance=instance,result=r))
            if status=="proved" and len(examples)<3:examples.append(dict(instance=instance,result=r))
        if not complete:break
    return dict(schema=1,spec=s,spec_sha256=digest(s),scanned=scanned,counts=counts,
                enumeration_complete=complete,all_eligible_decided=complete and counts["unknown"]==0,
                trace_sha256=trace.hexdigest(),counterexamples=witnesses,examples=examples,
                scope="finite labeled graphs only; no universal proof or novelty claim")

def replay(report):
    try:return isinstance(report,dict) and run(report["spec"])==report
    except (ValueError,TypeError,KeyError,ArithmeticError):return False

def budget_frontier(instance,lo=0,hi=None):
    """Evolve a failed finite hypothesis by testing neighboring piece budgets.
    Unknown leaves are never converted to an optimum.
    """
    s=cc.normalize(instance);hi=s["max_pieces"] if hi is None else hi
    if not cc.integer(lo,0,cc.MAX_ITEMS) or not cc.integer(hi,lo,cc.MAX_ITEMS):raise ValueError("budget range")
    results=[]
    for k in range(lo,hi+1):
        t=dict(s,max_pieces=k);r=cc.solve(t)
        results.append(dict(budget=k,result=r))
        if r["status"]=="proved":break
    optimum=results[-1]["budget"] if lo==0 and results[-1]["result"]["status"]=="proved" and all(x["result"]["status"]=="refuted" for x in results[:-1]) else None
    return dict(instance=s,results=results,minimum_certified=optimum,scope="fixed finite instance only")

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest="action",required=True)
    a=sub.add_parser("run");a.add_argument("spec");a.add_argument("output")
    a=sub.add_parser("replay");a.add_argument("report")
    a=sub.add_parser("frontier");a.add_argument("spec");a.add_argument("--hi",type=int)
    args=p.parse_args()
    if args.action=="run":
        r=run(read_json(args.spec))
        with Path(args.output).open("x",encoding="utf-8") as f:json.dump(r,f,indent=2)
        print(json.dumps({k:r[k] for k in ("scanned","counts","enumeration_complete")}))
    elif args.action=="replay":
        ok=replay(read_json(args.report));print(json.dumps(dict(replayed=ok)))
        if not ok:p.exit(1)
    else:print(json.dumps(budget_frontier(read_json(args.spec),hi=args.hi),indent=2))
if __name__=="__main__":main()
