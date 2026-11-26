"""Exact universal Shannon-capacity upper certificates and finite refutations.
Edges denote confusability; products are strong graph products.
"""
import json,itertools
from fractions import Fraction as F
from affine import rational
from runtime import strict_json

PREFIX='Shannon capacity upper bound (strong product, edges are confusable): '


def normalize(s):
    if not isinstance(s,dict) or set(s)!={'n','edges','upper'}:raise ValueError('invalid capacity spec')
    n=s['n'];es=s['edges'];t=rational(s['upper'])
    if type(n) is not int or not 1<=n<=32 or t<=0:raise ValueError('invalid graph order or bound')
    if not isinstance(es,list) or len(es)>n*(n-1)//2:raise ValueError('invalid edge list')
    pairs=set()
    for e in es:
        if not isinstance(e,list) or len(e)!=2 or any(type(i) is not int for i in e) or not 0<=e[0]<e[1]<n or tuple(e) in pairs:raise ValueError('invalid or duplicate edge')
        pairs.add(tuple(e))
    return dict(n=n,edges=[list(e) for e in sorted(pairs)],upper=str(t))


def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))


def parse_statement(s):
    if not s.startswith(PREFIX):raise ValueError('not a canonical capacity claim')
    x=strict_json(s[len(PREFIX):])
    if statement(x)!=s:raise ValueError('noncanonical capacity claim')
    return x


def psd(matrix):
    """Exact Schur complement elimination; singular zero pivots are checked."""
    a=[list(r) for r in matrix];n=len(a)
    if any(len(r)!=n for r in a) or any(a[i][j]!=a[j][i] for i in range(n) for j in range(n)):return False
    for i in range(n):
        d=a[i][i]
        if d<0:return False
        if d==0:
            if any(a[i][j] for j in range(i+1,n)):return False
            continue
        for j in range(i+1,n):
            for k in range(j,n):
                a[j][k]-=a[i][j]*a[i][k]/d;a[k][j]=a[j][k]
    return True


def rank(matrix,prime):
    a=[list(r) for r in matrix];r=0;n=len(a)
    for j in range(n):
        pivot=next((i for i in range(r,n) if a[i][j]%prime),None)
        if pivot is None:continue
        a[r],a[pivot]=a[pivot],a[r];inv=pow(a[r][j]%prime,-1,prime)
        a[r]=[(x*inv)%prime for x in a[r]]
        for i in range(r+1,n):
            k=a[i][j];a[i]=[(x-k*y)%prime for x,y in zip(a[i],a[r])]
        r+=1
    return r


PRIMES=(2,3,5,7,11,13,17,19,23,29,31)


def replay(s,c):
    """Check all hypotheses of one of two tensor-product upper bound theorems."""
    try:
        s=normalize(s);n=s['n'];t=F(s['upper']);es={tuple(e) for e in s['edges']}
        if not isinstance(c,dict):return False
        if set(c)=={'kind','matrix'} and c['kind']=='gram':
            a=c['matrix']
            if not isinstance(a,list) or len(a)!=n or any(not isinstance(r,list) or len(r)!=n for r in a):return False
            a=[list(map(rational,r)) for r in a]
            if any(a[i][i]!=1 for i in range(n)) or any(a[i][j] or a[j][i] for i in range(n) for j in range(i+1,n) if (i,j) not in es):return False
            return psd([[v-1/t for v in row] for row in a])
        if set(c)=={'kind','prime','matrix'} and c['kind']=='rank':
            q=c['prime'];a=c['matrix']
            if type(q) is not int or q not in PRIMES or not isinstance(a,list) or len(a)!=n or any(not isinstance(r,list) or len(r)!=n or any(type(v) is not int or not 0<=v<q for v in r) for r in a):return False
            if any(a[i][i]==0 for i in range(n)) or any(a[i][j] or a[j][i] for i in range(n) for j in range(i+1,n) if (i,j) not in es):return False
            return rank(a,q)<=t
        return False
    except (ValueError,TypeError,KeyError,ZeroDivisionError,OverflowError):return False


def replay_counterexample(s,words):
    try:
        s=normalize(s);n=s['n'];es={tuple(e) for e in s['edges']}
        if not isinstance(words,list) or not 1<=len(words)<=2000 or not isinstance(words[0],list) or not 1<=len(words[0])<=12:return False
        k=len(words[0])
        if any(not isinstance(w,list) or len(w)!=k or any(type(v) is not int or not 0<=v<n for v in w) for w in words):return False
        if len(words)<=F(s['upper'])**k:return False
        return all(any(x!=y and tuple(sorted((x,y))) not in es for x,y in zip(a,b)) for a,b in itertools.combinations(words,2))
    except (ValueError,TypeError,KeyError):return False


def solve(s):
    s=normalize(s);n=s['n'];t=F(s['upper']);es={tuple(e) for e in s['edges']};tested=0
    def done(status,certificate=None):return dict(status=status,certificate=certificate,tested=tested)
    def gram(a):return dict(kind='gram',matrix=[[str(v) for v in row] for row in a])
    def adj(i,j):return tuple(sorted((i,j))) in es
    def try_cert(c):
        nonlocal tested
        tested+=1;return replay(s,c)
    # Transfer from clique covers, and regular adjacency spectra.
    groups=[]
    for i in sorted(range(n),key=lambda i:(-sum(adj(i,j) for j in range(n)),i)):
        g=next((g for g in groups if all(adj(i,j) for j in g)),None)
        if g is None:groups.append([i])
        else:g.append(i)
    labels={i:k for k,g in enumerate(groups) for i in g}
    c=gram([[F(labels[i]==labels[j]) for j in range(n)] for i in range(n)])
    if len(groups)<=t and try_cert(c):return done('proved',c)
    ds=[sum(adj(i,j) for j in range(n)) for i in range(n)]
    if len(set(ds))==1 and ds[0] and t<=n:
        w=(F(n)/t-1)/ds[0]
        c=gram([[F(1) if i==j else w if adj(i,j) else F(0) for j in range(n)] for i in range(n)])
        if try_cert(c):return done('proved',c)
    # Independent algebraic route: fitting matrices over small prime fields.
    for q in PRIMES[:5]:
        for w in range(1,q):
            c=dict(kind='rank',prime=q,matrix=[[1 if i==j else w if adj(i,j) else 0 for j in range(n)] for i in range(n)])
            if try_cert(c):return done('proved',c)
    # Exact constructive refutation only; limited greedy independent sets.
    for k in (1,2):
        if n**k>1024 or t**k>=n**k:continue
        for order in (range(n),reversed(range(n))):
            ws=list(itertools.product(list(order),repeat=k));chosen=[]
            for w in ws:
                if all(any(x!=y and not adj(x,y) for x,y in zip(w,v)) for v in chosen):
                    chosen.append(w)
                    if len(chosen)>t**k:
                        words=[list(v) for v in chosen]
                        if not replay_counterexample(s,words):raise ArithmeticError('packing replay failed')
                        return done('counterexample',dict(kind='packing',words=words))
    return done('unknown')
