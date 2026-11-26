"""Exact beta-weighted integral inequalities for every integer index."""
import json
from fractions import Fraction as Q
from affine import rational
from runtime import strict_json
from integer_sign import classify
PREFIX='Beta integral sequence inequality: '
def normalize(s):
    if not isinstance(s,dict) or set(s)!={'left','right','polynomial','start'}:raise ValueError('claim')
    if type(s['start']) is not int or not 0<=s['start']<=10**6:raise ValueError('start')
    for k in ('left','right'):
        a=s[k]
        if not isinstance(a,list) or len(a)!=2 or any(type(v) is not int or not 0<=v<=10**6 for v in a):raise ValueError('nonnegative affine exponent')
    p=s['polynomial']
    if not isinstance(p,list) or not 1<=len(p)<=9:raise ValueError('polynomial degree')
    p=list(map(rational,p))
    while len(p)>1 and not p[-1]:p.pop()
    return dict(left=s['left'][:],right=s['right'][:],polynomial=list(map(str,p)),start=s['start'])
def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))
def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('not beta integral')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical beta integral')
    return s
def mul(a,b):
    out=[Q(0)]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):out[i+j]+=x*y
    return out
def numerator(s):
    s=normalize(s);a,b=s['left'],s['right'];p=list(map(Q,s['polynomial']));d=len(p)-1
    out=[Q(0)]*(d+1)
    for j,c in enumerate(p):
        t=[c]
        for k in range(j):t=mul(t,[Q(a[0]+1+k),Q(a[1])])
        for k in range(j,d):t=mul(t,[Q(a[0]+b[0]+2+k),Q(a[1]+b[1])])
        for k,v in enumerate(t):out[k]+=v
    return out
def replay(s,cert):
    try:
        s=normalize(s)
        if not isinstance(cert,dict) or set(cert)!={'kind','classification'} or cert['kind']!='beta-integer-sign':return None
        from integer_sign import replay as sign_replay
        return sign_replay([numerator(s)],[],s['start'],dict(kind='integer-sign',classification=cert['classification']))
    except (ValueError,TypeError,KeyError,ArithmeticError,OverflowError):return None
def solve(s):
    s=normalize(s)
    try:r=classify([numerator(s)],[],s['start'])
    except (ValueError,OverflowError):return dict(status='unknown')
    c=dict(kind='beta-integer-sign',classification=r)
    if replay(s,c)!=r['outcome']:raise ArithmeticError('beta replay')
    return dict(status='proved' if r['outcome']=='proved' else 'counterexample',certificate=c)
def auto_discharge(g,limit=1):
    from deep_invention_dispatch import discharge
    return discharge(g,parse_statement,solve,replay,'beta-integral-',limit)
