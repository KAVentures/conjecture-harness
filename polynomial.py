"""Bounded exact polynomial identities, weighted squares and counterexamples."""
import itertools,json,re
from fractions import Fraction as F
from affine import rational
from runtime import strict_json

PREFIX='Universal rational polynomial claim: '

def terms(raw,n,degree=8):
    if not isinstance(raw,list) or len(raw)>64:raise ValueError('at most 64 terms')
    p={}
    for t in raw:
        if not isinstance(t,list) or len(t)!=2:raise ValueError('expected [exponents, coefficient]')
        e,c=t
        if not isinstance(e,list) or len(e)!=n or any(type(x) is not int or x<0 for x in e) or sum(e)>degree:raise ValueError('invalid exponents')
        e=tuple(e);p[e]=p.get(e,F(0))+rational(c)
    return {e:c for e,c in p.items() if c}

def encode(p):
    out=[[list(e),str(c)] for e,c in sorted(p.items()) if c]
    if any(len(c)>80 for _,c in out):raise ValueError('coefficient limit')
    return out

def normalize(s):
    if not isinstance(s,dict) or set(s)!={'variables','domain','relation','terms'}:raise ValueError('invalid polynomial spec')
    vs=s['variables']
    if not isinstance(vs,list) or not 1<=len(vs)<=4 or any(not isinstance(v,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,15}',v) for v in vs) or len(set(vs))!=len(vs):raise ValueError('invalid variables')
    if s['domain'] not in ('real','nonnegative') or s['relation'] not in ('zero','nonnegative'):raise ValueError('invalid domain or relation')
    return dict(variables=vs,domain=s['domain'],relation=s['relation'],terms=encode(terms(s['terms'],len(vs))))

def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))

def parse_statement(s):
    if not s.startswith(PREFIX):raise ValueError('not a polynomial claim')
    x=strict_json(s[len(PREFIX):])
    if statement(x)!=s:raise ValueError('noncanonical polynomial claim')
    return x

def value(p,x):return sum((c*prod(e,x) for e,c in p.items()),F(0))

def prod(e,x):
    a=F(1)
    for k,v in zip(e,x):a*=v**k
    return a

def replay(s,cert):
    s=normalize(s);n=len(s['variables']);p=terms(s['terms'],n)
    if not isinstance(cert,dict):raise ValueError('invalid certificate')
    if cert=={'kind':'identity'}:return s['relation']=='zero' and not p
    if cert.get('kind')=='point' and set(cert)=={'kind','point'}:
        x=cert['point']
        if not isinstance(x,list) or len(x)!=n:raise ValueError('invalid point')
        x=list(map(rational,x))
        if s['domain']=='nonnegative' and any(v<0 for v in x):return False
        v=value(p,x);return v!=0 if s['relation']=='zero' else v<0
    if s['relation']!='nonnegative' or set(cert)!={'kind','squares','monomials'} or cert['kind']!='sos':return False
    ms=terms(cert['monomials'],n)
    if any(c<0 or (s['domain']=='real' and any(k%2 for k in e)) for e,c in ms.items()):return False
    squares=cert['squares']
    if not isinstance(squares,list) or len(squares)>32:raise ValueError('square limit')
    total=dict(ms)
    for sq in squares:
        if not isinstance(sq,list) or len(sq)!=2:raise ValueError('invalid square')
        w=rational(sq[0]);q=terms(sq[1],n,4)
        if w<=0:return False
        for a,c in q.items():
            for b,d in q.items():
                e=tuple(i+j for i,j in zip(a,b));total[e]=total.get(e,F(0))+w*c*d
    return {e:c for e,c in total.items() if c}==p

def gram(p):
    # A restricted Gram choice: even terms supply diagonal entries, other
    # terms are assigned to the first compatible off-diagonal pair.
    basis=sorted(tuple(k//2 for k in e) for e,c in p.items() if all(k%2==0 for k in e) and c>0)
    if len(basis)>32:return None
    n=len(basis);a=[[F(0) for _ in basis] for _ in basis]
    for i,b in enumerate(basis):a[i][i]=p[tuple(2*k for k in b)]
    for e,c in p.items():
        if c>0 and all(k%2==0 for k in e):continue
        pair=next(((i,j) for i in range(n) for j in range(i+1,n) if tuple(x+y for x,y in zip(basis[i],basis[j]))==e),None)
        if pair is None:return None
        i,j=pair;a[i][j]=a[j][i]=c/2
    squares=[]
    for i in range(n):
        d=a[i][i]
        if d<0:return None
        if not d:
            if any(a[i][j] for j in range(i+1,n)):return None
            continue
        q={basis[i]:F(1)}
        for j in range(i+1,n):q[basis[j]]=a[i][j]/d
        squares.append([str(d),encode(q)])
        for j in range(i+1,n):
            for k in range(i+1,n):a[j][k]-=a[i][j]*a[i][k]/d
        if any(x.numerator.bit_length()>240 or x.denominator.bit_length()>240 for row in a for x in row):return None
    return squares

def solve(s,budget=256):
    if type(budget) is not int or not 1<=budget<=4096:raise ValueError('invalid point budget')
    s=normalize(s);n=len(s['variables']);p=terms(s['terms'],n)
    def done(status,cert=None,tested=0):
        if cert is not None and not replay(s,cert):raise ArithmeticError('certificate replay failed')
        return dict(status=status,certificate=cert,tested=tested)
    if s['relation']=='zero' and not p:return done('proved',{'kind':'identity'})
    if s['relation']=='nonnegative':
        mono={e:c for e,c in p.items() if c>0 and (s['domain']=='nonnegative' or all(k%2==0 for k in e))}
        if mono==p:return done('proved',dict(kind='sos',squares=[],monomials=encode(mono)))
        # In the orthant, remove positive odd monomials as a second attempt.
        for residual,extra in [(p,{}),({e:c for e,c in p.items() if not (s['domain']=='nonnegative' and c>0 and any(k%2 for k in e))},{e:c for e,c in p.items() if s['domain']=='nonnegative' and c>0 and any(k%2 for k in e)})]:
            try:
                sq=gram(residual)
                if sq is not None and all(len(w)<=80 for w,_ in sq):return done('proved',dict(kind='sos',squares=sq,monomials=encode(extra)))
            except ValueError:continue
    grid=[F(0),F(1),F(2),F(1,2)] if s['domain']=='nonnegative' else [F(0),F(1),F(-1),F(2),F(-2),F(1,2),F(-1,2)]
    tested=0
    for x in itertools.product(grid,repeat=n):
        if tested>=budget:break
        tested+=1;v=value(p,x)
        if (v!=0 if s['relation']=='zero' else v<0):return done('counterexample',dict(kind='point',point=list(map(str,x))),tested)
    return done('unknown',tested=tested)
