"""Exact, closed finite benchmarks. Not evidence of open-problem solving ability."""
from itertools import product, combinations
import argparse, json, time
from verify import ALPHABET, packing
from certificates import replay


def max_clique(adj):
    """Exhaustive branch-and-bound. Greedy coloring supplies a valid upper bound.
    adj: symmetric loop-free bit adjacency, validated before search.
    """
    n=len(adj)
    for i,a in enumerate(adj):
        if type(a) is not int or a<0 or a>>n or a & (1<<i): raise ValueError('invalid adjacency')
        if any(bool(a & (1<<j)) != bool(adj[j] & (1<<i)) for j in range(n)): raise ValueError('asymmetric adjacency')
    best=[]; nodes=0
    def color(P):
        order=[]; bounds=[]; c=0
        while P:
            c+=1; Q=P
            while Q:
                bit=Q & -Q; v=bit.bit_length()-1
                order.append(v); bounds.append(c); P^=bit; Q &= ~bit & ~adj[v]
        return order,bounds
    def visit(P,clique):
        nonlocal best,nodes
        nodes+=1
        if len(clique)>len(best): best=clique[:]
        order,bounds=color(P)
        for v,b in reversed(list(zip(order,bounds))):
            if len(clique)+b<=len(best): return
            bit=1<<v
            visit(P & adj[v],clique+[v]); P &= ~bit
    visit((1<<n)-1,[])
    return best,nodes


def graph(n):
    if n not in (1,2): raise ValueError('benchmark restricted to powers 1 and 2')
    words=list(product(range(10),repeat=n)); sets=list(map(set,ALPHABET))
    adj=[sum(1<<j for j,b in enumerate(words) if any(sets[x].isdisjoint(sets[y]) for x,y in zip(a,b))) for a in words]
    return words,adj


def run():
    reports=[]
    for n,expected in [(1,2),(2,5)]:
        start=time.monotonic(); words,adj=graph(n); clique,nodes=max_clique(adj)
        w={'words':[list(words[i]) for i in clique]}; exact=packing(w['words']); independent=replay('shannon',w,exact)
        reports.append(dict(power=n,expected=expected,maximum=len(clique),passed=len(clique)==expected and independent['replayed'],
                            nodes=nodes,witness=w,independent=independent,seconds=round(time.monotonic()-start,6)))
    return {'scope':'known finite maxima; exhaustive search with greedy coloring upper bounds; no asymptotic claim','results':reports}

if __name__=='__main__':
    result=run(); print(json.dumps(result,indent=2)); raise SystemExit(0 if all(x['passed'] for x in result['results']) else 1)
