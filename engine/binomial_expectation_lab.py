"""Symbolic binomial expectations via factorial moments, all integer n."""
from fractions import Fraction as Q
import json
import polynomial as p
import parametric_cone_lab as pc
from runtime import strict_json
PREFIX='Binomial expectation inequality: '
def normalize(s):
    if not isinstance(s,dict) or set(s)!={'start','terms'}:raise ValueError('claim')
    if type(s['start']) is not int or not 0<=s['start']<=10**6:raise ValueError('start')
    return dict(start=s['start'],terms=p.encode(p.terms(s['terms'],2,4)))
def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))
def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('not binomial expectation')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical expectation')
    return s
def stirling(k,j):
    # S(k,j) from k^m=sum_j S(m,j)*(k)_j.
    row=[1]
    for _ in range(k):
        row=[(i*row[i] if i<len(row) else 0)+(row[i-1] if i else 0) for i in range(len(row)+1)]
    return row[j] if j<len(row) else 0
def falling(j):
    a=[Q(1)]
    for k in range(j):
        b=[Q(0)]*(len(a)+1)
        for i,v in enumerate(a):b[i]-=k*v;b[i+1]+=v
        a=b
    return a
def transformed(s):
    s=normalize(s);out={}
    for (a,k),v in p.terms(s['terms'],2,4).items():
        for j in range(k+1):
            c=v*stirling(k,j)
            for i,z in enumerate(falling(j)):
                e=(a+i,j);out[e]=out.get(e,Q(0))+c*z
    return {e:v for e,v in out.items() if v}
def target(s):return dict(start=s['start'],rows=[[1]],equalities=[],weights=[p.encode(transformed(s))])
def replay(s,cert):
    try:
        s=normalize(s)
        if not isinstance(cert,dict) or set(cert)!={'kind','inner'} or cert['kind']!='factorial-moment':return None
        return pc.replay(target(s),cert['inner'])
    except (ValueError,TypeError,KeyError,ArithmeticError,OverflowError):return None
def solve(s):
    s=normalize(s);r=pc.solve(target(s))
    if r['status']=='unknown':return r
    cert=dict(kind='factorial-moment',inner=r['certificate'])
    expected='proved' if r['status']=='proved' else 'refuted'
    if replay(s,cert)!=expected:raise ArithmeticError('factorial moment replay')
    return dict(status=r['status'],certificate=cert)
def auto_discharge(g,limit=1):
    from deep_invention_dispatch import discharge
    return discharge(g,parse_statement,solve,replay,'binomial-expectation-',limit)
