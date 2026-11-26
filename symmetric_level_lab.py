"""Certified few-level reduction for symmetric polynomials on a simplex.

A proof covers every multiplicity pattern up to the justified level bound.
Finite sampling or a proposed extremizer cannot certify coverage.
"""
import json
from fractions import Fraction as Q
from math import comb
from itertools import product
import polynomial as p
import simplex_discovery as sx
from runtime import strict_json
from moment_envelope_lab import interval_nonnegative

PREFIX='Symmetric simplex moment inequality: '
MAX_CHARTS=384
MAX_DEGREE=6

def normalize(s):
    if not isinstance(s,dict) or set(s)!={'dimension','terms'}:raise ValueError('claim shape')
    n=s['dimension']
    if type(n) is not int or not 1<=n<=64:raise ValueError('dimension')
    # Variables are power sums p2,p3,p4; p1=1 on the simplex.
    q=p.terms(s['terms'],3,MAX_DEGREE)
    if any(sum((i+2)*k for i,k in enumerate(e))>MAX_DEGREE for e in q):raise ValueError('weighted degree')
    return dict(dimension=n,terms=p.encode(q))

def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))

def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('not symmetric simplex')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical symmetric simplex')
    return s

def objective(s):
    return p.terms(normalize(s)['terms'],3,MAX_DEGREE)

def levels(s):
    q=objective(s);n=s['dimension']
    k=max((i+2 for e in q for i,v in enumerate(e) if v),default=1)
    if k==1:return 1
    # If dF/dp_k is a nonzero constant, the Lagrange polynomial for
    # positive coordinates has degree exactly k-1. Otherwise use the
    # moment-preserving secondary-extremum argument in the documentation.
    active=[(e,c) for e,c in q.items() if e[k-2]]
    linear= len(active)==1 and active[0][0][k-2]==1 and sum(active[0][0])==1
    return min(n,k-1 if linear else k)

def charts(s):
    s=normalize(s);n=s['dimension'];k=levels(s);out=[]
    def visit(prefix,remaining,low):
        if prefix:
            out.append(tuple(prefix))
            if len(out)>MAX_CHARTS:raise OverflowError('multiplicity coverage budget')
        if len(prefix)==k:return
        for m in range(low,remaining+1):visit(prefix+[m],remaining-m,m)
    visit([],n,1)
    return sorted(out,key=lambda a:(len(a),a))

def mul(a,b):
    out={}
    for e,c in a.items():
        for f,d in b.items():
            k=tuple(x+y for x,y in zip(e,f));out[k]=out.get(k,Q(0))+c*d
    out={e:v for e,v in out.items() if v}
    if len(out)>256 or any(sum(e)>MAX_DEGREE for e in out):raise OverflowError('chart expansion')
    return out

def chart_poly(s,counts):
    r=len(counts);out={}
    powers=[]
    for j in (2,3,4):
        powers.append({tuple(j if i==h else 0 for i in range(r)):Q(1,m**(j-1)) for h,m in enumerate(counts)})
    for e,c in objective(s).items():
        term={(0,)*r:c}
        for a,b in zip(e,powers):
            for _ in range(a):term=mul(term,b)
        for k,v in term.items():out[k]=out.get(k,Q(0))+v
    return {k:v for k,v in out.items() if v}

def binary(q):
    # y=(t,1-t) on a two-level simplex.
    out=[Q(0)]*(MAX_DEGREE+1)
    for (a,b),c in q.items():
        for j in range(b+1):out[a+j]+=c*comb(b,j)*(-1)**j
    return out

def simplex_spec(q,r):
    return sx.normalize(dict(variables=['y'+str(i) for i in range(r)],terms=p.encode(q)))

def point_value(s,x):
    return p.value(objective(s),[sum((v**j for v in x),Q(0)) for j in (2,3,4)])

def lift(n,counts,y):
    return [v/m for m,v in zip(counts,y) for _ in range(m)]+[Q(0)]*(n-sum(counts))

def replay(s,cert):
    try:
        s=normalize(s);n=s['dimension']
        if not isinstance(cert,dict) or len(json.dumps(cert))>18000:return None
        if set(cert)=={'kind','point'} and cert['kind']=='point':
            raw=cert['point']
            if not isinstance(raw,list) or len(raw)!=n:return None
            x=list(map(p.rational,raw))
            return 'refuted' if all(v>=0 for v in x) and sum(x)==1 and point_value(s,x)<0 else None
        if set(cert)!={'kind','charts'} or cert['kind']!='few-level-cover' or not isinstance(cert['charts'],list):return None
        expected=charts(s)
        if len(cert['charts'])!=len(expected):return None
        for counts,row in zip(expected,cert['charts']):
            if not isinstance(row,list) or len(row)!=2 or not isinstance(row[0],list) or any(type(v) is not int for v in row[0]) or row[0]!=list(counts):return None
            r=len(counts);q=chart_poly(s,counts);c=row[1]
            if r==1:
                if c!={'kind':'constant'} or sum(q.values())<0:return None
            elif r==2:
                if c!={'kind':'binary-sturm'} or not interval_nonnegative(binary(q)):return None
            else:
                if not isinstance(c,dict) or c.get('kind')!='simplex-cover' or sx.replay(simplex_spec(q,r),c)!='proved':return None
        return 'proved'
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,OverflowError,RecursionError):return None

def solve(s):
    s=normalize(s);n=s['dimension'];tested=0
    def point(counts,y):
        x=lift(n,counts,y)
        if point_value(s,x)>=0:return None
        cert=dict(kind='point',point=list(map(str,x)))
        if replay(s,cert)!='refuted':raise ArithmeticError('point lift replay failed')
        return dict(status='counterexample',certificate=cert,tested=tested)
    # Check sparse equal-coordinate points even if complete coverage exceeds budget.
    for m in range(1,n+1):
        r=point((m,),[Q(1)])
        if r:return r
    rows=[]
    try:
        expected=charts(s)
        for counts in expected:
            tested+=1;r=len(counts);q=chart_poly(s,counts)
            if r==1:c=dict(kind='constant')
            elif r==2:
                if not interval_nonnegative(binary(q)):
                    for den in (8,32,128):
                        for i in range(1,den):
                            t=Q(i,den);w=point(counts,[t,1-t])
                            if w:return w
                    return dict(status='unknown',tested=tested,scope='negative chart without bounded rational witness')
                c=dict(kind='binary-sturm')
            else:
                ans=sx.solve(simplex_spec(q,r),depth=2)
                if ans['status']=='counterexample':
                    w=point(counts,list(map(Q,ans['certificate']['point'])))
                    if w:return w
                    raise ArithmeticError('chart witness did not lift')
                if ans['status']!='proved':return dict(status='unknown',tested=tested,scope='unclosed simplex chart')
                c=ans['certificate']
            rows.append([list(counts),c])
        cert=dict(kind='few-level-cover',charts=rows)
        if replay(s,cert)=='proved':return dict(status='proved',certificate=cert,tested=tested,levels=levels(s))
    except (ValueError,OverflowError):pass
    return dict(status='unknown',tested=tested,scope='bounded multiplicity coverage or certificate budget')

def auto_discharge(g,limit=1):
    from discovery import check,frontier,record,fingerprint
    check(g);count=0
    for focus in frontier(g):
        if count>=limit:break
        if focus not in frontier(g):continue
        try:s=parse_statement(g['nodes'][focus]['statement'])
        except (ValueError,TypeError):continue
        if any(o['focus']==focus and i.startswith('symmetric-level-') for i,o in g['observations'].items()):continue
        r=solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True)
        oid='symmetric-level-'+fingerprint(focus+'\n'+detail)[:32]
        if len(detail)>20000:continue
        ops=[dict(op='observe',id=oid,focus=focus,kind={'proved':'proof_sketch','counterexample':'counterexample','unknown':'experiment'}[status],detail=detail)]
        if status!='unknown':
            expected='proved' if status=='proved' else 'refuted'
            if replay(s,r['certificate'])!=expected:raise ArithmeticError('symmetric level replay failed')
            ops.append(dict(op='review_claim',id=focus,decision='established' if expected=='proved' else 'refuted',evidence='Exact few-level coverage '+oid))
        g=record(g,'falsify' if status=='counterexample' else 'forward',focus,ops,trusted=True);count+=1
    return g

def main():
    import argparse
    from runtime import read_json
    q=argparse.ArgumentParser(description=__doc__);q.add_argument('spec');a=q.parse_args()
    print(json.dumps(solve(read_json(a.spec)),indent=2))
if __name__=='__main__':main()
