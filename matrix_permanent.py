"""Exact permanent-polynomial discovery; bounded finite evidence, never universal proof by sampling."""
from fractions import Fraction as Q
from math import factorial, comb
from itertools import permutations
import json, random

PREFIX = 'matrix-permanent:'
MAX_N = 7

def rational(x):
    if type(x) not in (int,str) or len(str(x))>128: raise ValueError('expected bounded rational')
    try: return Q(x)
    except (ZeroDivisionError,ValueError) as e: raise ValueError('invalid rational') from e

def matrix(rows):
    if not isinstance(rows,(list,tuple)) or not 3<=len(rows)<=MAX_N: raise ValueError('finite order 3..7')
    n=len(rows)
    if any(not isinstance(r,(list,tuple)) or len(r)!=n for r in rows): raise ValueError('square matrix')
    a=tuple(tuple(rational(x) for x in r) for r in rows)
    if any(x<0 for r in a for x in r) or any(sum(r)!=1 for r in a) or any(sum(a[i][j] for i in range(n))!=1 for j in range(n)): raise ValueError('not doubly stochastic')
    return a

def encode(a): return [[str(x) for x in r] for r in a]

def spec(s):
    if not isinstance(s,dict) or s.get('kind') not in ('lih-wang','signed-prefix') or set(s)-{'kind','matrix'}: raise ValueError('unsupported claim')
    return dict(kind=s['kind'],**({'matrix':encode(matrix(s['matrix']))} if 'matrix' in s else {}))

def statement(s): return PREFIX+json.dumps(spec(s),sort_keys=True,separators=(',',':'))
def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX): raise ValueError('not a matrix claim')
    s=spec(json.loads(text[len(PREFIX):]))
    if statement(s)!=text: raise ValueError('noncanonical statement')
    return s

def coefficients(a):
    """Subset DP for per(J+t(A-J))/per(J), exact in t."""
    n=len(a); u=Q(1,n); dp={0:[Q(1)]}
    for i in range(n):
        nxt={}
        for mask,p in dp.items():
            for j in range(n):
                if mask>>j&1: continue
                q=nxt.setdefault(mask|(1<<j),[Q(0)]*(i+2)); b=a[i][j]-u
                for k,v in enumerate(p):
                    q[k]+=u*v; q[k+1]+=b*v
        dp=nxt
    return [v/(factorial(n)*u**n) for v in dp[(1<<n)-1]]

def permanent(a):
    """Independent scalar evaluator, permutation definition."""
    total=Q(0)
    for p in permutations(range(len(a))):
        term=Q(1)
        for i,j in enumerate(p): term*=a[i][j]
        total+=term
    return total

def prefixes(c):
    out=[]; v=Q(0)
    for k in range(2,len(c)):
        v+=(2-Q(1,2**(k-2)))*c[k];out.append(v)
    return out

def gap_poly(c):
    # normalized chord gap / t, continuous at zero
    return [sum(c[1:])]+[-v for v in c[2:]]

def value(p,t): return sum(v*t**k for k,v in enumerate(p))

def bernstein(p,l,r):
    """Power coefficients after affine substitution, then Bernstein on [0,1]."""
    d=len(p)-1
    a=[sum(p[k]*comb(k,j)*l**(k-j)*(r-l)**j for k in range(j,d+1)) for j in range(d+1)]
    return [sum(a[j]*Q(comb(i,j),comb(d,j)) for j in range(i+1)) for i in range(d+1)]

def interval_certificate(p,depth=5):
    pending=[(Q(0),Q(1,2),0)]; accepted=[]
    while pending:
        l,r,d=pending.pop()
        if min(bernstein(p,l,r))>=0: accepted.append([str(l),str(r)]);continue
        if d>=depth:return None
        m=(l+r)/2;pending.extend([(m,r,d+1),(l,m,d+1)])
    return sorted(accepted,key=lambda pair:Q(pair[0]))

def replay(s,certificate):
    try:
        s=spec(s)
        if not isinstance(certificate,dict):return None
        kind=certificate.get('kind')
        a=matrix(certificate['matrix'])
        if 'matrix' in s and encode(a)!=s['matrix']:return None
        if kind=='point' and s['kind']=='lih-wang':
            t=rational(certificate['t'])
            if not 0<t<=Q(1,2):return None
            n=len(a);u=Q(1,n); b=[[u*(1-t)+t*x for x in row] for row in a]
            return 'refuted' if permanent(b)>(1-t)*factorial(n)*u**n+t*permanent(a) else None
        c=coefficients(a)
        if kind=='prefix-point' and s['kind']=='signed-prefix':
            k=certificate['k']
            if type(k) is int and 2<=k<=len(a) and prefixes(c)[k-2]<0:return 'refuted'
        if 'matrix' not in s:return None # finite evidence cannot prove universal statements
        if kind=='prefix-proof' and s['kind']=='signed-prefix' and min(prefixes(c))>=0:return 'proved'
        if kind=='bernstein' and s['kind']=='lih-wang':
            intervals=certificate['intervals']
            if not isinstance(intervals,list) or not 1<=len(intervals)<=64:return None
            end=Q(0); p=gap_poly(c)
            for pair in intervals:
                l,r=map(rational,pair)
                if l!=end or not l<r<=Q(1,2) or min(bernstein(p,l,r))<0:return None
                end=r
            if end==Q(1,2):return 'proved'
    except (ValueError,TypeError,KeyError,ArithmeticError,AttributeError):pass
    return None

def mixed(n,rng,count):
    rows=[[Q(0) for _ in range(n)] for _ in range(n)]
    weights=[rng.randint(1,5) for _ in range(count)];den=sum(weights)
    for w in weights:
        p=list(range(n));rng.shuffle(p)
        for i,j in enumerate(p):rows[i][j]+=Q(w,den)
    return tuple(map(tuple,rows))

def blocks(n):
    for k in range(1,n):
        yield tuple(tuple(Q(1,k) if i<k and j<k else Q(1,n-k) if i>=k and j>=k else Q(0) for j in range(n)) for i in range(n))

def cycle_move(a,rng):
    """Feasible rational 2x2 transportation-polytope move, including support boundaries."""
    n=len(a);i,j=rng.sample(range(n),2);u,v=rng.sample(range(n),2)
    lo=-min(a[i][u],a[j][v]);hi=min(a[i][v],a[j][u]);d=lo+(hi-lo)*Q(rng.randrange(5),4)
    b=[list(r) for r in a]
    for row,col,sign in ((i,u,1),(j,v,1),(i,v,-1),(j,u,-1)):b[row][col]+=sign*d
    return tuple(map(tuple,b))

def score(s,c):
    if s['kind']=='signed-prefix':
        v,k=min((v,k) for k,v in enumerate(prefixes(c),2));return v,dict(kind='prefix-point',k=k)
    p=gap_poly(c)
    v,t=min((value(p,Q(i,16)),Q(i,16)) for i in range(1,9))
    return v,dict(kind='point',t=str(t))

def solve(s,budget=24,seed=0):
    s=spec(s)
    if type(budget) is not int or not 1<=budget<=256 or type(seed) is not int:raise ValueError('invalid search limits')
    rng=random.Random(seed); tested=0; best=None; best_a=None; visited=set()
    def probe(a):
        nonlocal tested,best,best_a
        if a in visited or tested>=budget:return None
        visited.add(a);tested+=1;c=coefficients(a);v,w=score(s,c)
        if best is None or v<best:best,best_a=v,a
        if v<0:
            cert=dict(w,matrix=encode(a))
            if replay(s,cert)!='refuted':raise ArithmeticError('witness replay failed')
            return dict(status='counterexample',certificate=cert,tested=tested)
        return None
    if 'matrix' in s:
        a=matrix(s['matrix']);r=probe(a)
        if r:return r
        c=coefficients(a);cert=dict(matrix=encode(a),kind='prefix-proof') if s['kind']=='signed-prefix' else dict(matrix=encode(a),kind='bernstein',intervals=interval_certificate(gap_poly(c)))
        if replay(s,cert)=='proved':return dict(status='proved',certificate=cert,tested=tested)
    else:
        for n in range(3,6):
            for a in blocks(n):
                r=probe(a)
                if r:return r
        for i in range(budget*3):
            if tested>=budget:break
            n=3+i%3
            a=cycle_move(best_a,rng) if best_a is not None and i%3==0 else mixed(n,rng,1+i%7)
            r=probe(a)
            if r:return r
    return dict(status='unknown',tested=tested,best=str(best),best_matrix=encode(best_a) if best_a else None,scope='bounded rational search; no universal certificate')

def prefix_bridge(parent,premise):
    """Typed Abel-summation rule, same scope/matrix, no sampled premise."""
    try:
        a,b=parse_statement(parent),parse_statement(premise)
        return a['kind']=='lih-wang' and b['kind']=='signed-prefix' and a.get('matrix')==b.get('matrix')
    except (ValueError,TypeError,KeyError):return False

def partitions(k):
    if k==0:yield ();return
    for p in partitions(k-1):
        yield p+((k-1,),)
        for j in range(len(p)):yield p[:j]+(p[j]+(k-1,),)+p[j+1:]

def matching_identity(k,centered=True):
    """Dimension-independent Mobius expansion of k! times matching sum.
    Each term is an unrestricted index contraction specified by row/column partitions.
    Singleton blocks vanish for zero row/column sums. No assertion of positivity."""
    if type(k) is not int or not 1<=k<=5:raise ValueError('symbolic order 1..5')
    ps=[p for p in partitions(k) if not centered or all(len(b)>1 for b in p)]
    def mob(p):
        m=1
        for b in p:m*=(-1)**(len(b)-1)*factorial(len(b)-1)
        return m
    return [(r,c,mob(r)*mob(c)) for r in ps for c in ps]

def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('claim',choices=['lih-wang','signed-prefix']);p.add_argument('--matrix',help='JSON file with rational entries');p.add_argument('--budget',type=int,default=24);p.add_argument('--seed',type=int,default=0);a=p.parse_args()
    s=dict(kind=a.claim)
    if a.matrix:
        with open(a.matrix,encoding='utf-8') as f:s['matrix']=json.load(f)
    print(json.dumps(solve(s,a.budget,a.seed),indent=2))
if __name__=='__main__':main()
