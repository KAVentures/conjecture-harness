"""Exact induction for index-dependent affine vector recurrences.

State x(n+1)=M(n)x(n)+b(n), with rational polynomial coefficients in n.
Invariants are affine inequalities in the state with polynomial-in-n
coefficients. The search uses nonnegative Newton-basis multipliers;
certificate replay checks both the initial state and symbolic induction step.
"""
from fractions import Fraction as Q
from math import factorial
from rational_cone import solve

def poly(raw):
    if not isinstance(raw,(tuple,list)) or len(raw)>13 or any(type(v) not in (int,Q) for v in raw):
        raise ValueError("polynomial coefficients must be exact")
    a=list(map(Q,raw))
    while a and not a[-1]:
        a.pop()
    return tuple(a)

def add(a,b):
    return poly([ (a[i] if i<len(a) else 0)+(b[i] if i<len(b) else 0)
                   for i in range(max(len(a),len(b))) ])

def scale(a,w):
    return poly([w*x for x in a])

def mul(a,b):
    if not a or not b:
        return ()
    out=[Q(0)]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):
            out[i+j]+=x*y
    return poly(out)

def shift(a):
    from math import comb
    return poly([sum((a[j]*comb(j,i) for j in range(i,len(a))),Q(0))
                 for i in range(len(a))])

def newton(k):
    if type(k) is not int or not 0<=k<=6:
        raise ValueError("Newton degree bound")
    p=(Q(1),)
    for i in range(k):
        p=mul(p,(-Q(i),Q(1)))
    return scale(p,Q(1,factorial(k)))

def normalize(M,b,x0,claims):
    d=len(x0)
    if not 1<=d<=8 or len(M)!=d or len(b)!=d or any(len(row)!=d for row in M) or not 1<=len(claims)<=12:
        raise ValueError("recurrence bounds")
    if any(type(x) not in (int,Q) for x in x0) or any(len(c)!=d+1 for c in claims):
        raise ValueError("state/invariant shape")
    M=[[poly(p) for p in row] for row in M]
    b=[poly(p) for p in b]
    claims=[[poly(p) for p in c] for c in claims]
    if any(len(p)>7 for row in M for p in row) or any(len(p)>7 for p in b) or any(len(p)>7 for c in claims for p in c):
        raise ValueError("input degree bound")
    return M,b,list(map(Q,x0)),claims

def pullback(M,b,c):
    """Substitute n+1 and the recurrence into c(n+1,x(n+1))."""
    d=len(b)
    shifted=[shift(p) for p in c]
    out=[shifted[0]]+[() for _ in range(d)]
    for i in range(d):
        out[0]=add(out[0],mul(shifted[i+1],b[i]))
        for j in range(d):
            out[j+1]=add(out[j+1],mul(shifted[i+1],M[i][j]))
    return out

def sparse(c):
    return {(i,j):v for i,p in enumerate(c) for j,v in enumerate(p) if v}

def initial(c,x0):
    return (c[0][0] if c[0] else 0)+sum((p[0] if p else 0)*x for p,x in zip(c[1:],x0))

def generators(claims,degree):
    if type(degree) is not int or not 0<=degree<=6:
        raise ValueError("multiplier degree bound")
    d=len(claims[0])
    out=[]
    for k in range(degree+1):
        p=newton(k)
        out.append((None,k,[p]+[()]*(d-1)))
        for i,c in enumerate(claims):
            out.append((i,k,[mul(p,q) for q in c]))
    return out

def replay(M,b,x0,claims,certificate):
    try:
        M,b,x0,claims=normalize(M,b,x0,claims)
        if not isinstance(certificate,list) or len(certificate)!=len(claims) or any(initial(c,x0)<0 for c in claims):
            return False
        for c,rows in zip(claims,certificate):
            if not isinstance(rows,list) or len(rows)>128:
                return False
            total=[() for _ in c]
            for i,k,w in rows:
                if type(w) not in (int,Q) or w<0 or (i is not None and (type(i) is not int or not 0<=i<len(claims))):
                    return False
                p=newton(k)
                gen=[p]+[()]*(len(c)-1) if i is None else [mul(p,q) for q in claims[i]]
                total=[add(a,scale(g,w)) for a,g in zip(total,gen)]
            if total!=pullback(M,b,c):
                return False
        return True
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError):
        return False

def discover(M,b,x0,claims,degree=2):
    M,b,x0,claims=normalize(M,b,x0,claims)
    if any(initial(c,x0)<0 for c in claims):
        return None
    cols=generators(claims,degree);raw=[sparse(c) for _,_,c in cols]
    cert=[]
    for c in claims:
        try:
            w,_=solve(raw,sparse(pullback(M,b,c)))
        except ValueError:
            return None
        if w is None:
            return None
        cert.append([(i,k,v) for (i,k,_),v in zip(cols,w) if v])
    if not replay(M,b,x0,claims,cert):
        raise ArithmeticError("induction certificate replay failed")
    return cert

def linear_candidates(M,b,x0,degree=2):
    """Invent simple state inequalities and affine lower bounds in n.

    These are heuristically generated proposals; only replayed induction
    establishes them. No claim is made about completeness.
    """
    d=len(x0)
    for i in range(d):
        e=[() for _ in range(d+1)];e[i+1]=(Q(1),)
        for const in ((),(-Q(x0[i]),),(Q(0),Q(-1)),(Q(0),Q(-1,2),Q(-1,2))):
            c=e[:];c[0]=poly(list(const))
            r=discover(M,b,x0,[c],degree)
            if r is not None:
                yield c,r
