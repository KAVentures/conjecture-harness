"""All-index coefficient inequalities for rational generating functions.

Discover inductive cones for the exact companion recurrence; never infer
infinite coefficient positivity from a finite prefix.
"""
from fractions import Fraction as Q
import json
from itertools import combinations
from affine import rational
from rational_cone import solve as cone
from runtime import strict_json
PREFIX='Rational generating function nonnegativity: '
MAX_DEGREE=16
MAX_ROWS=40
def trim(a):
    a=list(a)
    while len(a)>1 and not a[-1]:a.pop()
    return a
def normalize(s):
    if not isinstance(s,dict) or set(s)!={'numerator','denominator'}:raise ValueError('claim')
    def poly(a):
        if not isinstance(a,list) or not 1<=len(a)<=MAX_DEGREE+1:raise ValueError('degree')
        return trim(list(map(rational,a)))
    p,q=poly(s['numerator']),poly(s['denominator'])
    if not q[0]:raise ValueError('denominator constant')
    return dict(numerator=[str(v/q[0]) for v in p],denominator=[str(v/q[0]) for v in q])
def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))
def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('not rational GF')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical GF')
    return s
def data(s):
    s=normalize(s);return list(map(Q,s['numerator'])),list(map(Q,s['denominator']))
def coeffs(p,q,N):
    a=[]
    for n in range(N+1):
        v=(p[n] if n<len(p) else Q(0))-sum(q[j]*a[n-j] for j in range(1,min(n+1,len(q))))
        if v.numerator.bit_length()>4096 or v.denominator.bit_length()>4096:raise OverflowError('coefficient growth')
        a.append(v)
    return a
def state(p,q):
    d=len(q)-1;n=max(len(p)-1,d-1);a=coeffs(p,q,n)
    M=[[-v for v in q[1:]]]+[[Q(int(j==i-1)) for j in range(d)] for i in range(1,d)]
    return a,M,list(reversed(a[-d:])) if d else []
def dot(a,b):return sum((x*y for x,y in zip(a,b)),Q(0))
def pull(r,M):return [sum(r[i]*M[i][j] for i in range(len(r))) for j in range(len(r))]
def replay(s,cert):
    try:
        p,q=data(s);d=len(q)-1
        if not isinstance(cert,dict) or len(json.dumps(cert))>18000:return None
        if set(cert)=={'index'}:
            n=cert['index']
            if type(n) is not int or not 0<=n<=256:return None
            return 'refuted' if coeffs(p,q,n)[n]<0 else None
        if cert=={'kind':'polynomial'}:return 'proved' if d==0 and min(p)>=0 else None
        if not d or set(cert)!={'kind','rows','steps'} or cert['kind']!='invariant-cone':return None
        a,M,x=state(p,q)
        if min(a)<0:return None
        rows=cert['rows'];steps=cert['steps']
        if not isinstance(rows,list) or not 1<=len(rows)<=MAX_ROWS or not isinstance(steps,list) or len(steps)!=len(rows):return None
        if any(not isinstance(r,list) or len(r)!=d for r in rows):return None
        rows=[list(map(rational,r)) for r in rows]
        if rows[0]!=[Q(1)]+[Q(0)]*(d-1) or any(dot(r,x)<0 for r in rows):return None
        for r,w in zip(rows,steps):
            if not isinstance(w,list) or len(w)!=len(rows):return None
            w=list(map(rational,w))
            if any(v<0 for v in w) or [sum(v*a[j] for v,a in zip(w,rows)) for j in range(d)]!=pull(r,M):return None
        return 'proved'
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,OverflowError,RecursionError):return None
def solve(s):
    p,q=data(s)
    try:
        a=coeffs(p,q,64)
        for i,v in enumerate(a):
            if v<0:return dict(status='counterexample',certificate={'index':i})
        if len(q)==1:return dict(status='proved',certificate={'kind':'polynomial'})
        a,M,x=state(p,q);d=len(M);rows=[]
        def add(r):
            if any(r) and dot(r,x)>=0:
                v=abs(next(v for v in r if v));r=[w/v for w in r]
                if r not in rows and len(rows)<MAX_ROWS:rows.append(r)
        E=[[Q(int(i==j)) for j in range(d)] for i in range(d)]
        for r in E:add(r)
        # Discrete monotonicity and scaled growth invariants; useful even
        # when denominator coefficients have alternating signs.
        scales=[Q(1),Q(1,2),Q(2),Q(3),Q(3,2)]
        for i,j in combinations(range(d),2):
            for k in scales:
                add([a-k*b for a,b in zip(E[i],E[j])])
                add([b-k*a for a,b in zip(E[i],E[j])])
        r=E[0]
        for _ in range(6):
            r=pull(r,M);add(r)
        # Simultaneous inductive invariant search with deletion of unclosed
        # candidates. Removing a candidate never asserts it false.
        for _ in range(MAX_ROWS):
            cols=[dict(enumerate(r)) for r in rows];steps=[];keep=[]
            for i,r in enumerate(rows):
                w,_=cone(cols,dict(enumerate(pull(r,M))),pivot_budget=128)
                if w is not None:keep.append(i);steps.append(list(map(str,w)))
            if 0 not in keep:break
            if len(keep)==len(rows):
                cert=dict(kind='invariant-cone',rows=[list(map(str,r)) for r in rows],steps=steps)
                if replay(s,cert)=='proved':return dict(status='proved',certificate=cert)
                break
            rows=[rows[i] for i in keep]
    except (ValueError,OverflowError):pass
    return dict(status='unknown',scope='bounded invariant discovery, all-index replay')
def auto_discharge(g,limit=1):
    from deep_invention_dispatch import discharge
    return discharge(g,parse_statement,solve,replay,'rational-gf-',limit)
