"""Projective box charts for homogeneous polynomial inequalities.

For x!=0 divide by max_i |x_i|, or max_i x_i on the nonnegative
orthant. Every normalized point is covered by one of the checked charts.
An even homogeneous polynomial on real space is invariant under x -> -x.
No finite sample or unchecked chart can close a proof.
"""
import json
from fractions import Fraction as Q
from affine import rational
from runtime import strict_json
from affine_chart_lab import decode_polynomial,encode_polynomial,substitute,constant,variable,scaled
from inequality_invention import add
from box_bernstein import search as box_search,replay as box_replay
from discovery import check,frontier,record,fingerprint

PREFIX='Homogeneous polynomial inequality: '

def normalize(s):
    if not isinstance(s,dict) or set(s)!={'dimension','degree','domain','terms'}:raise ValueError('claim shape')
    n=s['dimension'];d=s['degree']
    if type(n) is not int or not 1<=n<=16 or type(d) is not int or not 1<=d<=12 or s['domain'] not in ('real','nonnegative'):
        raise ValueError('claim bounds')
    q=decode_polynomial(s['terms'],n)
    if any(sum(e)!=d for e in q):raise ValueError('not homogeneous')
    return dict(dimension=n,degree=d,domain=s['domain'],terms=encode_polynomial(q))

def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))

def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('wrong statement type')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical statement')
    return s

def charts(s):
    signs=(1,-1) if s['domain']=='real' and s['degree']%2 else (1,)
    return [(i,sgn) for i in range(s['dimension']) for sgn in signs]

def chart_poly(s,i,sign):
    n=s['dimension'];d=n-1;q=decode_polynomial(s['terms'],n)
    if n==1:return {():sum(w*Q(sign)**e[0] for e,w in q.items())}
    im=[];j=0
    for k in range(n):
        if k==i:im.append(constant(d,sign));continue
        v=variable(d,j);j+=1
        if s['domain']=='real':v=add(scaled(v,2),constant(d,-1))
        im.append(v)
    return substitute(q,im,d)

def value(s,x):
    from math import prod
    q=decode_polynomial(s['terms'],s['dimension'])
    return sum((w*prod(v**k for v,k in zip(x,e)) for e,w in q.items()),Q(0))

def replay(s,cert):
    try:
        s=normalize(s);n=s['dimension']
        if not isinstance(cert,dict):return None
        if set(cert)=={'point'}:
            x=list(map(rational,cert['point']))
            if len(x)!=n or (s['domain']=='nonnegative' and any(v<0 for v in x)):return None
            return 'refuted' if value(s,x)<0 else None
        if set(cert)!={'charts'} or not isinstance(cert['charts'],list) or len(cert['charts'])!=len(charts(s)):
            return None
        for (i,sgn),row in zip(charts(s),cert['charts']):
            if not isinstance(row,list) or len(row)!=3 or type(row[0]) is not int or type(row[1]) is not int or row[:2]!=[i,sgn]:
                return None
            q=chart_poly(s,i,sgn)
            if n==1:
                if row[2] is not None or q.get((),0)<0:return None
            elif not box_replay(q,n-1,row[2]):return None
        return 'proved'
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,OverflowError):
        return None

def solve(s,depth=2):
    s=normalize(s);n=s['dimension']
    # Try sparse sign patterns and equal-coordinate witnesses first.
    from itertools import combinations,product
    signs=(1,-1) if s['domain']=='real' else (1,)
    count=0
    for k in range(1,min(n,3)+1):
        for ix in combinations(range(n),k):
            for ss in product(signs,repeat=k):
                if count>=128:break
                count+=1;x=[Q(0)]*n
                for i,v in zip(ix,ss):x[i]=Q(v)
                if value(s,x)<0:
                    cert={'point':[str(v) for v in x]}
                    if replay(s,cert)=='refuted':return dict(status='counterexample',certificate=cert,tested=count)
            if count>=128:break
        if count>=128:break
    rows=[]
    try:
        for i,sgn in charts(s):
            q=chart_poly(s,i,sgn)
            if n==1:
                if q.get((),0)<0:break
                rows.append([i,sgn,None]);continue
            r=box_search(q,n-1,depth)
            if r['status']!='proved':break
            rows.append([i,sgn,r['certificate']])
        cert={'charts':rows}
        if len(rows)==len(charts(s)) and len(json.dumps(cert))<=15000 and replay(s,cert)=='proved':
            return dict(status='proved',certificate=cert,tested=count)
    except (ValueError,OverflowError):pass
    return dict(status='unknown',tested=count,scope='bounded projective chart search')

def auto_discharge(g,limit=1):
    check(g);count=0
    for i in frontier(g):
        if count>=limit:break
        if i not in frontier(g):continue
        try:s=parse_statement(g['nodes'][i]['statement'])
        except (ValueError,TypeError):continue
        if any(o['focus']==i and oid.startswith('homogeneous-') for oid,o in g['observations'].items()):continue
        r=solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True)
        oid='homogeneous-'+fingerprint(i+'\n'+detail)[:32]
        ops=[dict(op='observe',id=oid,focus=i,kind={'proved':'proof_sketch','counterexample':'counterexample','unknown':'experiment'}[status],detail=detail)]
        if status!='unknown':
            ops.append(dict(op='review_claim',id=i,decision='established' if status=='proved' else 'refuted',evidence='Exact projective chart evidence '+oid))
        g=record(g,'falsify' if status=='counterexample' else 'reformulate',i,ops,trusted=True);count+=1
    return g
