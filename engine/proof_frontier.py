"""Heuristic proof-route ranking. Cost is not a proof length or success probability."""
from collections import deque


def routes(g, known):
    """Build one greedy completion estimate per live root alternative.

    Shared obligations count once. Candidate implication checks are distinct
    from premise proofs. This is not globally optimal AND/OR search.
    """
    visits={}
    for event in g['history']:
        focus=event['focus'];visits[focus]=visits.get(focus,0)+1
    incoming={i:[] for i in g['nodes']}
    for i,e in sorted(g['edges'].items()):
        if e['rule']!='rejected' and not any(g['nodes'][p]['status']=='refuted' for p in e['premises']):incoming[e['parent']].append((i,e))
    def cost(claims,bridges):
        return sum(1+min(visits.get(c,0),20)/4 for c in claims)+sum(1+min(visits.get(g['edges'][b]['parent'],0),20)/4 for b in bridges)
    def branch(i,e):
        claims=set();bridges={i} if e['rule']=='candidate' else set()
        for p in e['premises']:
            c,b=best[p];claims.update(c);bridges.update(b)
        return frozenset(claims),frozenset(bridges)
    # Bottom-up evaluation of the same greedy recurrence. Shared
    # subproblems are evaluated once, with no recursion-depth dependency.
    deps={i:set() if i in known else {p for _,e in incoming[i] for p in e['premises']} for i in incoming}
    parents={i:[] for i in deps}
    for i,ps in deps.items():
        for p in ps:parents[p].append(i)
    pending={i:len(ps) for i,ps in deps.items()}
    todo=deque(i for i,k in pending.items() if k==0);best={}
    while todo:
        i=todo.popleft()
        if i in known:best[i]=(frozenset(),frozenset())
        else:
            options=[branch(j,e) for j,e in incoming[i]]
            best[i]=min(options,key=lambda cb:(cost(*cb),sorted(cb[0]),sorted(cb[1]))) if options else (frozenset([i]),frozenset())
        for p in parents[i]:
            pending[p]-=1
            if not pending[p]:todo.append(p)
    if len(best)!=len(deps):raise ValueError('cyclic proof routes')
    out=[]
    for i,e in incoming['goal']:
        c,b=branch(i,e);out.append(dict(edge=i,claims=sorted(c),bridges=sorted(b),estimated_cost=cost(c,b)))
    if not out and 'goal' not in known and g['nodes']['goal']['status']=='open':out.append(dict(edge=None,claims=['goal'],bridges=[],estimated_cost=cost(['goal'],[])))
    return sorted(out,key=lambda r:(r['estimated_cost'],len(r['bridges']),r['edge'] or ''))


def choose_focus(g, route, reachable, fallback):
    """Select a proof obligation; explicitly surface a bridge whose premises are ready."""
    from discovery import closure
    known=closure(g)
    ready=[i for i in route['bridges'] if set(g['edges'][i]['premises'])<=known and g['edges'][i]['parent'] in reachable]
    if ready:
        i=ready[0];return g['edges'][i]['parent'],i
    candidates=[i for i in route['claims'] if i in reachable]
    if not candidates:return fallback,None
    def score(i):
        uses=sum(i in e['premises'] for e in g['edges'].values() if e['rule']!='rejected' and e['parent'] in reachable and not any(g['nodes'][p]['status']=='refuted' for p in e['premises']))
        visits=sum(a['focus']==i for a in g['history'])
        return (1+uses)/(1+visits)
    return max(candidates,key=score),None
