"""Exact cancellation certificates for parameter-dependent linear inequalities.

For all integers n >= start, 0 <= t <= 1, and vectors x satisfying
rows*x >= 0 and equalities*x == 0, prove weights(n,t)*x >= 0.
The solver builds a finite prefix and a shifted-power/Bernstein tail.
Failure to find a certificate is unknown, not a proof of infeasibility.
"""
from fractions import Fraction as Q
from math import comb
from itertools import combinations, product
import json
import polynomial as p
from rational_cone import solve as cone
from runtime import strict_json

PREFIX = 'Parametric cone inequality: '
MAX_OFFSET = 16
MAX_DEPTH = 3
MAX_BYTES = 18000

def normalize(s):
    if not isinstance(s, dict) or set(s) != {'start','rows','equalities','weights'}:
        raise ValueError('parametric claim shape')
    if type(s['start']) is not int or not 0 <= s['start'] <= 10**6:
        raise ValueError('integer start')
    w = s['weights']
    if not isinstance(w,list) or not 1 <= len(w) <= 8:
        raise ValueError('vector dimension')
    def rows(raw):
        if not isinstance(raw,list) or len(raw)>12:
            raise ValueError('row limit')
        out=[]
        for r in raw:
            if not isinstance(r,list) or len(r)!=len(w):
                raise ValueError('row shape')
            out.append([str(p.rational(c)) for c in r])
        return out
    a,b=rows(s['rows']),rows(s['equalities'])
    if len(a)+2*len(b)>16: raise ValueError('cone size')
    return dict(start=s['start'],rows=a,equalities=b,
                weights=[p.encode(p.terms(q,2,8)) for q in w])

def statement(s):
    return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))

def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('not parametric cone')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical parametric cone')
    return s

def inputs(s):
    s=normalize(s)
    a=[tuple(map(Q,r)) for r in s['rows']]
    b=[tuple(map(Q,r)) for r in s['equalities']]
    return a,b,[p.terms(q,2,8) for q in s['weights']]

def generators(a,b):
    return a+b+[tuple(-v for v in r) for r in b]

def vectors(w,n0,tail,l,r):
    """Expand n=n0+u (tail) or n=n0 (slice), t=l+(r-l)v.
    Use ordinary powers in u>=0 and Bernstein basis in v in [0,1].
    Returns one vector for each coefficient in that product basis.
    """
    dn=max((i for q in w for i,j in q),default=0) if tail else 0
    dt=max((j for q in w for i,j in q),default=0)
    out=[]
    for a in range(dn+1):
        for b in range(dt+1):
            row=[]
            for q in w:
                c=Q(0)
                for (i,j),v in q.items():
                    if i<a:continue
                    f=comb(i,a)*Q(n0)**(i-a)
                    for k in range(min(j,b)+1):
                        c+=v*f*comb(j,k)*l**(j-k)*(r-l)**k*Q(comb(b,k),comb(dt,k))
                row.append(c)
            out.append(tuple(row))
    return out

def dot(a,b):return sum((x*y for x,y in zip(a,b)),Q(0))

def point_ok(a,b,w,start,cert):
    if set(cert)!={'kind','n','t','x'} or type(cert['n']) is not int or not start<=cert['n']<=10**12:return False
    t=p.rational(cert['t'])
    if not 0<=t<=1 or not isinstance(cert['x'],list) or len(cert['x'])!=len(w):return False
    x=list(map(p.rational,cert['x']))
    return (all(dot(r,x)>=0 for r in a) and all(dot(r,x)==0 for r in b)
            and dot([p.value(q,[Q(cert['n']),t]) for q in w],x)<0)

def replay(s,cert):
    try:
        s=normalize(s);a,b,w=inputs(s);g=generators(a,b);start=s['start']
        if not isinstance(cert,dict) or len(json.dumps(cert))>MAX_BYTES:return None
        if cert.get('kind')=='point':
            return 'refuted' if point_ok(a,b,w,start,cert) else None
        if set(cert)!={'kind','offset','prefix','tail'} or cert['kind']!='cone-cover':return None
        offset=cert['offset']
        if type(offset) is not int or not 0<=offset<=MAX_OFFSET or not isinstance(cert['prefix'],list) or len(cert['prefix'])!=offset:return None
        def visit(node,n,tail,l,r,depth):
            if depth>MAX_DEPTH or not isinstance(node,dict):return False
            if set(node)=={'split'}:
                pair=node['split']
                if not isinstance(pair,list) or len(pair)!=2:return False
                m=(l+r)/2
                return visit(pair[0],n,tail,l,m,depth+1) and visit(pair[1],n,tail,m,r,depth+1)
            if set(node)!={'weights'} or not isinstance(node['weights'],list):return False
            vv=vectors(w,n,tail,l,r)
            if len(node['weights'])!=len(vv):return False
            for v,raw in zip(vv,node['weights']):
                if not isinstance(raw,list) or len(raw)!=len(g):return False
                lam=list(map(p.rational,raw))
                if any(c<0 for c in lam):return False
                if any(sum((c*row[j] for c,row in zip(lam,g)),Q(0))!=v[j] for j in range(len(w))):return False
            return True
        if not visit(cert['tail'],start+offset,True,Q(0),Q(1),0):return None
        return 'proved' if all(visit(node,start+i,False,Q(0),Q(1),0) for i,node in enumerate(cert['prefix'])) else None
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,RecursionError,OverflowError):return None

def witness(a,b,w,start):
    # Sparse small rational vectors, no completeness guarantee.
    d=len(w);xs=[]
    for k in (1,2):
        for ids in combinations(range(d),k):
            for signs in product((-1,1),repeat=k):
                x=[0]*d
                for j,v in zip(ids,signs):x[j]=v
                if all(dot(r,x)>=0 for r in a) and all(dot(r,x)==0 for r in b):xs.append(x)
    for n in (start,start+1,start+2,start+8,start+16,start+64,start+1024):
        for t in (Q(0),Q(1,4),Q(1,2),Q(3,4),Q(1)):
            v=[p.value(q,[Q(n),t]) for q in w]
            for x in xs:
                if dot(v,x)<0:return dict(kind='point',n=n,t=str(t),x=x)
    return None

def solve(s):
    s=normalize(s);a,b,w=inputs(s);g=generators(a,b);start=s['start']
    cert=witness(a,b,w,start)
    if cert is not None and replay(s,cert)=='refuted':return dict(status='counterexample',certificate=cert)
    columns=[dict(enumerate(r)) for r in g];cache={};budget=640
    def cover(n,tail,l,r,depth):
        nonlocal budget
        weights=[]
        for v in vectors(w,n,tail,l,r):
            if v not in cache:
                if budget<=0:return None
                budget-=1
                lam,_=cone(columns,dict(enumerate(v)),pivot_budget=96)
                cache[v]=lam
            lam=cache[v]
            if lam is None:break
            weights.append([str(c) for c in lam])
        else:return dict(weights=weights)
        if depth>=MAX_DEPTH:return None
        m=(l+r)/2
        left=cover(n,tail,l,m,depth+1)
        if left is None:return None
        right=cover(n,tail,m,r,depth+1)
        return dict(split=[left,right]) if right is not None else None
    prefix=[]
    try:
        for offset in range(MAX_OFFSET+1):
            tail=cover(start+offset,True,Q(0),Q(1),0)
            if tail is not None:
                cert=dict(kind='cone-cover',offset=offset,prefix=prefix,tail=tail)
                if replay(s,cert)=='proved':return dict(status='proved',certificate=cert)
            if offset==MAX_OFFSET or budget<=0:break
            item=cover(start+offset,False,Q(0),Q(1),0)
            if item is None:break
            prefix.append(item)
    except (ValueError,OverflowError):pass
    return dict(status='unknown',scope='bounded exact cone search; finite prefix and unbounded integer tail not certified')

def auto_discharge(g,limit=1):
    from discovery import check,frontier,record,fingerprint
    check(g);count=0
    for focus in frontier(g):
        if count>=limit:break
        if focus not in frontier(g):continue
        try:s=parse_statement(g['nodes'][focus]['statement'])
        except (ValueError,TypeError):continue
        if any(o['focus']==focus and i.startswith('parametric-cone-') for i,o in g['observations'].items()):continue
        r=solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True)
        oid='parametric-cone-'+fingerprint(focus+'\n'+detail)[:32]
        if len(detail)>20000:continue
        ops=[dict(op='observe',id=oid,focus=focus,kind={'proved':'proof_sketch','counterexample':'counterexample','unknown':'experiment'}[status],detail=detail)]
        if status!='unknown':
            expected='proved' if status=='proved' else 'refuted'
            if replay(s,r['certificate'])!=expected:raise ArithmeticError('parametric cone replay failed')
            ops.append(dict(op='review_claim',id=focus,decision='established' if expected=='proved' else 'refuted',evidence='Exact parametric cone certificate '+oid))
        g=record(g,'falsify' if status=='counterexample' else 'forward',focus,ops,trusted=True);count+=1
    return g
