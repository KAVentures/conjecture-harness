"""Global polynomial inequalities on simplices, using exact Bernstein certificates.

The simplex is x_i>=0, sum x_i=1. Homogenization plus nonnegative
coefficients is a universal certificate. Recursive rational simplex splits
can expose local structure; finite sample survival never establishes a bound.
"""
import itertools,json,re
from fractions import Fraction as Q
from math import factorial
from affine import rational
from runtime import strict_json
from symbolic_discovery import terms,encode,add,evaluate

PREFIX='Simplex polynomial inequality: '
MAX_DEGREE=6
MAX_N=4
MAX_DEPTH=5

def normalize(s):
    if not isinstance(s,dict) or set(s)!={'variables','terms'}:raise ValueError('simplex spec')
    vs=s['variables']
    if not isinstance(vs,list) or not 2<=len(vs)<=MAX_N or any(not isinstance(v,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,15}',v) for v in vs) or len(set(vs))!=len(vs):raise ValueError('variables')
    return dict(variables=vs,terms=encode(terms(s['terms'],len(vs),MAX_DEGREE)))

def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))
def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('not simplex')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical simplex claim')
    return s

def compositions(d,n):
    if n==1:yield (d,);return
    for i in range(d+1):
        for r in compositions(d-i,n-1):yield (i,*r)

def multinomial(e):
    v=factorial(sum(e))
    for k in e:v//=factorial(k)
    return v

def homogenize(p,n,d):
    out={}
    for e,c in p.items():
        if sum(e)>d:raise ValueError('degree')
        for f in compositions(d-sum(e),n):
            k=tuple(a+b for a,b in zip(e,f));out[k]=out.get(k,Q(0))+c*multinomial(f)
    return {e:c for e,c in out.items() if c}

def mul(a,b):
    out={}
    for e,c in a.items():
        for f,d in b.items():
            k=tuple(i+j for i,j in zip(e,f));out[k]=out.get(k,Q(0))+c*d
    if len(out)>1024 or any(v.numerator.bit_length()>256 or v.denominator.bit_length()>256 for v in out.values()):raise ValueError('expansion limit')
    return {e:c for e,c in out.items() if c}

def substitute(p,vertices):
    n=len(vertices);zero=(0,)*n;out={}
    images=[{tuple(int(j==k) for j in range(n)):vertices[k][i] for k in range(n) if vertices[k][i]} for i in range(n)]
    for e,c in p.items():
        q={zero:c}
        for k,img in zip(e,images):
            for _ in range(k):q=mul(q,img)
        out=add(out,q)
    return out

def root(n):return tuple(tuple(Q(i==j) for j in range(n)) for i in range(n))

def split(v,i,j):
    m=tuple((a+b)/2 for a,b in zip(v[i],v[j]))
    left=list(v);right=list(v);left[i]=m;right[j]=m
    return tuple(left),tuple(right)

def coefficients(p,vertices,d):
    n=len(vertices)
    h=homogenize(substitute(p,vertices),n,d)
    return {e:h.get(e,Q(0))/multinomial(e) for e in compositions(d,n)}

def point(vertices,e,d):
    if d==0:return vertices[0]
    return tuple(sum(Q(k,d)*v[j] for k,v in zip(e,vertices)) for j in range(len(vertices)))

def val(p,x):return evaluate(p,x[0],x[1:])

def replay(s,cert):
    try:
        s=normalize(s);n=len(s['variables']);p=terms(s['terms'],n,MAX_DEGREE)
        if not isinstance(cert,dict):return None
        if cert.get('kind')=='point' and set(cert)=={'kind','point'}:
            xs=cert['point']
            if not isinstance(xs,list) or len(xs)!=n:return None
            x=list(map(rational,xs))
            return 'refuted' if all(a>=0 for a in x) and sum(x)==1 and val(p,x)<0 else None
        if set(cert)!={'kind','tree'} or cert['kind']!='simplex-cover':return None
        def visit(t,v,depth):
            if depth>MAX_DEPTH or not isinstance(t,dict):return False
            if set(t)=={'degree'}:
                d=t['degree']
                return type(d) is int and max((sum(e) for e in p),default=0)<=d<=MAX_DEGREE+2 and all(c>=0 for c in coefficients(p,v,d).values())
            if set(t)!={'split','left','right'} or not isinstance(t['split'],list) or len(t['split'])!=2:return False
            i,j=t['split']
            if type(i) is not int or type(j) is not int or not 0<=i<j<n:return False
            a,b=split(v,i,j)
            return visit(t['left'],a,depth+1) and visit(t['right'],b,depth+1)
        return 'proved' if visit(cert['tree'],root(n),0) else None
    except (ValueError,TypeError,KeyError,ArithmeticError,AttributeError,RecursionError):return None

def solve(s,depth=3):
    s=normalize(s);n=len(s['variables']);p=terms(s['terms'],n,MAX_DEGREE)
    if type(depth) is not int or not 0<=depth<=MAX_DEPTH:raise ValueError('depth')
    d=max((sum(e) for e in p),default=0);visited=0;witness=None
    def search(v,level):
        nonlocal visited,witness
        visited+=1
        for k in range(d,min(MAX_DEGREE+2,d+2)+1):
            cs=coefficients(p,v,k)
            if min(cs.values())>=0:return dict(degree=k)
            # Bernstein control points guide exact evaluations; coefficient
            # negativity alone is not a counterexample.
            for e in sorted(cs,key=cs.get)[:4]:
                x=point(v,e,k)
                if val(p,x)<0:
                    witness=dict(kind='point',point=list(map(str,x)));return None
        if level>=depth:return None
        # Longest edge midpoint: deterministic, covers both half-simplices.
        i,j=max(itertools.combinations(range(n),2),key=lambda ij:sum((a-b)**2 for a,b in zip(v[ij[0]],v[ij[1]])))
        a,b=split(v,i,j);left=search(a,level+1)
        if witness:return None
        right=search(b,level+1)
        return dict(split=[i,j],left=left,right=right) if left is not None and right is not None else None
    try:t=search(root(n),0)
    except ValueError:t=None
    if witness is not None:
        if replay(s,witness)!='refuted':raise ArithmeticError('point replay failed')
        return dict(status='counterexample',certificate=witness,visited=visited)
    if t is not None:
        cert=dict(kind='simplex-cover',tree=t)
        if replay(s,cert)!='proved':raise ArithmeticError('cover replay failed')
        return dict(status='proved',certificate=cert,visited=visited)
    return dict(status='unknown',visited=visited,scope='bounded Bernstein cover search')

def main():
    import argparse
    from runtime import read_json
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('spec');p.add_argument('--depth',type=int,default=3);a=p.parse_args()
    print(json.dumps(solve(read_json(a.spec),a.depth),indent=2))
if __name__=='__main__':main()
