"""Discover finite inductive polynomial ideals via exact multivariate reduction.

No Groebner completeness claim. A certificate proves that the initial state
lies in the common zero set and the transition preserves that zero set.
"""
import json
from fractions import Fraction as Q
from symbolic_discovery import terms,encode,add
from representation_transfer import mul

MAX_BASIS=6
MAX_STEPS=128

def lead(p):return max(p,key=lambda e:(sum(e),e))

def divide(p,basis):
    """Bounded multivariate division with an explicit quotient/remainder identity."""
    from dynamics_discovery import bounded
    live=dict(p);rem={};qs=[{} for _ in basis];steps=0
    if any(not q for q in basis):raise ValueError('zero divisor')
    while live:
        if steps>=MAX_STEPS:raise ValueError('division limit')
        steps+=1;e=lead(live);c=live[e]
        for j,q in enumerate(basis):
            a=lead(q)
            if any(x<y for x,y in zip(e,a)):continue
            t={tuple(x-y for x,y in zip(e,a)):c/q[a]}
            qs[j]=bounded(add(qs[j],t))
            live=bounded(add(live,mul(t,q),Q(-1)))
            break
        else:
            rem[e]=c;del live[e]
    return qs,rem

def replay(s,cert):
    from dynamics_discovery import normalize,substitute,eval_poly,bounded
    try:
        s=normalize(s)
        if s['kind']!='orbit-zero' or not isinstance(cert,dict) or set(cert)!={'kind','basis','multipliers'} or cert['kind']!='ideal-induction':return False
        n=len(s['variables']);raw=cert['basis'];ms=cert['multipliers']
        if not isinstance(raw,list) or not 1<=len(raw)<=MAX_BASIS or not isinstance(ms,list) or len(ms)!=len(raw):return False
        basis=[terms(t,n,8) for t in raw]
        if basis[0]!=terms(s['observable'],n,8) or any(not p for p in basis):return False
        initial=list(map(Q,s['initial']));images=[terms(t,n,2) for t in s['transition']]
        if any(eval_poly(p,initial) for p in basis):return False
        for p,row in zip(basis,ms):
            if not isinstance(row,list) or len(row)!=len(basis):return False
            total={}
            for q,v in zip(basis,row):total=bounded(add(total,mul(terms(v,n,8),q)))
            if total!=substitute(p,images):return False
        return True
    except (ValueError,TypeError,KeyError,ArithmeticError,AttributeError):return False

def discover(s):
    from dynamics_discovery import normalize,substitute,eval_poly
    try:
        s=normalize(s)
        if s['kind']!='orbit-zero':return None
        n=len(s['variables']);target=terms(s['observable'],n,8)
        initial=list(map(Q,s['initial']));images=[terms(t,n,2) for t in s['transition']]
        if not target or eval_poly(target,initial):return None
        basis=[target]
        while True:
            added=False
            for p in list(basis):
                _,r=divide(substitute(p,images),basis)
                if not r:continue
                if len(basis)>=MAX_BASIS or eval_poly(r,initial):return None
                # Scaling is optional; use a monic leading coefficient to
                # reduce arithmetic growth. Keep target exactly as supplied.
                r={e:c/r[lead(r)] for e,c in r.items()}
                basis.append(r);added=True;break
            if not added:break
        multipliers=[]
        for p in basis:
            qs,r=divide(substitute(p,images),basis)
            if r:return None
            multipliers.append([encode(q) for q in qs])
        cert=dict(kind='ideal-induction',basis=[encode(p) for p in basis],multipliers=multipliers)
        if len(json.dumps(cert))>15000:return None
        if not replay(s,cert):raise ArithmeticError('ideal induction replay failed')
        return cert
    except ValueError:return None
