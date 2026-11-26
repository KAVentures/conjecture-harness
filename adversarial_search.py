"""Bounded deterministic exact rational search for polynomial counterexamples.

No optimization guarantee; only a negative evaluation (or nonzero equality
evaluation) is evidence. Each new point consumes one unit of budget.
"""
import itertools
from fractions import Fraction as Q

def search(value,n,domain,relation,budget,seeds=(),seen=None):
    if type(n) is not int or not 1<=n<=4 or domain not in ('real','nonnegative') or relation not in ('zero','nonnegative') or type(budget) is not int or not 0<=budget<=4096:raise ValueError('search limits')
    seen=set() if seen is None else set(seen)
    best=None;score=None;tested=0
    def objective(v):return -abs(v) if relation=='zero' else v
    def valid(x):return len(x)==n and all(len(str(v))<=80 for v in x) and (domain=='real' or all(v>=0 for v in x))
    def probe(x):
        nonlocal best,score,tested
        if not valid(x) or x in seen or tested>=budget:return None
        seen.add(x);tested+=1
        v=value(x);s=objective(v)
        if score is None or s<score:score,best=s,x
        if s<0:return dict(kind='point',point=list(map(str,x)))
        return None
    # Seed observations supplied by the caller have already been evaluated;
    # use their scores without charging the evaluation budget twice.
    for x,v in seeds:
        x=tuple(x)
        if not valid(x) or x not in seen:continue
        s=objective(v)
        if score is None or s<score:score,best=s,x
    for z in (0,1,2,-1):
        x=(Q(z),)*n
        hit=probe(x)
        if hit:return hit,tested
    if best is None:return None,tested
    dirs=[]
    for i in range(n):
        for sign in (1,-1):dirs.append(tuple(sign if j==i else 0 for j in range(n)))
    for i,j in itertools.combinations(range(n),2):
        for a,b in itertools.product((1,-1),repeat=2):dirs.append(tuple(a if k==i else b if k==j else 0 for k in range(n)))
    # Interleave fine local refinement and long-range probes, instead of
    # consuming all attempts at one scale. Every round has a fixed center.
    scales=(Q(1,8),Q(1),Q(4),Q(1,4),Q(16),Q(1,16),Q(64),Q(1,2),Q(256),Q(1,32),Q(1024),Q(1,64),Q(2),Q(8),Q(32),Q(1,128))
    for cycle in range(4):
        for h in scales:
            if tested>=budget:return None,tested
            center=best
            for d in dirs:
                x=tuple(a+h*b for a,b in zip(center,d))
                if domain=='nonnegative':x=tuple(max(Q(0),v) for v in x)
                hit=probe(x)
                if hit:return hit,tested
                if tested>=budget:return None,tested
        # Probe remote axis/diagonal configurations even when the incumbent
        # remains at a local minimum. Alternating signs are only used on R^n.
        for magnitude in (8,32,128,512,2048):
            for pattern in itertools.product((0,1) if domain=='nonnegative' else (-1,0,1),repeat=n):
                if not any(pattern):continue
                hit=probe(tuple(Q(magnitude*a) for a in pattern))
                if hit:return hit,tested
                if tested>=budget:return None,tested
    return None,tested
