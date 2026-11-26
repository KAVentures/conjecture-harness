"""Exact eventual signs of finite rational exponential-polynomial sequences."""
from fractions import Fraction as Q
from math import comb

MAX_N=4096

def canonical(rows):
    if not isinstance(rows,(list,tuple)) or len(rows)>16:raise ValueError('term count')
    groups={}
    for b,k,c in rows:
        if type(b) not in (int,Q) or b<=0 or type(k) is not int or not 0<=k<=8 or type(c) not in (int,Q):raise ValueError('term shape')
        key=(Q(b),k);groups[key]=groups.get(key,Q(0))+Q(c)
    return {key:v for key,v in groups.items() if v}

def value(terms,n):
    return sum((c*b**n*n**k for (b,k),c in terms.items()),Q(0))

def tail(terms,n):
    """Prove dominant monomial exceeds absolute sum of all other terms."""
    if not terms:return True
    (b,k),c=max(terms.items());other=[(a,j,d) for (a,j),d in terms.items() if (a,j)!=(b,k)]
    # Ratios of each subordinate monomial to b^n n^k are nonincreasing
    # after n if (a/b)*(1+1/n)^(j-k) <= 1 when j>k.
    if any(j>k and a*Q(n+1,n)**(j-k)>b for a,j,d in other):return False
    total=sum((abs(d)*(a/b)**n*Q(n)**(j-k) for a,j,d in other),Q(0))
    return total<abs(c)

def classify(rows,start,quantifier):
    if type(start) is not int or not 1<=start<=MAX_N or quantifier not in ('all','eventual'):raise ValueError('sequence scope')
    t=canonical(rows)
    if not t:return dict(outcome='proved',kind='zero')
    (b,k),c=max(t.items());sgn=1 if c>0 else -1
    if quantifier=='eventual':
        # For a<b, (a/b)^n n^j tends to zero; for a=b, j<k.
        # The leading term gives the exact eventual sign, even if an
        # explicit threshold exceeds our computational budget.
        return dict(outcome='proved' if sgn>0 else 'refuted',kind='dominance',base=str(b),degree=k,coefficient=str(c))
    for n in range(start,min(MAX_N,start+64)+1):
        if value(t,n)<0:return dict(outcome='refuted',kind='point',n=n)
    n=start
    while True:
        if tail(t,n):
            if sgn<0:return dict(outcome='refuted',kind='point',n=n)
            for i in range(start,n):
                if value(t,i)<0:return dict(outcome='refuted',kind='point',n=i)
            return dict(outcome='proved',kind='tail',threshold=n)
        if n==MAX_N:break
        n=min(MAX_N,max(n+1,2*n))
    return dict(outcome='unknown')

def replay(rows,start,quantifier,cert):
    try:
        if not isinstance(cert,dict) or cert.get('outcome') not in ('proved','refuted'):return None
        if type(start) is not int or not 1<=start<=MAX_N or quantifier not in ('all','eventual'):return None
        t=canonical(rows);kind=cert.get('kind')
        if kind=='zero':return 'proved' if cert==dict(outcome='proved',kind='zero') and not t else None
        if quantifier=='eventual':
            expected=classify(rows,start,quantifier)
            return expected['outcome'] if cert==expected else None
        if kind=='point' and set(cert)=={'outcome','kind','n'}:
            n=cert['n'];return 'refuted' if cert['outcome']=='refuted' and type(n) is int and start<=n<=MAX_N and value(t,n)<0 else None
        if kind=='tail' and set(cert)=={'outcome','kind','threshold'}:
            n=cert['threshold']
            return 'proved' if cert['outcome']=='proved' and t and t[max(t)]>0 and type(n) is int and start<=n<=MAX_N and tail(t,n) and all(value(t,i)>=0 for i in range(start,n)) else None
    except (ValueError,TypeError,KeyError,ArithmeticError):pass
    return None
