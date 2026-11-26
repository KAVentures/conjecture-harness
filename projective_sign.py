"""Reduce homogeneous binary semialgebraic implications to exact sign cells.

Each polynomial may have a different homogeneous degree. The two real
projective charts are oriented (y>0 and y<0); the axis y=0 is checked
separately. The orthant needs only the positive chart.
"""
from fractions import Fraction as Q
from math import comb
from sign_cells import classify as cells, value

def homogeneous(raw):
    if not isinstance(raw,dict) or len(raw)>64:raise ValueError('binary polynomial shape')
    p={}
    for e,c in raw.items():
        if not isinstance(e,tuple) or len(e)!=2 or any(type(k) is not int or k<0 for k in e) or sum(e)>8 or type(c) not in (int,Q):raise ValueError('binary term shape')
        if c:p[e]=Q(c)
    degrees={sum(e) for e in p}
    if len(degrees)>1:raise ValueError('not homogeneous')
    return p,next(iter(degrees),0)

def valid_relations(raw,relations,domain):
    if not isinstance(raw,(list,tuple)) or not 1<=len(raw)<=9 or not isinstance(relations,(list,tuple)) or len(relations)!=len(raw)-1 or any(r not in ('zero','nonnegative') for r in relations) or domain not in ('real','nonnegative'):raise ValueError('implication shape')

def sign(x):return (x>0)-(x<0)
def fails(signs,relations):return signs[-1]<0 and all(s==0 if r=='zero' else s>=0 for r,s in zip(relations,signs))

def binary(raw,relations,domain):
    valid_relations(raw,relations,domain)
    polys=[homogeneous(p) for p in raw]
    for x in ([0,1,-1] if domain=='real' else [0,1]):
        signs=[sign(sum(c*Q(x)**a for (a,b),c in p.items() if not b)) for p,d in polys]
        if fails(signs,relations):return dict(outcome='refuted',witness=dict(kind='axis',point=[str(x),'0'],signs=signs))
    reports=[]
    for orientation in ([1,-1] if domain=='real' else [1]):
        dense=[]
        for p,d in polys:
            # (x,y) = |y|*(t,orientation), so each homogeneous factor
            # |y|^d is positive. Coefficients retain the sign of y^b.
            q=[Q(0)]*(d+1)
            for (a,b),c in p.items():q[a]+=c*orientation**b
            dense.append(q)
        r=cells(dense,relations,domain)
        if r['outcome']=='refuted':return dict(outcome='refuted',witness=dict(kind='chart',orientation=orientation,classification=r))
        reports.append(dict(orientation=orientation,classification=r))
    return dict(outcome='proved',charts=reports,axis_checked=True)

def simplex(raw):
    if not isinstance(raw,dict) or len(raw)>64:raise ValueError('binary polynomial shape')
    q=[Q(0)]*9
    for e,c in raw.items():
        if not isinstance(e,tuple) or len(e)!=2 or any(type(k) is not int or k<0 for k in e) or sum(e)>8 or type(c) not in (int,Q):raise ValueError('binary term shape')
        a,b=e
        for k in range(b+1):q[a+k]+=Q(c)*comb(b,k)*(-1)**k
    # x=t,y=1-t; nonnegative t and 1-t exactly define the segment.
    return cells([[Q(1),Q(-1)],q],['nonnegative'],'nonnegative')

def replay_binary(raw,relations,domain,cert):
    try:
        if not isinstance(cert,dict) or set(cert)!={'kind','classification'} or cert['kind']!='projective-sign':return None
        r=binary(raw,relations,domain)
        return r['outcome'] if cert['classification']==r else None
    except (ValueError,TypeError,KeyError,ArithmeticError):return None

def replay_simplex(raw,cert):
    try:
        if not isinstance(cert,dict) or set(cert)!={'kind','classification'} or cert['kind']!='segment-sign':return None
        r=simplex(raw)
        return r['outcome'] if cert['classification']==r else None
    except (ValueError,TypeError,KeyError,ArithmeticError):return None
