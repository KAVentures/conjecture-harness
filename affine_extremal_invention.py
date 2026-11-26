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


def transportation_directions(rows,cols):
    """All elementary 4-cycle directions for a rectangular array."""
    if type(rows) is not int or type(cols) is not int or not 1<=rows*cols<=32 or rows<1 or cols<1:
        raise ValueError("array limit")
    from itertools import combinations
    for i,j in combinations(range(rows),2):
        for u,v in combinations(range(cols),2):
            d=[Q(0)]*(rows*cols)
            for a,b,w in [(i,u,1),(j,v,1),(i,v,-1),(j,u,-1)]:
                d[a*cols+b]=Q(w)
            yield d

def transportation_equalities(rows,cols):
    return [[int(i//cols==j) for i in range(rows*cols)] for j in range(rows)]+[
            [int(i%cols==j) for i in range(rows*cols)] for j in range(cols)]

def search_box_directions(p,rows,n,directions,depth=2,budget=32):
    """Certify directional concavity using exact tensor Bernstein bounds."""
    from box_bernstein import search
    from itertools import islice
    out=[]
    for d in islice(directions,budget):
        if len(d)!=n or not any(d) or any(type(x) not in (int,Q) for x in d):
            continue
        if any(len(r)!=n or sum(x*y for x,y in zip(r,d)) for r in rows):
            continue
        r=search(curvature(p,d),n,depth)
        if r['status']=='proved':
            out.append((d,r['certificate']))
    return out

def verify_box_direction(p,rows,n,d,cert):
    from box_bernstein import replay
    return (len(d)==n and any(d) and all(type(x) in (int,Q) for x in d)
            and all(len(r)==n and not sum(x*y for x,y in zip(r,d)) for r in rows)
            and replay(curvature(p,d),n,cert))
