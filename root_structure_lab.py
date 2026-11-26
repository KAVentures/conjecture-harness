"""Exact root-location and strict interlacing certificates over Q.

The search is a checked algebraic criterion, not numerical root finding.
"""
import json
from fractions import Fraction as Q
from affine import rational
from runtime import strict_json
from univariate_sign import trim,derivative,gcd,exact_divide,monic,sturm,variation,divide
PREFIX='Polynomial root structure: '
def normalize(s):
    if not isinstance(s,dict) or s.get('kind') not in ('nonpositive-roots','strict-interlacing'):raise ValueError('claim')
    kind=s['kind'];keys={'kind','p'} if kind=='nonpositive-roots' else {'kind','p','q'}
    if set(s)!=keys:raise ValueError('claim shape')
    def poly(a):
        if not isinstance(a,list) or not 1<=len(a)<=17:raise ValueError('degree')
        a=trim(list(map(rational,a)))
        if not a:raise ValueError('zero polynomial')
        return [str(v) for v in a]
    p=poly(s['p'])
    if kind=='nonpositive-roots':return dict(kind=kind,p=p)
    q=poly(s['q'])
    if len(p)!=len(q)+1:raise ValueError('adjacent degrees')
    return dict(kind=kind,p=p,q=q)
def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))
def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('not root structure')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical roots')
    return s
def classify(s):
    s=normalize(s);p=list(map(Q,s['p']))
    if s['kind']=='nonpositive-roots':
        # The squarefree part has exactly the same distinct roots.
        f=exact_divide(p,gcd(p,derivative(p)));seq=sturm(f)
        real=variation(seq,'minus')-variation(seq,'plus')
        positive=variation(seq,'zero-plus')-variation(seq,'plus')
        return dict(kind='sturm-root-count',distinct_degree=len(f)-1,real=real,positive=positive) if real==len(f)-1 and positive==0 else None
    a,b=monic(p),monic(list(map(Q,s['q'])));scales=[]
    # a=(x-c)b-k*c0 with c0 monic, k>0. If b and c0 strictly
    # interlace then a and b do too, by signs at b's roots and infinity.
    while len(b)>1:
        _,r=divide(a,b)
        if len(r)!=len(b)-1 or r[-1]>=0:return None
        scales.append(str(-r[-1]));a,b=b,monic(r)
    return dict(kind='negative-remainder-chain',scales=scales)
def replay(s,cert):
    try:
        r=classify(s)
        return 'proved' if r is not None and r==cert else None
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,OverflowError):return None
def solve(s):
    try:r=classify(s)
    except (ValueError,OverflowError):r=None
    return dict(status='proved',certificate=r) if r is not None else dict(status='unknown')
def auto_discharge(g,limit=1):
    from deep_invention_dispatch import discharge
    return discharge(g,parse_statement,solve,replay,'root-structure-',limit)
