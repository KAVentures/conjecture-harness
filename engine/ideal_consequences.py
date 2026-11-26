"""Bounded Buchberger search with explicit original-generator multipliers."""
from fractions import Fraction as Q
from itertools import combinations

MAX_DEGREE=12
MAX_TERMS=256
MAX_BASIS=20

def clean(p):
    p={e:c for e,c in p.items() if c}
    if len(p)>MAX_TERMS or any(sum(e)>MAX_DEGREE or c.numerator.bit_length()>256 or c.denominator.bit_length()>256 for e,c in p.items()):raise ValueError('polynomial growth limit')
    return p

def add(a,b,scale=Q(1)):
    p=dict(a)
    for e,c in b.items():p[e]=p.get(e,Q(0))+scale*c
    return clean(p)

def mul(a,b):
    p={}
    for e,c in a.items():
        for f,d in b.items():
            k=tuple(x+y for x,y in zip(e,f));p[k]=p.get(k,Q(0))+c*d
    return clean(p)

def lead(p):return max(p,key=lambda e:(sum(e),e))
def shift(p,e,c):return clean({tuple(x+y for x,y in zip(f,e)):c*d for f,d in p.items()})
def scale(p,c):return clean({e:c*v for e,v in p.items()})
def vadd(a,b,c=Q(1)):return [add(p,q,c) for p,q in zip(a,b)]
def vshift(a,e,c):return [shift(p,e,c) for p in a]

def reduce(p,basis,width,limit=512):
    """Return remainder and multipliers in the original generators."""
    rem={};live=dict(p);used=[{} for _ in range(width)];steps=0
    while live:
        steps+=1
        if steps>limit:raise ValueError('reduction limit')
        e=lead(live);c=live[e]
        for q,v in basis:
            a=lead(q)
            if any(x<y for x,y in zip(e,a)):continue
            d=tuple(x-y for x,y in zip(e,a));k=c/q[a]
            live=add(live,shift(q,d,k),Q(-1));used=vadd(used,vshift(v,d,k));break
        else:rem[e]=c;del live[e]
    return clean(rem),used

def basis_search(generators,n,pair_budget=96):
    """A partial basis is still sound; no completeness assertion on exhaustion."""
    if type(n) is not int or not 1<=n<=4 or not 1<=len(generators)<=8 or type(pair_budget) is not int or not 0<=pair_budget<=256:raise ValueError('ideal limits')
    z=(0,)*n;w=len(generators);basis=[];pairs=[];tested=0
    def insert(p,v):
        c=p[lead(p)];p=scale(p,1/c);v=[scale(q,1/c) for q in v]
        j=len(basis);pairs.extend((i,j) for i in range(j));basis.append((p,v))
    for i,p in enumerate(generators):
        if not p:continue
        r,u=reduce(p,basis,w);v=[{z:Q(1)} if i==j else {} for j in range(w)]
        if r:insert(r,vadd(v,u,Q(-1)))
        if any(set(q)=={z} for q,_ in basis):return basis,tested
    while pairs and tested<pair_budget and len(basis)<MAX_BASIS:
        # Prefer low-degree overlaps. Relatively prime leading monomials
        # are skipped by Buchberger's product criterion.
        def lcm(pair):
            a,b=(lead(basis[i][0]) for i in pair);return tuple(max(x,y) for x,y in zip(a,b))
        pair=min(pairs,key=lambda ij:(sum(lcm(ij)),ij));pairs.remove(pair);tested+=1
        i,j=pair;p,v=basis[i];q,u=basis[j];a,b=lead(p),lead(q);m=lcm(pair)
        if all(not(x and y) for x,y in zip(a,b)):continue
        x=tuple(k-l for k,l in zip(m,a));y=tuple(k-l for k,l in zip(m,b))
        try:
            sp=add(shift(p,x,Q(1)),shift(q,y,Q(1)),Q(-1))
            sv=vadd(vshift(v,x,Q(1)),vshift(u,y,Q(1)),Q(-1))
            rem,used=reduce(sp,basis,w)
            if rem:insert(rem,vadd(sv,used,Q(-1)))
        except ValueError:continue
        if any(set(q)=={z} for q,_ in basis):break
    return basis,tested

def identity(generators,multipliers,n):
    if len(generators)!=len(multipliers):raise ValueError('multiplier width')
    out={}
    for p,q in zip(generators,multipliers):out=add(out,mul(p,q))
    return out

def candidates(generators,target,n,pair_budget=96):
    """Yield original-generator identities, including radical membership."""
    basis,tested=basis_search(generators,n,pair_budget);z=(0,)*n;w=len(generators)
    for p,v in basis:
        if p=={z:Q(1)}:
            yield 'inconsistent',1,{},v,tested;return
    rem,v=reduce(target,basis,w)
    yield 'residual',1,rem,v,tested
    if not rem:return
    power=target
    for k in (2,3):
        try:power=mul(power,target);r,v=reduce(power,basis,w)
        except ValueError:break
        if not r:yield 'zero-power',k,{},v,tested;return
