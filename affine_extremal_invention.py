"""Certified box/affine slice boundary reductions.

A direction in the nullspace preserves all affine equalities. Concavity on the
box suffices to reduce the minimum to endpoints. Endpoint coverage and any
subsequent face recursion remain explicit proof obligations.
"""
from fractions import Fraction as Q
from inequality_invention import derivative,discover,replay

def nullspace(rows,n):
    if not 1<=n<=32 or len(rows)>64 or any(len(r)!=n for r in rows):
        raise ValueError("linear system shape")
    if any(type(x) not in (int,Q) for r in rows for x in r):
        raise ValueError("exact linear system required")
    a=[list(map(Q,r)) for r in rows]
    pivots=[]
    for j in range(n):
        k=next((k for k in range(len(pivots),len(a)) if a[k][j]),None)
        if k is None:
            continue
        i=len(pivots); a[i],a[k]=a[k],a[i]
        v=a[i][j];a[i]=[x/v for x in a[i]]
        for k in range(len(a)):
            if k!=i:
                v=a[k][j];a[k]=[x-v*y for x,y in zip(a[k],a[i])]
        pivots.append(j)
    out=[]
    for j in range(n):
        if j in pivots:
            continue
        d=[Q(0)]*n;d[j]=Q(1)
        for i,k in enumerate(pivots):
            d[k]=-a[i][j]
        out.append(d)
    return out

def box_hypotheses(n):
    zero=(0,)*n
    out=[]
    for i in range(n):
        e=tuple(int(j==i) for j in range(n))
        out.extend([{e:Q(1)},{zero:Q(1),e:Q(-1)}])
    return out

def curvature(p,d):
    return {e:-c for e,c in derivative(derivative(p,d),d).items()}

def discover_directions(p,rows,n,atoms=()):
    """Try basis directions and pairwise sums/differences; return checked leads."""
    basis=nullspace(rows,n)
    directions=basis[:]
    for i,x in enumerate(basis):
        for y in basis[i+1:]:
            directions.extend([[a+b for a,b in zip(x,y)],[a-b for a,b in zip(x,y)]])
    if 2*n>12:
        return []
    out=[]
    for d in directions[:64]:
        c=curvature(p,d)
        cert=discover(c,n,box_hypotheses(n),list(atoms))
        if cert is not None:
            out.append((d,cert))
    return out

def verify_direction(p,rows,n,d,atoms,cert):
    if len(d)!=n or not any(d) or any(type(x) not in (int,Q) for x in d):
        return False
    if any(len(r)!=n or sum(x*y for x,y in zip(r,d)) for r in rows):
        return False
    return replay(curvature(p,d),n,box_hypotheses(n),list(atoms),cert)

def endpoints(x,d):
    """Exact feasible interval for x+s*d inside the unit box."""
    if len(x)!=len(d) or not any(d) or any(type(v) not in (int,Q) for v in [*x,*d]) or any(not 0<=v<=1 for v in x):
        raise ValueError("invalid point/direction")
    lower=[];upper=[]
    for a,b in zip(map(Q,x),map(Q,d)):
        if b:
            l,r=sorted((-a/b,(1-a)/b));lower.append(l);upper.append(r)
    return max(lower),min(upper)
