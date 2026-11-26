"""Dimension-free sharp polynomial moment bounds on [0,1].

A dual polynomial envelope is checked by exact projective Sturm sign.
An atomic primal witness is checked directly. Search is incomplete.
"""
from fractions import Fraction as Q
from math import comb
import json
import polynomial as p
from rational_cone import solve as cone
from runtime import strict_json
from univariate_sign import classify

PREFIX='Moment envelope inequality: '
DEGREE=8

def normalize(s):
    if not isinstance(s,dict) or set(s)!={'assumptions','objective','bound'}:raise ValueError('moment claim shape')
    if not isinstance(s['assumptions'],list) or len(s['assumptions'])>6:raise ValueError('moment assumption limit')
    def poly(t):return p.encode(p.terms(t,1,DEGREE))
    a=[]
    for h in s['assumptions']:
        if not isinstance(h,dict) or set(h)!={'relation','terms'} or h['relation'] not in ('zero','nonnegative'):raise ValueError('moment assumption')
        a.append(dict(relation=h['relation'],terms=poly(h['terms'])))
    return dict(assumptions=a,objective=poly(s['objective']),bound=str(p.rational(s['bound'])))

def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))

def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('not moment envelope')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical moment envelope')
    return s

def dense(raw):
    q=p.terms(raw,1,DEGREE)
    return [q.get((i,),Q(0)) for i in range(DEGREE+1)]

def inputs(s):
    s=normalize(s)
    return [dense(h['terms']) for h in s['assumptions']],[h['relation'] for h in s['assumptions']],dense(s['objective']),Q(s['bound'])

def value(q,x):return sum((a*x**i for i,a in enumerate(q)),Q(0))

def product(a,b):
    if len(a)+len(b)-2>DEGREE:raise ValueError('degree limit')
    q=[Q(0)]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):q[i+j]+=x*y
    return q

def interval_nonnegative(q):
    # x=u/(1+u) covers [0,1); continuity includes 1.
    d=max((i for i,v in enumerate(q) if v),default=0)
    transformed=[Q(0)]*(d+1)
    for i in range(d+1):
        for j in range(d-i+1):transformed[i+j]+=q[i]*comb(d-i,j)
    return classify(transformed,'nonnegative')['outcome']=='proved'

def residual(s,raw):
    a,relations,f,b=inputs(s)
    if not isinstance(raw,list) or len(raw)!=len(a):raise ValueError('multiplier count')
    lam=list(map(p.rational,raw))
    if any(v<0 for v,r in zip(lam,relations) if r=='nonnegative'):raise ValueError('multiplier sign')
    q=f[:];q[0]-=b
    for v,h in zip(lam,a):
        q=[c-v*z for c,z in zip(q,h)]
    return q

def atomic_value(s,atoms):
    a,relations,f,b=inputs(s)
    if not isinstance(atoms,list) or not 1<=len(atoms)<=24:raise ValueError('atom count')
    xs=[]
    for pair in atoms:
        if not isinstance(pair,list) or len(pair)!=2:raise ValueError('atom shape')
        x,w=map(p.rational,pair)
        if not 0<=x<=1 or w<=0:raise ValueError('atom domain')
        xs.append((x,w))
    if sum(w for x,w in xs)!=1:raise ValueError('mass')
    for h,r in zip(a,relations):
        v=sum(w*value(h,x) for x,w in xs)
        if (r=='zero' and v!=0) or (r=='nonnegative' and v<0):raise ValueError('moment constraint')
    return sum((w*value(f,x) for x,w in xs),Q(0))

def replay(s,cert):
    try:
        s=normalize(s)
        if not isinstance(cert,dict) or len(json.dumps(cert))>15000:return None
        if set(cert)=={'kind','atoms'} and cert['kind']=='point':
            return 'refuted' if atomic_value(s,cert['atoms'])<Q(s['bound']) else None
        if set(cert)!={'kind','multipliers'} or cert['kind']!='envelope':return None
        return 'proved' if interval_nonnegative(residual(s,cert['multipliers'])) else None
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,OverflowError,RecursionError):return None

def roots(a):
    # Linear moment constraints suggest candidate means/contact points.
    r=[]
    for h in a:
        if h[1] and not any(h[2:]):
            x=-h[0]/h[1]
            if 0<x<1 and x not in r:r.append(x)
    for x in (Q(1,2),Q(1,3),Q(2,3),Q(1,4),Q(3,4)):
        if x not in r:r.append(x)
    return r[:8]

def basis(a):
    # Positive x^i(1-x)^j and (x-r)^2 times those factors.
    # Retain low degrees, allowing exact vanishing at suggested contact points.
    def bern(i,j):return [Q(0)]*i+[Q((-1)**k*comb(j,k)) for k in range(j+1)]
    out=[bern(i,d-i) for d in range(DEGREE+1) for i in range(d+1)]
    for x in roots(a):
        sq=[x*x,-2*x,Q(1)]
        out.extend(product(sq,bern(i,d-i)) for d in range(4) for i in range(d+1))
    # Products of two squares expose distinct interior contact points.
    rr=roots(a)
    for i,x in enumerate(rr):
        for y in rr[i+1:]:
            q=product([x*x,-2*x,Q(1)],[y*y,-2*y,Q(1)])
            out.extend((q,product(q,[Q(0),Q(1)]),product(q,[Q(1),Q(-1)])))
    unique={}
    for q in out:unique.setdefault(tuple(q),q)
    return list(unique.values())[:220]

def dual(s):
    a,relations,f,b=inputs(s);cols=[];owners=[]
    for i,(h,r) in enumerate(zip(a,relations)):
        cols.append(dict(enumerate(h)));owners.append((i,1))
        if r=='zero':cols.append(dict(enumerate(-v for v in h)));owners.append((i,-1))
    cols.extend(dict(enumerate(q)) for q in basis(a))
    f=f[:];f[0]-=b
    try:lam,_=cone(cols,dict(enumerate(f)),pivot_budget=160)
    except (ValueError,OverflowError):return None
    if lam is None:return None
    multipliers=[Q(0)]*len(a)
    for v,(i,sign) in zip(lam,owners):multipliers[i]+=v*sign
    cert=dict(kind='envelope',multipliers=list(map(str,multipliers)))
    return cert if replay(s,cert)=='proved' else None

def atomic(s,threshold=None):
    """Grid-restricted exact primal feasibility, not a global optimization proof."""
    a,relations,f,b=inputs(s)
    grid=sorted(set([Q(i,8) for i in range(9)]+roots(a)))
    target={0:Q(1)}
    size=1+len(a)+(threshold is not None)
    if threshold is not None:target[size-1]=threshold
    cols=[]
    for x in grid:
        c={0:Q(1),**{i+1:value(h,x) for i,h in enumerate(a)}}
        if threshold is not None:c[size-1]=value(f,x)
        cols.append(c)
    for i,r in enumerate(relations):
        if r=='nonnegative':cols.append({i+1:Q(-1)})
    if threshold is not None:cols.append({size-1:Q(1)})
    try:lam,_=cone(cols,target,pivot_budget=128)
    except (ValueError,OverflowError):return None
    if lam is None:return None
    atoms=[[str(x),str(w)] for x,w in zip(grid,lam) if w]
    try:
        v=atomic_value(s,atoms)
        return atoms if threshold is None or v<=threshold else None
    except ValueError:return None

def sharpness(s,cert,atoms):
    """Exact attainment plus equality conditions; no assumed uniqueness."""
    if replay(s,cert)!='proved':return None
    try:
        if atomic_value(s,atoms)!=Q(normalize(s)['bound']):return None
        a,relations,_,_=inputs(s)
        lam=list(map(p.rational,cert['multipliers']))
        q=residual(s,cert['multipliers'])
        return dict(bound=normalize(s)['bound'],atoms=atoms,
                    contact_polynomial=p.encode({(i,):v for i,v in enumerate(q) if v}),
                    active_inequalities=[i for i,(v,r) in enumerate(zip(lam,relations)) if v>0 and r=='nonnegative'])
    except (ValueError,TypeError,KeyError,ArithmeticError):return None

def solve(s):
    s=normalize(s);cert=dual(s)
    if cert is not None:
        result=dict(status='proved',certificate=cert)
        atoms=atomic(s,Q(s['bound']))
        if atoms:
            q=sharpness(s,cert,atoms)
            if q is not None:result['sharpness']=q
        return result
    for k in (0,4,8,12,16):
        atoms=atomic(s,Q(s['bound'])-Q(1,2**k))
        if atoms:
            cert=dict(kind='point',atoms=atoms)
            if replay(s,cert)=='refuted':return dict(status='counterexample',certificate=cert)
    return dict(status='unknown',scope='bounded envelope and atomic search')

def discover_bounds(s,steps=6):
    """Find a certified lower and feasible upper bound; label sharp only by replay."""
    s=normalize(s)
    if type(steps) is not int or not 0<=steps<=12:raise ValueError('step limit')
    _,_,f,_=inputs(s)
    lo=-sum(abs(v) for v in f)
    low_spec=dict(s,bound=str(lo));low_cert=dual(low_spec)
    atoms=atomic(s)
    if low_cert is None or atoms is None:return dict(status='unknown')
    hi=atomic_value(s,atoms)
    # Contact points suggested by linear moment constraints often give exact
    # extremizers. Test them before bisection, rather than hoping the grid LP
    # happens to select an attaining distribution.
    a,_,_,_=inputs(s)
    for x in [Q(0),Q(1),*roots(a)]:
        candidate=[[str(x),'1']]
        try:v=atomic_value(s,candidate)
        except ValueError:continue
        if v<hi:atoms,hi=candidate,v
    for _ in range(steps+1):
        high_spec=dict(s,bound=str(hi));cert=dual(high_spec)
        if cert is not None:
            exact=sharpness(high_spec,cert,atoms)
            if exact is not None:return dict(status='sharp',lower=str(hi),upper=str(hi),certificate=cert,sharpness=exact)
        if hi==lo:break
        mid=(lo+hi)/2
        cert=dual(dict(s,bound=str(mid)))
        if cert is not None:lo,low_cert=mid,cert;continue
        w=atomic(s,mid)
        if w is None:break
        atoms=w;hi=atomic_value(s,atoms)
    return dict(status='bracket',lower=str(lo),upper=str(hi),certificate=low_cert,atoms=atoms)

def auto_discharge(g,limit=1):
    from discovery import check,frontier,record,fingerprint
    check(g);count=0
    for focus in frontier(g):
        if count>=limit:break
        if focus not in frontier(g):continue
        try:s=parse_statement(g['nodes'][focus]['statement'])
        except (ValueError,TypeError):continue
        if any(o['focus']==focus and i.startswith('moment-envelope-') for i,o in g['observations'].items()):continue
        r=solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True)
        oid='moment-envelope-'+fingerprint(focus+'\n'+detail)[:32]
        if len(detail)>20000:continue
        ops=[dict(op='observe',id=oid,focus=focus,kind={'proved':'proof_sketch','counterexample':'counterexample','unknown':'experiment'}[status],detail=detail)]
        if status!='unknown':
            expected='proved' if status=='proved' else 'refuted'
            if replay(s,r['certificate'])!=expected:raise ArithmeticError('moment envelope replay failed')
            ops.append(dict(op='review_claim',id=focus,decision='established' if expected=='proved' else 'refuted',evidence='Exact moment envelope '+oid))
        g=record(g,'falsify' if status=='counterexample' else 'forward',focus,ops,trusted=True);count+=1
    return g

def main():
    import argparse
    from runtime import read_json
    q=argparse.ArgumentParser(description=__doc__);q.add_argument('spec');q.add_argument('--discover',action='store_true');args=q.parse_args()
    s=read_json(args.spec)
    print(json.dumps(discover_bounds(s) if args.discover else solve(s),indent=2))
if __name__=='__main__':main()
