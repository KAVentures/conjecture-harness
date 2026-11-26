"""Exact three-moment charts, including a dimension-free simplex transfer.

The chart covers all first three moments of probability measures on [0,1].
The simplex transfer is one-way: size-biased empirical measures form a
subset, so a chart counterexample must not refute a simplex claim.
"""
from fractions import Fraction as Q
from itertools import product
import json
import polynomial as p
from runtime import strict_json
import box_bernstein as box

PREFIX='Moment chart polynomial inequality: '
N=3
MAX_DEGREE=6

def normalize(s):
    if not isinstance(s,dict) or set(s)!={'domain','terms'} or s['domain'] not in ('probability','simplex'):
        raise ValueError('moment chart shape')
    q=p.terms(s['terms'],3,MAX_DEGREE)
    if any(sum((i+1)*v for i,v in enumerate(e))>MAX_DEGREE for e in q):
        raise ValueError('weighted moment degree')
    return dict(domain=s['domain'],terms=p.encode(q))

def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))

def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('not moment chart')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical moment chart')
    return s

def constant(c):return {(0,0,0):Q(c)} if c else {}
def var(i):return {tuple(int(j==i) for j in range(3)):Q(1)}
def add(a,b):
    q=dict(a)
    for e,v in b.items():q[e]=q.get(e,Q(0))+v
    return {e:v for e,v in q.items() if v}
def neg(a):return {e:-v for e,v in a.items()}
def mul(a,b):
    q={}
    for e,c in a.items():
        for f,d in b.items():
            k=tuple(x+y for x,y in zip(e,f));q[k]=q.get(k,Q(0))+c*d
    q={e:v for e,v in q.items() if v}
    if len(q)>128 or any(sum(e)>12 for e in q):raise OverflowError('chart polynomial size')
    return q
def times(*args):
    q=constant(1)
    for a in args:q=mul(q,a)
    return q

def chart_images():
    a,b,c=map(var,range(3));one=constant(1)
    A=add(one,neg(a));B=add(one,neg(b))
    q=add(a,mul(A,b))
    # m2 = a*q; m3 = lower + c*width.
    return [a,mul(a,q),add(times(a,q,q),times(c,a,A,b,B))]

def chart_poly(s):
    s=normalize(s);images=chart_images();out={}
    for e,w in p.terms(s['terms'],3,MAX_DEGREE).items():
        q=constant(w)
        for k,img in zip(e,images):
            for _ in range(k):q=mul(q,img)
        out=add(out,q)
    if len(out)>128:raise OverflowError('chart polynomial size')
    return out

def chart_moments(a,b,c):
    q=a+(1-a)*b
    return [a,a*q,a*q*q+c*a*(1-a)*b*(1-b)]

def atomic(a,b,c):
    """Rational primal distribution for any chart point; exact at boundaries."""
    a,b,c=map(Q,(a,b,c))
    if any(not 0<=v<=1 for v in (a,b,c)):raise ValueError('chart point domain')
    if a in (0,1):return [(a,Q(1))]
    q=a+(1-a)*b;r=a*(1-b)
    lo=[(Q(0),1-a/q),(q,a/q)]
    hi=[(r,(1-a)/(1-r)),(Q(1),(a-r)/(1-r))]
    out={}
    for k,atoms in ((1-c,lo),(c,hi)):
        for x,w in atoms:out[x]=out.get(x,Q(0))+k*w
    return sorted((x,w) for x,w in out.items() if w)

def moments(atoms):
    return [sum((w*x**k for x,w in atoms),Q(0)) for k in (1,2,3)]

def objective(s,m):
    return p.value(p.terms(normalize(s)['terms'],3,MAX_DEGREE),m)

def replay(s,cert):
    try:
        s=normalize(s)
        if not isinstance(cert,dict) or len(json.dumps(cert))>15000:return None
        if set(cert)=={'kind','tree'} and cert['kind']=='moment-box-cover':
            return 'proved' if box.replay(chart_poly(s),3,cert['tree']) else None
        if set(cert)=={'kind','parameters'} and cert['kind']=='moment-point':
            if s['domain']!='probability' or not isinstance(cert['parameters'],list) or len(cert['parameters'])!=3:return None
            a,b,c=map(p.rational,cert['parameters'])
            atoms=atomic(a,b,c)
            if any(not 0<=x<=1 or w<=0 for x,w in atoms) or sum(w for x,w in atoms)!=1:return None
            m=moments(atoms)
            return 'refuted' if m==chart_moments(a,b,c) and objective(s,m)<0 else None
        if set(cert)=={'kind','point'} and cert['kind']=='simplex-point':
            if s['domain']!='simplex' or not isinstance(cert['point'],list) or not 1<=len(cert['point'])<=64:return None
            x=list(map(p.rational,cert['point']))
            if any(v<0 for v in x) or sum(x)!=1:return None
            m=moments([(v,v) for v in x if v])
            return 'refuted' if objective(s,m)<0 else None
        return None
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,OverflowError,RecursionError):return None

def solve(s):
    s=normalize(s)
    if s['domain']=='simplex':
        for n in range(1,65):
            cert=dict(kind='simplex-point',point=[str(Q(1,n))]*n)
            if replay(s,cert)=='refuted':return dict(status='counterexample',certificate=cert)
        for n in range(2,9):
            for t in (Q(1,4),Q(1,3),Q(1,2),Q(2,3),Q(3,4)):
                cert=dict(kind='simplex-point',point=[str(t)]+[str((1-t)/(n-1))]*(n-1))
                if replay(s,cert)=='refuted':return dict(status='counterexample',certificate=cert)
    else:
        for x in product((Q(0),Q(1,4),Q(1,2),Q(3,4),Q(1)),repeat=3):
            if objective(s,chart_moments(*x))<0:
                cert=dict(kind='moment-point',parameters=list(map(str,x)))
                if replay(s,cert)=='refuted':return dict(status='counterexample',certificate=cert)
    try:
        q=chart_poly(s);r=box.search(q,3,depth=4)
        if r['status']=='proved':
            cert=dict(kind='moment-box-cover',tree=r['certificate'])
            if replay(s,cert)=='proved':return dict(status='proved',certificate=cert)
    except (ValueError,OverflowError):pass
    return dict(status='unknown',scope='bounded box certificate search; simplex relaxation failure is not refutation')

def auto_discharge(g,limit=1):
    from discovery import check,frontier,record,fingerprint
    check(g);count=0
    for focus in frontier(g):
        if count>=limit:break
        if focus not in frontier(g):continue
        try:s=parse_statement(g['nodes'][focus]['statement'])
        except (ValueError,TypeError):continue
        if any(o['focus']==focus and i.startswith('moment-chart-') for i,o in g['observations'].items()):continue
        r=solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True)
        oid='moment-chart-'+fingerprint(focus+'\n'+detail)[:32]
        if len(detail)>20000:continue
        ops=[dict(op='observe',id=oid,focus=focus,kind={'proved':'proof_sketch','counterexample':'counterexample','unknown':'experiment'}[status],detail=detail)]
        if status!='unknown':
            expected='proved' if status=='proved' else 'refuted'
            if replay(s,r['certificate'])!=expected:raise ArithmeticError('moment chart replay failed')
            ops.append(dict(op='review_claim',id=focus,decision='established' if expected=='proved' else 'refuted',evidence='Exact moment chart certificate '+oid))
        g=record(g,'falsify' if status=='counterexample' else 'forward',focus,ops,trusted=True);count+=1
    return g

def main():
    import argparse
    from runtime import read_json
    q=argparse.ArgumentParser(description=__doc__);q.add_argument('spec');a=q.parse_args()
    print(json.dumps(solve(read_json(a.spec)),indent=2))
if __name__=='__main__':main()
