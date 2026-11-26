"""Invent polynomial representation candidates from explicit constraints.

These are untrusted search proposals. A map derived from an equality
is not automatically an equivalence or a valid domain transfer. Its use
must pass the theorem-recombination identity and hypothesis checker.
"""
from fractions import Fraction as Q
import polynomial as p
import representation_transfer as rt

def candidates(g):
    n=len(g['variables']);vs=[rt.var(n,i) for i in range(n)]
    out=[];seen=set()
    def add(a):
        if not a:return
        key=tuple(sorted(a.items()))
        if key not in seen:
            seen.add(key);out.append(a)
    for h in g['assumptions']:
        q=p.terms(h['terms'],n)
        add(q)
        if h['relation']=='zero':
            add({e:-v for e,v in q.items()})
            if all(sum(e)<=1 for e in q):
                for v in vs:
                    e=next(iter(v))
                    w=q.get(e,Q(0))
                    if w:
                        # If q=0, x_j equals this polynomial. Do not silently
                        # assume this during replay; it is only a useful image.
                        add({k:-c/w for k,c in q.items() if k!=e})
    for v in vs:
        add(rt.add(rt.constant(n,1),{e:-c for e,c in v.items()}))
    return out[:32]
