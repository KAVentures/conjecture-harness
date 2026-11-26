"""Exact univariate semialgebraic implications by sign-invariant cells.

Every open cell is sampled rationally. Every algebraic root is handled by
root counts and exact gcds, so equality-only feasible sets are not missed.
"""
from fractions import Fraction as Q
from univariate_sign import trim,monic,multiply,divide,exact_divide,gcd,derivative,sturm,sign

MAX_DEGREE=32
MAX_SPLITS=1024

def value(p,x):
    v=Q(0)
    for c in reversed(p):v=v*x+c
    return v

def at(seq,x):
    signs=[sign(value(p,x)) for p in seq]
    signs=[s for s in signs if s]
    return sum(a!=b for a,b in zip(signs,signs[1:]))

def count(seq,a,b):return at(seq,a)-at(seq,b)

def root_union(polys,domain):
    u=[Q(1)]
    for p in polys:
        if len(p)<=1:continue
        q=monic(exact_divide(p,gcd(p,derivative(p))))
        u=monic(multiply(u,exact_divide(q,gcd(u,q))))
        if len(u)>MAX_DEGREE+1:raise ValueError('root union degree limit')
    if domain=='nonnegative' and not u[0]:u=exact_divide(u,[Q(0),Q(1)])
    return u

def isolate(u,domain):
    # Cauchy bound is strictly larger than all absolute root values.
    b=Q(2)+max((abs(c/u[-1]) for c in u[:-1]),default=Q(0))
    hi=Q(b.__ceil__());lo=-hi if domain=='real' else Q(0)
    seq=sturm(u);todo=[(lo,hi,count(seq,lo,hi))];intervals=[];steps=0
    while todo:
        a,b,k=todo.pop()
        if not k:continue
        if k<0:raise ArithmeticError('negative root count')
        if k==1 and (domain=='real' or a>0):intervals.append((a,b));continue
        steps+=1
        if steps>MAX_SPLITS:raise ValueError('isolation split limit')
        n=len(u)+1
        # More than degree many distinct candidates in the middle third;
        # at least one is not a root, and both children shrink geometrically.
        choices=[(a+b)/2]+[a+(b-a)*Q(j,3*n) for j in range(n,2*n+1)]
        m=next((x for x in choices if value(u,x)),None)
        if m is None:raise ArithmeticError('no nonroot split point')
        if m.numerator.bit_length()>4096 or m.denominator.bit_length()>4096:raise ValueError('isolation endpoint growth')
        left=count(seq,a,m);right=count(seq,m,b)
        if left+right!=k or min(left,right)<0:raise ArithmeticError('root count mismatch')
        todo.append((m,b,right));todo.append((a,m,left))
    return lo,hi,sorted(intervals)

def classify(raw,relations,domain):
    if domain not in ('real','nonnegative') or not isinstance(raw,(list,tuple)) or not 1<=len(raw)<=9 or not isinstance(relations,(list,tuple)) or len(relations)!=len(raw)-1 or any(r not in ('zero','nonnegative') for r in relations):raise ValueError('unsupported implication')
    if any(not isinstance(p,(list,tuple)) or len(p)>9 or any(type(c) not in (int,Q) for c in p) for p in raw):raise ValueError('exact coefficients required')
    polys=[trim([Q(c) for c in p]) for p in raw]
    u=root_union(polys,domain);lo,hi,intervals=isolate(u,domain)
    gs=[sturm(gcd(u,p)) if p else None for p in polys]
    # Endpoints of the isolating intervals represent every open sign cell;
    # include the half-line endpoint separately, even if it is an isolated root.
    points={hi}
    if domain=='real':points.add(lo)
    for a,b in intervals:points.update((a,b))
    if domain=='nonnegative':points.add(Q(0))
    checked=0;feasible=0
    def inspect(signs,witness):
        nonlocal checked,feasible
        checked+=1
        if not all(s==0 if r=='zero' else s>=0 for r,s in zip(relations,signs)):return None
        feasible+=1
        if signs[-1]<0:return dict(witness,signs=signs)
        return None
    for x in sorted(points):
        w=inspect([sign(value(p,x)) for p in polys],dict(kind='rational',point=str(x)))
        if w:return dict(outcome='refuted',roots=len(intervals),witness=w)
    for a,b in intervals:
        signs=[]
        for p,g in zip(polys,gs):
            if not p or count(g,a,b):signs.append(0)
            else:signs.append(sign(value(p,a)))
        w=inspect(signs,dict(kind='algebraic-root',interval=[str(a),str(b)]))
        if w:return dict(outcome='refuted',roots=len(intervals),witness=w)
    return dict(outcome='proved',roots=len(intervals),checked_representatives=checked,feasible_representatives=feasible)

def replay(raw,relations,domain,cert):
    try:
        if not isinstance(cert,dict) or set(cert)!={'kind','classification'} or cert['kind']!='sign-cells':return None
        r=classify(raw,relations,domain)
        return r['outcome'] if cert['classification']==r else None
    except (ValueError,TypeError,ArithmeticError,KeyError):return None
