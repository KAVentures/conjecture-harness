"""Rational cone/SOS discovery on sparse polynomials with explicit hypotheses.

The search is incomplete; replay checks a polynomial identity, not a sampled
inequality. Assumptions are obligations, not automatically true facts.
"""
from fractions import Fraction as Q
from itertools import combinations
from rational_cone import solve

def clean(p):
    return {tuple(e):Q(c) for e,c in p.items() if c}

def add(a,b,w=1):
    out = dict(a)
    for e,c in b.items():
        out[e] = out.get(e,Q(0))+w*c
    return clean(out)

def mul(a,b):
    out = {}
    for e,c in a.items():
        for f,d in b.items():
            k = tuple(x+y for x,y in zip(e,f))
            out[k] = out.get(k,Q(0))+c*d
    return clean(out)

def derivative(p,d):
    out = {}
    for e,c in p.items():
        for i,k in enumerate(e):
            if k and d[i]:
                f = e[:i]+(k-1,)+e[i+1:]
                out[f] = out.get(f,Q(0))+c*k*d[i]
    return clean(out)

def _check(p,n):
    if not isinstance(p,dict) or len(p)>128:
        raise ValueError("polynomial size")
    for e,c in p.items():
        if not isinstance(e,tuple) or len(e)!=n or any(type(i) is not int or i<0 for i in e) or sum(e)>12 or type(c) not in (int,Q):
            raise ValueError("exact polynomial required")
    return clean(p)

def gram_squares(basis,matrix):
    """Exact LDL decomposition; returns weighted polynomial squares or None."""
    n = len(basis)
    if not 1<=n<=32 or len(matrix)!=n or any(len(r)!=n for r in matrix):
        raise ValueError("Gram shape")
    dim = len(basis[0])
    if not 1<=dim<=32 or len(set(basis))!=n or any(len(e)!=dim or any(type(k) is not int or k<0 for k in e) or sum(e)>6 for e in basis):
        raise ValueError("monomial basis")
    if any(type(x) not in (int,Q) for r in matrix for x in r):
        raise ValueError("exact Gram entries required")
    a = [list(map(Q,r)) for r in matrix]
    if any(a[i][j]!=a[j][i] for i in range(n) for j in range(n)):
        return None
    out = []
    for i in range(n):
        d = a[i][i]
        if d<0 or (d==0 and any(a[i][j] for j in range(i+1,n))):
            return None
        if not d:
            continue
        p = {basis[i]:Q(1)}
        for j in range(i+1,n):
            if a[i][j]:
                p[basis[j]]=a[i][j]/d
        out.append((d,p))
        for j in range(i+1,n):
            for k in range(i+1,n):
                a[j][k]-=a[i][j]*a[i][k]/d
    return out

def replay_gram(target,basis,matrix):
    squares = gram_squares(basis,matrix)
    if squares is None:
        return False
    result = {}
    for w,p in squares:
        result = add(result,mul(p,p),w)
    return result==_check(target,len(basis[0]))

def dictionary(n,assumptions,atoms,degree):
    """Generate products of constraints and squares of supplied atoms.

    All assumptions must be nonnegative; even products need no extra domain.
    Atoms are arbitrary polynomials, squared, never assumed positive.
    """
    if not 1<=n<=32 or not 0<=degree<=12 or len(assumptions)>12 or len(atoms)>24:
        raise ValueError("dictionary bounds")
    assumptions=[_check(p,n) for p in assumptions]
    atoms=[_check(p,n) for p in atoms]
    one={(0,)*n:Q(1)}
    factors=[((),one)]
    for k in (1,2):
        for ids in combinations(range(len(assumptions)),k):
            p=one
            for i in ids:
                p=mul(p,assumptions[i])
            factors.append((ids,p))
    squares=[(None,one)]+[(i,mul(p,p)) for i,p in enumerate(atoms)]
    out=[]
    for ids,p in factors:
        for j,s in squares:
            v=mul(p,s)
            if v and max(map(sum,v))<=degree:
                out.append((ids,j,v))
    return out

def discover(target,n,assumptions,atoms,degree=6,pivot_budget=256):
    target=_check(target,n)
    columns=dictionary(n,assumptions,atoms,degree)
    # Prefer low-degree, short generators and respect the exact LP bounds.
    columns.sort(key=lambda c:(len(c[0])+(c[1] is not None),len(c[2]),c[0],-1 if c[1] is None else c[1]))
    columns=columns[:256]
    try:
        weights,_=solve([p for _,_,p in columns],target,pivot_budget)
    except ValueError:
        return None
    if weights is None:
        return None
    cert=[(ids,j,w) for (ids,j,_),w in zip(columns,weights) if w]
    if not replay(target,n,assumptions,atoms,cert):
        raise ArithmeticError("cone certificate replay failed")
    return cert

def replay(target,n,assumptions,atoms,certificate):
    target=_check(target,n)
    if not 1<=n<=32 or len(assumptions)>12 or len(atoms)>24 or len(certificate)>256:
        raise ValueError("replay bounds")
    assumptions=[_check(p,n) for p in assumptions]
    atoms=[_check(p,n) for p in atoms]
    total={}
    for ids,j,w in certificate:
        if type(w) not in (int,Q) or w<0 or len(ids)>2 or len(set(ids))!=len(ids) or any(type(i) is not int or not 0<=i<len(assumptions) for i in ids):
            return False
        p={(0,)*n:Q(1)}
        for i in ids:
            p=mul(p,assumptions[i])
        if j is not None:
            if type(j) is not int or not 0<=j<len(atoms):
                return False
            p=mul(p,mul(atoms[j],atoms[j]))
        total=add(total,p,w)
    return total==target
