"""Exact tensor Bernstein certificates on rational boxes.

The domain and coefficients are exact. A negative Bernstein coefficient is
not a counterexample; bounded search may return unknown.
"""
from fractions import Fraction as Q
from itertools import product
from math import comb,prod
from inequality_invention import clean,derivative

def prepare(p,n,box=None):
    if type(n) is not int or not 1<=n<=32 or len(p)>128:
        raise ValueError("polynomial bounds")
    if any(len(e)!=n or any(type(k) is not int or k<0 for k in e) or sum(e)>12 or type(c) not in (int,Q) for e,c in p.items()):
        raise ValueError("exact polynomial required")
    if box is None:
        box=[(Q(0),Q(1))]*n
    if len(box)!=n or any(len(r)!=2 or any(type(x) not in (int,Q) for x in r) or not 0<=r[0]<r[1]<=1 for r in box):
        raise ValueError("invalid subbox")
    return clean(p),[(Q(l),Q(r)) for l,r in box]

def coefficients(p,n,box=None,budget=4096):
    p,box=prepare(p,n,box)
    d=[max((e[i] for e in p),default=0) for i in range(n)]
    if prod(k+1 for k in d)>budget:
        raise OverflowError("Bernstein grid budget")
    # Substitute x_i = l_i + (r_i-l_i)*y_i, expand power basis.
    a={}
    for e,c in p.items():
        for j in product(*(range(k+1) for k in e)):
            v=c*prod(comb(k,m)*l**(k-m)*(r-l)**m for k,m,(l,r) in zip(e,j,box))
            if v:
                a[j]=a.get(j,Q(0))+v
    a=clean(a)
    if prod(k+1 for k in d)*max(1,len(a))*n>2000000:
        raise OverflowError('Bernstein arithmetic budget')
    out={}
    for i in product(*(range(k+1) for k in d)):
        out[i]=sum((c*prod(Q(comb(k,m),comb(z,m)) for k,m,z in zip(i,j,d))
                    for j,c in a.items() if all(m<=k for m,k in zip(j,i))),Q(0))
    return out

def replay(p,n,cert):
    """Certificate is a binary midpoint splitting tree, or a leaf None."""
    try:
        p,box=prepare(p,n)
        stack=[(box,cert,0)];visited=0
        while stack:
            box,node,depth=stack.pop()
            visited+=1
            if visited>127 or depth>6:
                return False
            if node is None:
                if min(coefficients(p,n,box).values())<0:
                    return False
            else:
                if not isinstance(node,list) or len(node)!=3:
                    return False
                i,left,right=node
                if type(i) is not int or not 0<=i<n:
                    return False
                l,r=box[i];m=(l+r)/2
                a=box[:];b=box[:];a[i]=(l,m);b[i]=(m,r)
                stack.extend([(a,left,depth+1),(b,right,depth+1)])
        return True
    except (ValueError,TypeError,AttributeError,ArithmeticError,OverflowError):
        return False

def search(p,n,depth=3):
    p,box=prepare(p,n)
    if type(depth) is not int or not 0<=depth<=6:
        raise ValueError("depth limit")
    active=[i for i in range(n) if any(e[i] for e in p)]
    def f(box,k):
        if min(coefficients(p,n,box).values())>=0:
            return True,None
        if k==0 or not active:
            return False,None
        i=max(active,key=lambda i:(box[i][1]-box[i][0],-i))
        l,r=box[i];m=(l+r)/2
        a=box[:];b=box[:];a[i]=(l,m);b[i]=(m,r)
        ok,x=f(a,k-1)
        if not ok:
            return False,None
        ok,y=f(b,k-1)
        return (True,[i,x,y]) if ok else (False,None)
    try:
        ok,cert=f(box,depth)
    except OverflowError:
        ok,cert=False,None
    if ok and replay(p,n,cert):
        return dict(status='proved',certificate=cert)
    return dict(status='unknown')
