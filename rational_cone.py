"""Bounded exact phase-I simplex for nonnegative rational combinations.

Only a replayed nonnegative solution is a certificate. No infeasibility
claim is exported when the artificial objective cannot reach zero.
"""
from fractions import Fraction as Q


def solve(columns,target,pivot_budget=256):
    if type(pivot_budget) is not int or not 1<=pivot_budget<=1024 or not isinstance(columns,list) or len(columns)>256 or not isinstance(target,dict):raise ValueError('cone limits')
    if any(not isinstance(c,dict) for c in columns):raise ValueError('column shape')
    keys=sorted(set(target).union(*(set(c) for c in columns)))
    if len(keys)>96:raise ValueError('row limit')
    n=len(columns);m=len(keys)
    if not m:return [Q(0)]*n,0
    rows=[];basis=list(range(n,n+m));width=n+m
    for i,k in enumerate(keys):
        b=Q(target.get(k,0));sgn=-1 if b<0 else 1
        rows.append([sgn*Q(c.get(k,0)) for c in columns]+[Q(j==i) for j in range(m)]+[abs(b)])
    costs=[Q(0)]*n+[Q(-1)]*m
    for pivots in range(pivot_budget+1):
        objective=sum(costs[j]*r[-1] for j,r in zip(basis,rows))
        if objective==0:
            x=[Q(0)]*n
            for j,r in zip(basis,rows):
                if j<n:x[j]=r[-1]
            if any(v<0 for v in x) or any(sum(v*Q(c.get(k,0)) for v,c in zip(x,columns))!=Q(target.get(k,0)) for k in keys):raise ArithmeticError('cone solution replay failed')
            return x,pivots
        if pivots==pivot_budget:return None,pivots
        if any(v.numerator.bit_length()>256 or v.denominator.bit_length()>256 for row in rows for v in row):return None,pivots
        basic=set(basis)
        enter=next((j for j in range(width) if j not in basic and costs[j]-sum(costs[b]*r[j] for b,r in zip(basis,rows))>0),None)
        if enter is None:return None,pivots
        choices=[(r[-1]/r[enter],basis[i],i) for i,r in enumerate(rows) if r[enter]>0]
        if not choices:return None,pivots
        _,_,i=min(choices);r=rows[i];d=r[enter];rows[i]=[v/d for v in r];basis[i]=enter
        for k,r in enumerate(rows):
            if k!=i and r[enter]:
                v=r[enter];rows[k]=[a-v*b for a,b in zip(r,rows[i])]
    return None,pivot_budget
