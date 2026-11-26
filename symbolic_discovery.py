"""Exact parameterized polynomial summation: discovery by finite differences, proof by induction."""
import itertools,json,re
from fractions import Fraction as F
from math import comb,factorial
from affine import rational
from runtime import strict_json

PREFIX='Parameterized polynomial sum: '
def terms(raw,width,degree=13):
    if not isinstance(raw,list) or len(raw)>128:raise ValueError('term limit')
    out={}
    for t in raw:
        if not isinstance(t,list) or len(t)!=2:raise ValueError('term shape')
        e,c=t
        if not isinstance(e,list) or len(e)!=width or any(type(i) is not int or i<0 for i in e) or sum(e)>degree:raise ValueError('exponents')
        e=tuple(e);out[e]=out.get(e,F(0))+rational(c)
    return {e:c for e,c in out.items() if c}
def encode(p):
    rows=[[list(e),str(c)] for e,c in sorted(p.items()) if c]
    if len(rows)>128 or any(len(c)>80 for _,c in rows):raise ValueError('certificate size limit')
    return rows
def normalize(s):
    if not isinstance(s,dict) or set(s)!={'parameters','relation','summand','rhs'}:raise ValueError('spec shape')
    ps=s['parameters']
    if not isinstance(ps,list) or len(ps)>3 or any(not isinstance(x,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,15}',x) or x in ('n','i') for x in ps) or len(set(ps))!=len(ps):raise ValueError('parameters')
    if s['relation'] not in ('zero','nonnegative'):raise ValueError('relation')
    return dict(parameters=ps,relation=s['relation'],summand=encode(terms(s['summand'],1+len(ps),12)),rhs=encode(terms(s['rhs'],1+len(ps))))
def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))
def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('not symbolic sum')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical symbolic sum')
    return s
def add(a,b,scale=F(1)):
    p=dict(a)
    for e,c in b.items():p[e]=p.get(e,F(0))+scale*c
    return {e:c for e,c in p.items() if c}
def shift(p):
    out={}
    for (k,*rest),c in p.items():
        for j in range(k+1):
            e=(j,*rest);out[e]=out.get(e,F(0))+c*comb(k,j)
    return {e:c for e,c in out.items() if c}
def newton(p):
    groups={}
    for (k,*rest),c in p.items():groups.setdefault(tuple(rest),{})[k]=c
    out={}
    for rest,q in groups.items():
        d=max(q);v=[sum(c*j**k for k,c in q.items()) for j in range(d+1)]
        for k in range(d+1):
            if v[0]:out[(k,*rest)]=v[0]
            v=[b-a for a,b in zip(v,v[1:])]
    return out
def power_basis(p):
    out={}
    for (k,*rest),c in p.items():
        q=[F(1)]
        for j in range(k):
            r=[F(0)]*(len(q)+1)
            for i,v in enumerate(q):r[i]-=j*v;r[i+1]+=v
            q=r
        for j,v in enumerate(q):
            e=(j,*rest);out[e]=out.get(e,F(0))+c*v/factorial(k)
    return {e:c for e,c in out.items() if c}
def antidifference(f):return {(k+1,*rest):c for (k,*rest),c in newton(f).items()}
def evaluate(p,n,params):
    result=F(0)
    for (k,*rest),c in p.items():
        v=c*n**k
        for e,x in zip(rest,params):v*=x**e
        result+=v
    return result
def replay(s,cert):
    try:
        s=normalize(s);w=1+len(s['parameters']);f=terms(s['summand'],w);rhs=terms(s['rhs'],w)
        if not isinstance(cert,dict):return None
        if cert.get('kind')=='point' and set(cert)=={'kind','n','parameters'}:
            n=cert['n'];xs=cert['parameters']
            if type(n) is not int or not 0<=n<=64 or not isinstance(xs,list) or len(xs)!=w-1:return None
            xs=list(map(rational,xs))
            if any(x<0 for x in xs):return None
            v=sum(evaluate(f,i,xs) for i in range(n))-evaluate(rhs,n,xs)
            return 'refuted' if (v!=0 if s['relation']=='zero' else v<0) else None
        if cert.get('kind')!='newton-induction' or set(cert)!={'kind','residual'}:return None
        b=terms(cert['residual'],w)
        if s['relation']=='zero' and b:return None
        if s['relation']=='nonnegative' and any(c<0 for c in b.values()):return None
        q=add(power_basis(b),rhs)
        if any(e[0]==0 for e in q) or add(shift(q),q,F(-1))!=f:return None
        return 'proved'
    except (ValueError,TypeError,KeyError,ArithmeticError,AttributeError):return None
def solve(s,budget=128):
    s=normalize(s)
    if type(budget) is not int or not 1<=budget<=512:raise ValueError('point budget')
    w=1+len(s['parameters']);f=terms(s['summand'],w);rhs=terms(s['rhs'],w)
    res=add(antidifference(f),newton(rhs),F(-1))
    try:
        cert=dict(kind='newton-induction',residual=encode(res))
        if replay(s,cert)=='proved':return dict(status='proved',certificate=cert,tested=0)
    except ValueError:pass
    tested=0
    # Round-robin across n and parameter tuples to cover boundaries early.
    ns=(0,1,2,3,4,8,16,32,64)
    for xs,n in itertools.product(itertools.product(('1','0','2','1/2','8'),repeat=w-1),ns):
        if tested>=budget:break
        tested+=1;cert=dict(kind='point',n=n,parameters=list(xs))
        if replay(s,cert)=='refuted':return dict(status='counterexample',certificate=cert,tested=tested)
    return dict(status='unknown',tested=tested,scope='nonnegative Newton coefficients are sufficient, not necessary')
def discover(summand,parameters):
    s=normalize(dict(parameters=parameters,relation='zero',summand=summand,rhs=[]))
    q=power_basis(antidifference(terms(s['summand'],1+len(parameters))))
    s=normalize(dict(s,rhs=encode(q)));cert=dict(kind='newton-induction',residual=[])
    if replay(s,cert)!='proved':raise ArithmeticError('induction replay failed')
    return dict(spec=s,certificate=cert)
def main():
    import argparse
    from runtime import read_json
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('spec');p.add_argument('--discover',action='store_true');p.add_argument('--budget',type=int,default=128);a=p.parse_args()
    s=read_json(a.spec);r=discover(s['summand'],s['parameters']) if a.discover else solve(s,a.budget)
    print(json.dumps(r,indent=2))
if __name__=='__main__':main()
