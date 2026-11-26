"""Audit-aware bounded Pareto compression of AND/OR proof obligations.

This is research planning, not a proof rule. Direct proofs remain alternative
routes; exact audited claims and bridges alone eliminate obligations.
"""
from collections import deque,Counter

def compress(g,report,width=12):
    if type(width) is not int or not 1<=width<=32:raise ValueError('beam width')
    if report['conflicts']:return []
    known=set(report['proved']);bad=set(report['refuted']);checked=set(report['checked_edges'])
    visits=Counter(h['focus'] for h in g['history'] if not h['trusted_review'])
    incoming={i:[] for i in g['nodes']}
    for i,e in sorted(g['edges'].items()):
        if e['rule']!='rejected' and not set(e['premises'])&bad and not any(g['nodes'][p]['status']=='refuted' for p in e['premises']):
            incoming[e['parent']].append((i,e))
    deps={i:set() if i in known or i in bad else {p for _,e in incoming[i] for p in e['premises']} for i in incoming}
    parents={i:[] for i in deps}
    for i,ps in deps.items():
        for p in ps:parents[p].append(i)
    pending={i:len(ps) for i,ps in deps.items()};todo=deque(i for i,v in pending.items() if not v);best={}
    def cost(a,b):return sum(4+min(20,visits[i]) for i in a)+sum(4+min(20,visits[g['edges'][i]['parent']]) for i in b)
    def prune(options):
        out=[]
        for a,b in sorted(set(options),key=lambda r:(cost(*r),len(r[1]),sorted(r[0]),sorted(r[1]))):
            if any(x<=a and y<=b for x,y in out):continue
            out.append((a,b))
            if len(out)==width:break
        return out
    def branch(i,e):
        out=[(frozenset(),frozenset() if i in checked else frozenset([i]))]
        for p in e['premises']:
            out=prune([(a|x,b|y) for a,b in out for x,y in best[p]])
            if not out:break
        return out
    empty=(frozenset(),frozenset())
    while todo:
        i=todo.popleft()
        if i in known:best[i]=[empty]
        elif i in bad or g['nodes'][i]['status']=='refuted':best[i]=[]
        else:
            options=[(frozenset([i]),frozenset())]
            for j,e in incoming[i]:options=prune(options+branch(j,e))
            best[i]=options
        for parent in parents[i]:
            pending[parent]-=1
            if not pending[parent]:todo.append(parent)
    if len(best)!=len(deps):raise ValueError('cyclic proof graph')
    out=[]
    for a,b in best['goal']:
        out.append(dict(claims=sorted(a),bridges=sorted(b),estimated_cost=cost(a,b)/4))
    return out

def shared(routes):
    """Report recurring bottlenecks across nondominated candidate routes."""
    counts=Counter(i for r in routes for i in r['claims'])
    return [dict(claim=i,routes=k) for i,k in sorted(counts.items(),key=lambda x:(-x[1],x[0])) if k>1]
