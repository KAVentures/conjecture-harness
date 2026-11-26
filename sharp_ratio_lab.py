"""Sharp rational linear bounds on cones, retaining signed cancellations."""
import json
from fractions import Fraction as Q
from itertools import combinations
from affine import rational
from runtime import strict_json
from rational_cone import solve as cone
PREFIX='Sharp cone ratio inequality: '

def normalize(s):
    if not isinstance(s,dict) or set(s)!={'rows','equalities','numerator','denominator','bound'}:raise ValueError('claim')
    n=len(s['numerator']) if isinstance(s['numerator'],list) else 0
    if not 1<=n<=8:raise ValueError('dimension')
    def row(x):
        if not isinstance(x,list) or len(x)!=n:raise ValueError('row')
        return list(map(lambda v:str(rational(v)),x))
    def rows(x):
        if not isinstance(x,list) or len(x)>12:raise ValueError('rows')
        return list(map(row,x))
    a,b=rows(s['rows']),rows(s['equalities'])
    if len(a)+2*len(b)>16:raise ValueError('generator count')
    d=row(s['denominator'])
    if not any(map(Q,d)):raise ValueError('zero denominator')
    return dict(rows=a,equalities=b,numerator=row(s['numerator']),denominator=d,bound=str(rational(s['bound'])))
def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))
def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('not ratio')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical ratio')
    return s
def data(s):
    s=normalize(s);a,b=[[tuple(map(Q,r)) for r in s[k]] for k in ('rows','equalities')]
    return a,b,a+b+[tuple(-v for v in r) for r in b],tuple(map(Q,s['numerator'])),tuple(map(Q,s['denominator'])),Q(s['bound'])
def dot(a,b):return sum((x*y for x,y in zip(a,b)),Q(0))
def certificate(s):
    _,_,g,f,d,k=data(s);t=[x-k*y for x,y in zip(f,d)]
    try:w,_=cone([dict(enumerate(r)) for r in g],dict(enumerate(t)),pivot_budget=160)
    except ValueError:return None
    return dict(kind='dual',weights=list(map(str,w))) if w is not None else None
def feasible(s,objective,upper=False):
    a,b,_,f,d,_=data(s);n=len(f)
    # x=x+ - x-, cone rows receive nonnegative slack. Normalize d*x=1.
    rows=[d,f,*a,*b];target={0:Q(1),1:Q(objective)}
    cols=[{i:sign*r[j] for i,r in enumerate(rows)} for sign in (1,-1) for j in range(n)]
    cols.extend({i+2:Q(-1)} for i in range(len(a)))
    if upper:cols.append({1:Q(1)})
    try:w,_=cone(cols,target,pivot_budget=160)
    except ValueError:return None
    if w is None:return None
    return [str(w[i]-w[n+i]) for i in range(n)]
def primal(s,raw):
    a,b,_,f,d,_=data(s)
    if not isinstance(raw,list) or len(raw)!=len(f):raise ValueError('point')
    x=list(map(rational,raw))
    if any(dot(r,x)<0 for r in a) or any(dot(r,x)!=0 for r in b) or dot(d,x)!=1:raise ValueError('infeasible point')
    return dot(f,x)
def replay(s,cert):
    try:
        a,b,g,f,d,k=data(s)
        if not isinstance(cert,dict) or len(json.dumps(cert))>12000:return None
        if set(cert)=={'kind','point'} and cert['kind']=='point':
            return 'refuted' if primal(s,cert['point'])<k else None
        if set(cert)!={'kind','weights'} or cert['kind']!='dual' or not isinstance(cert['weights'],list) or len(cert['weights'])!=len(g):return None
        w=list(map(rational,cert['weights']))
        if any(v<0 for v in w):return None
        return 'proved' if all(sum(v*r[i] for v,r in zip(w,g))==f[i]-k*d[i] for i in range(len(f))) else None
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError):return None
def sharp(s,cert,point):
    try:return replay(s,cert)=='proved' and primal(s,point)==Q(normalize(s)['bound'])
    except (ValueError,TypeError,KeyError,ArithmeticError):return False
def solve(s):
    s=normalize(s);c=certificate(s)
    if c is not None and replay(s,c)=='proved':
        out=dict(status='proved',certificate=c);x=feasible(s,Q(s['bound']))
        if x is not None and sharp(s,c,x):out['attainment']=x
        return out
    for k in (0,4,8,16):
        x=feasible(s,Q(s['bound'])-Q(1,2**k),upper=True)
        if x is not None:
            c=dict(kind='point',point=x)
            if replay(s,c)=='refuted':return dict(status='counterexample',certificate=c)
    return dict(status='unknown')
def coordinates(columns,f):
    # Solve an overdetermined system with independent selected columns.
    m=len(columns);rows=[[v[i] for v in columns]+[f[i]] for i in range(len(f))]
    for j in range(m):
        k=next((k for k in range(j,len(rows)) if rows[k][j]),None)
        if k is None:return None
        rows[j],rows[k]=rows[k],rows[j];v=rows[j][j];rows[j]=[x/v for x in rows[j]]
        for k,r in enumerate(rows):
            if k!=j:
                v=r[j];rows[k]=[x-v*y for x,y in zip(r,rows[j])]
    if any(r[-1] for r in rows[m:]):return None
    return [r[-1] for r in rows[:m]]
def discover(s,budget=512):
    s=normalize(s);_,_,g,f,d,_=data(s);n=len(f);best=None;tested=0
    if type(budget) is not int or not 1<=budget<=4096:raise ValueError('budget')
    # Enumerate small dual bases containing the unrestricted bound column d.
    for k in range(min(n-1,len(g))+1):
        for ids in combinations(range(len(g)),k):
            if tested>=budget:break
            tested+=1;z=coordinates([d]+[g[i] for i in ids],f)
            if z is None or any(v<0 for v in z[1:]) or (best and z[0]<=best[0]):continue
            w=[Q(0)]*len(g)
            for i,v in zip(ids,z[1:]):w[i]=v
            spec=dict(s,bound=str(z[0]));cert=dict(kind='dual',weights=list(map(str,w)))
            if replay(spec,cert)!='proved':continue
            best=(z[0],cert)
            x=feasible(spec,z[0])
            if x is not None and sharp(spec,cert,x):return dict(status='sharp',bound=str(z[0]),certificate=cert,attainment=x,tested=tested)
        if tested>=budget:break
    return dict(status='lower-bound',bound=str(best[0]),certificate=best[1],tested=tested) if best else dict(status='unknown',tested=tested)
def auto_discharge(g,limit=1):
    from deep_invention_dispatch import discharge
    return discharge(g,parse_statement,solve,replay,'sharp-ratio-',limit)
