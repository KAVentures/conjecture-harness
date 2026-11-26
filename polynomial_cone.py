"""Sparse polynomial certificates from simultaneous rational cone search."""
from fractions import Fraction as Q
from itertools import combinations
from rational_cone import solve as cone_solve


def mul(a,b):
    out={}
    for e,c in a.items():
        for f,d in b.items():
            k=tuple(x+y for x,y in zip(e,f));out[k]=out.get(k,Q(0))+c*d
    return {e:c for e,c in out.items() if c}


def monomials(n,cap):
    if n==0:
        yield ()
        return
    for k in range(cap+1):
        for tail in monomials(n-1,cap-k):yield (k,)+tail


def search(assumptions,relations,target,n,domain,pivot_budget=256):
    if not 1<=n<=4 or len(assumptions)!=len(relations) or len(assumptions)>8 or domain not in ('real','nonnegative') or any(r not in ('zero','nonnegative') for r in relations):raise ValueError('conditional cone limits')
    zero=(0,)*n;goal=set(target);degree=max([2]+[sum(e) for q in [target,*assumptions] for e in q]);pivots=0
    def admissible(e):return domain=='nonnegative' or not any(k%2 for k in e)
    products=[]
    degrees=[max(map(sum,q),default=-1) for q in assumptions]
    for k in (1,2,3):
        for ix in combinations(range(len(assumptions)),k):
            eq=any(relations[i]=='zero' for i in ix)
            if eq and k>1:continue # equality monomial multiples suffice for this search
            # Over Q the total degree of a nonzero product is additive.
            # Reject impossible products before expanding them.
            if any(degrees[i]<0 for i in ix) or sum(degrees[i] for i in ix)>8:continue
            q={zero:Q(1)}
            for i in ix:
                q=mul(q,assumptions[i])
                if len(q)>512 or any(c.numerator.bit_length()>256 or c.denominator.bit_length()>256 for c in q.values()):
                    q={};break
            if q:products.append((ix,q,eq,max(map(sum,q))))
    for cap in sorted({min(8,degree),min(8,degree+2)}):
        pool=[]
        for ix,q,eq,d in products:
            if d>cap or len(q)>80:continue
            for e in monomials(n,cap-d):
                if not(eq or admissible(e)):continue
                shifted={tuple(x+y for x,y in zip(e,f)) for f in q}
                if len(shifted|goal)>80:continue
                score=(not bool(shifted&goal),len(shifted-goal),sum(e),len(ix),ix,e)
                # Retain shared source polynomials, not a dense copy of
                # every shifted candidate column.
                pool.append((score,ix,e,q,eq))
        columns=[];meta=[];support=set(goal)
        for _,ix,e,q,eq in sorted(pool,key=lambda x:x[0]):
            if len(columns)+(2 if eq else 1)>160:break
            v={tuple(x+y for x,y in zip(e,f)):c for f,c in q.items()}
            if len(support|set(v))>80:continue
            support.update(v);columns.append(v);meta.append((ix,e,1))
            if eq:columns.append({k:-c for k,c in v.items()});meta.append((ix,e,-1))
        for e in sorted(support):
            if admissible(e):columns.append({e:Q(1)});meta.append(((),e,1))
        if pivots>=pivot_budget:break
        try:x,used=cone_solve(columns,target,pivot_budget-pivots)
        except ValueError:continue
        pivots+=used
        if x is None:continue
        rows={};residual={}
        for w,(ix,e,sign) in zip(x,meta):
            if not w:continue
            dest=rows.setdefault(ix,{}) if ix else residual
            dest[e]=dest.get(e,Q(0))+sign*w
        rows={ix:{e:c for e,c in q.items() if c} for ix,q in rows.items()}
        rows={ix:q for ix,q in rows.items() if q}
        if len(rows)>16:continue
        def encode(q):return [[list(e),str(c)] for e,c in sorted(q.items()) if c]
        if any(len(q)>64 or any(len(str(c))>80 for c in q.values()) for q in [*rows.values(),residual]):continue
        return dict(kind='conditional-identity',multipliers=[dict(indices=list(ix),multiplier=encode(q)) for ix,q in sorted(rows.items())],residual=dict(kind='sos',squares=[],monomials=encode(residual))),pivots
    return None,pivots
