"""Coefficientwise induction for polynomial transfer matrices.

For X_{n+1}(z)=M(z)X_n(z), prove every coefficient of G(z)X_n(z)
nonnegative for all n>=0. A finite polynomial invariant cone is replayed
symbolically, not by bounding the output degree or iterating finitely.
"""
from fractions import Fraction as Q
import json
from itertools import combinations
from affine import rational
from runtime import strict_json
from rational_cone import solve as cone
PREFIX='Polynomial transfer induction inequality: '
MAX_ROWS=16
MAX_D=6
MAX_INPUT=5
def clean(a):
    a=list(a)
    while a and not a[-1]:a.pop()
    if len(a)>32 or any(v.numerator.bit_length()>1024 or v.denominator.bit_length()>1024 for v in a):raise ValueError('polynomial growth')
    return tuple(a)
def add(a,b):
    return clean([(a[i] if i<len(a) else Q(0))+(b[i] if i<len(b) else Q(0)) for i in range(max(len(a),len(b)))])
def mul(a,b):
    if not a or not b:return ()
    out=[Q(0)]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):out[i+j]+=x*y
    return clean(out)
def scale(a,w):return clean([w*v for v in a])
def shift(a,k):return clean([Q(0)]*k+list(a)) if a else ()
def readpoly(a,limit=MAX_INPUT):
    if not isinstance(a,list) or len(a)>limit:raise ValueError('polynomial size')
    return clean(list(map(rational,a)))
def encode(a):return list(map(str,a))
def normalize(s):
    if not isinstance(s,dict) or set(s)!={'matrix','initial','goal'}:raise ValueError('claim')
    x=s['initial'];g=s['goal'];M=s['matrix']
    if not isinstance(x,list) or not 1<=len(x)<=MAX_D:raise ValueError('state dimension')
    n=len(x)
    if not isinstance(g,list) or len(g)!=n or not isinstance(M,list) or len(M)!=n or any(not isinstance(r,list) or len(r)!=n for r in M):raise ValueError('matrix dimensions')
    return dict(matrix=[[encode(readpoly(v)) for v in row] for row in M],initial=[encode(readpoly(v)) for v in x],goal=[encode(readpoly(v)) for v in g])
def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))
def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('not transfer induction')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical transfer')
    return s
def data(s):
    s=normalize(s);return [[readpoly(v) for v in row] for row in s['matrix']],[readpoly(v) for v in s['initial']],[readpoly(v) for v in s['goal']]
def dot(a,b):
    q=()
    for x,y in zip(a,b):q=add(q,mul(x,y))
    return q
def pull(r,M):return [dot(r,[M[i][j] for i in range(len(r))]) for j in range(len(r))]
def nonneg(q):return all(v>=0 for v in q)
def sparse(row):return {(i,j):v for i,a in enumerate(row) for j,v in enumerate(a) if v}
def step(M,x):return [dot(r,x) for r in M]
def orbit(M,x,n):
    if type(n) is not int or not 0<=n<=12:raise ValueError('orbit limit')
    for _ in range(n):x=step(M,x)
    return x
def replay(s,cert):
    try:
        M,x,g=data(s);n=len(x)
        if not isinstance(cert,dict) or len(json.dumps(cert))>18000:return None
        if set(cert)=={'index','degree'}:
            k=cert['degree']
            if type(k) is not int or k<0:return None
            q=dot(g,orbit(M,x,cert['index']))
            return 'refuted' if k<len(q) and q[k]<0 else None
        if set(cert)!={'rows','steps'} or not isinstance(cert['rows'],list) or not 1<=len(cert['rows'])<=MAX_ROWS or not isinstance(cert['steps'],list) or len(cert['steps'])!=len(cert['rows']):return None
        rows=[]
        for r in cert['rows']:
            if not isinstance(r,list) or len(r)!=n:return None
            rows.append([readpoly(v,9) for v in r])
        if rows[0]!=g or any(not nonneg(dot(r,x)) for r in rows):return None
        for r,terms in zip(rows,cert['steps']):
            if not isinstance(terms,list) or len(terms)>128:return None
            q=[()]*n
            for row in terms:
                if not isinstance(row,list) or len(row)!=3:return None
                i,k,w=row
                if type(i) is not int or not 0<=i<len(rows) or type(k) is not int or not 0<=k<=8:return None
                w=rational(w)
                if w<0:return None
                q=[add(a,scale(shift(b,k),w)) for a,b in zip(q,rows[i])]
            if q!=pull(r,M):return None
        return 'proved'
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,OverflowError,RecursionError):return None
def solve(s):
    M,x,g=data(s);n=len(x);y=x
    # Finite prefix only searches for genuine negative coefficient witnesses.
    try:
        for i in range(7):
            q=dot(g,y);k=next((k for k,v in enumerate(q) if v<0),None)
            if k is not None:
                c=dict(index=i,degree=k)
                if replay(s,c)=='refuted':return dict(status='counterexample',certificate=c)
            y=step(M,y)
    except ValueError:pass
    rows=[g]
    E=[[(Q(1),) if i==j else () for j in range(n)] for i in range(n)]
    def include(r):
        if len(rows)<MAX_ROWS and r not in rows and any(r) and max(map(len,r))<=9 and nonneg(dot(r,x)):rows.append(r)
    try:
        for r in E:include(r)
        # Discover both scaled coordinate and shifted coefficient inequalities.
        for i,j in combinations(range(n),2):
            for a,b in ((i,j),(j,i)):
                for k in (0,1,2):
                    for w in (Q(1),Q(2),Q(1,2)):
                        include([add(u,scale(shift(v,k),-w)) for u,v in zip(E[a],E[b])])
        r=g
        for _ in range(3):
            r=pull(r,M);include(r)
        for _ in range(MAX_ROWS):
            cols=[];keys=[]
            for i,r in enumerate(rows):
                for k in range(5):
                    cols.append(sparse([shift(v,k) for v in r]));keys.append((i,k))
            keep=[];steps=[]
            for i,r in enumerate(rows):
                try:w,_=cone(cols,sparse(pull(r,M)),pivot_budget=128)
                except ValueError:w=None
                if w is not None:
                    keep.append(i);steps.append([[j,k,str(v)] for (j,k),v in zip(keys,w) if v])
            if 0 not in keep:break
            if len(keep)==len(rows):
                c=dict(rows=[[encode(v) for v in r] for r in rows],steps=steps)
                if replay(s,c)=='proved':return dict(status='proved',certificate=c)
                break
            rows=[rows[i] for i in keep]
    except (ValueError,OverflowError):pass
    return dict(status='unknown',scope='bounded polynomial invariant discovery, arbitrary iteration and output degree')
def auto_discharge(g,limit=1):
    from deep_invention_dispatch import discharge
    return discharge(g,parse_statement,solve,replay,'poly-transfer-induction-',limit)
