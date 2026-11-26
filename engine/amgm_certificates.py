"""Exact weighted AM-GM certificates for sparse polynomial nonnegativity."""
from fractions import Fraction as Q
from itertools import combinations
from math import lcm

MAX_WEIGHT=32
MAX_CIRCUITS=24

def weights(points,target):
    """Unique rational barycentric coordinates on an affinely independent face."""
    k=len(points);n=len(target)
    a=[[Q(1)]*k+[Q(1)]]+[[Q(p[j]) for p in points]+[Q(target[j])] for j in range(n)]
    for i in range(k):
        pivot=next((j for j in range(i,len(a)) if a[j][i]),None)
        if pivot is None:return None
        a[i],a[pivot]=a[pivot],a[i];d=a[i][i];a[i]=[x/d for x in a[i]]
        for j in range(len(a)):
            if j!=i and a[j][i]:
                d=a[j][i];a[j]=[x-d*y for x,y in zip(a[j],a[i])]
    if any(row[-1] for row in a[k:]):return None
    xs=[row[-1] for row in a[:k]]
    if any(x<=0 for x in xs):return None
    w=lcm(*(x.denominator for x in xs))
    return [int(x*w) for x in xs] if w<=MAX_WEIGHT else None

def sufficient(coeffs,ws,b):
    """Compare integer powers; no logarithms or irrational approximations."""
    w=sum(ws);v=Q(1)
    for a,k in zip(coeffs,ws):v*= (a*w/k)**k
    return v>=b**w

def admissible(e,domain):return domain=='nonnegative' or all(k%2==0 for k in e)

def replay(poly,domain,cert):
    try:
        if domain not in ('real','nonnegative') or not isinstance(cert,dict) or set(cert)!={'kind','circuits'} or cert['kind']!='amgm':return False
        rows=cert['circuits'];live=dict(poly);n=len(next(iter(poly),()))
        if not isinstance(rows,list) or len(rows)>MAX_CIRCUITS:return False
        def exponent(e):
            if not isinstance(e,list) or len(e)!=n or any(type(k) is not int or k<0 for k in e) or sum(e)>8:raise ValueError('exponent')
            return tuple(e)
        def rational(x):
            if not isinstance(x,str) or len(x)>80:raise ValueError('coefficient')
            q=Q(x)
            if str(q)!=x or q<=0:raise ValueError('positive canonical rational required')
            return q
        for row in rows:
            if not isinstance(row,dict) or set(row)!={'target','coefficient','terms'}:return False
            beta=exponent(row['target']);b=rational(row['coefficient']);ts=row['terms']
            if not isinstance(ts,list) or not 2<=len(ts)<=n+1:return False
            es=[];cs=[];ws=[]
            for t in ts:
                if not isinstance(t,list) or len(t)!=3 or type(t[2]) is not int or not 1<=t[2]<=MAX_WEIGHT:return False
                e=exponent(t[0]);c=rational(t[1]);w=t[2]
                if not admissible(e,domain) or e==beta or e in es:return False
                es.append(e);cs.append(c);ws.append(w)
            w=sum(ws)
            if w>MAX_WEIGHT or any(sum(k*e[j] for k,e in zip(ws,es))!=w*beta[j] for j in range(n)) or not sufficient(cs,ws,b):return False
            for e,c in zip(es,cs):live[e]=live.get(e,Q(0))-c
            live[beta]=live.get(beta,Q(0))+b
        return all(not c or c>0 and admissible(e,domain) for e,c in live.items())
    except (ValueError,TypeError,KeyError,ArithmeticError,AttributeError):return False

def solve(poly,domain,budget=512):
    if domain not in ('real','nonnegative') or type(budget) is not int or not 1<=budget<=4096:raise ValueError('search limits')
    live=dict(poly);n=len(next(iter(poly),()));rows=[];tested=0
    # Odd positive monomials on R^n can be bounded by their absolute value
    # only after a separate sign argument; this solver deliberately abstains.
    if any(c>0 and not admissible(e,domain) for e,c in live.items()):return None,tested
    for beta,b in sorted([(e,-c) for e,c in live.items() if c<0],key=lambda t:(-t[1],t[0])):
        found=None
        pool=sorted(e for e,c in live.items() if c>0 and admissible(e,domain))
        for k in range(2,min(n+1,len(pool))+1):
            for es in combinations(pool,k):
                if tested>=budget:return None,tested
                tested+=1;ws=weights(es,beta)
                if not ws:continue
                available=[live[e] for e in es];w=sum(ws);equal=[b*Q(k,w) for k in ws]
                if all(a<=c for a,c in zip(equal,available)):cs=equal
                elif sufficient(available,ws,b):
                    # Shrink all available coefficients by a common rational
                    # factor, preserving the weighted product condition.
                    lo,hi=Q(0),Q(1)
                    for _ in range(12):
                        mid=(lo+hi)/2
                        if sufficient([a*mid for a in available],ws,b):hi=mid
                        else:lo=mid
                    cs=[a*hi for a in available]
                else:continue
                found=(es,cs,ws);break
            if found:break
        if not found or len(rows)>=MAX_CIRCUITS:return None,tested
        es,cs,ws=found
        if any(len(str(c))>80 for c in [b,*cs]):return None,tested
        rows.append(dict(target=list(beta),coefficient=str(b),terms=[[list(e),str(c),k] for e,c,k in zip(es,cs,ws)]))
        for e,c in zip(es,cs):live[e]-=c
        live[beta]+=b
    cert=dict(kind='amgm',circuits=rows)
    if not replay(poly,domain,cert):raise ArithmeticError('AM-GM replay failed')
    return cert,tested
