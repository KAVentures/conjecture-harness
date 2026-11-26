"""Exact sign decisions for univariate polynomial implications on integer tails."""
from fractions import Fraction as Q
from univariate_sign import trim,derivative,divide,sign
from sign_cells import root_union,count,value

MAX_SPLITS=4096

def sturm(p):
    # Positive scaling preserves the sign variations while controlling growth.
    a=p;b=derivative(a);seq=[a]
    while b:
        b=trim([v/abs(b[-1]) for v in b]);seq.append(b)
        _,r=divide(a,b);a,b=b,trim([-v for v in r])
    return seq

def classify(raw,relations,start=0):
    if type(start) is not int or not 0<=start<=10**12 or not isinstance(raw,(list,tuple)) or not 1<=len(raw)<=9 or not isinstance(relations,(list,tuple)) or len(relations)!=len(raw)-1 or any(r not in ('zero','nonnegative') for r in relations):raise ValueError('integer implication limits')
    if any(not isinstance(p,(list,tuple)) or len(p)>9 or any(type(c) not in (int,Q) for c in p) for p in raw):raise ValueError('exact coefficients required')
    ps=[trim([Q(c) for c in p]) for p in raw]
    u=root_union(ps,'nonnegative');seq=sturm(u)
    bound=max(start, (Q(2)+max((abs(c/u[-1]) for c in u[:-1]),default=Q(0))).__ceil__())
    if bound.bit_length()>512:raise ValueError('integer bound growth')
    todo=[(start,bound)];splits=0;tested=set()
    def probe(n):
        if n in tested:return None
        tested.add(n);ss=[sign(value(p,Q(n))) for p in ps]
        if ss[-1]<0 and all(s==0 if r=='zero' else s>=0 for r,s in zip(relations,ss)):
            return dict(outcome='refuted',witness=str(n),signs=ss)
        return None
    # Beyond bound every nonzero polynomial has constant sign, including at bound.
    hit=probe(bound)
    if hit:return hit
    while todo:
        a,b=todo.pop()
        hit=probe(a)
        if hit:return hit
        if a==b:continue
        roots=count(seq,Q(a),Q(b))
        if roots<0:raise ArithmeticError('negative root count')
        if roots==0:
            # a may be a root (or zero removed from the root union), but
            # (a,b] is root-free. One integer strictly above a suffices.
            hit=probe(a+1)
            if hit:return hit
            continue
        splits+=1
        if splits>MAX_SPLITS:raise ValueError('integer partition limit')
        m=(a+b)//2;todo.append((m+1,b));todo.append((a,m))
    return dict(outcome='proved',bound=str(bound),splits=splits,representatives=len(tested))


def replay(raw,relations,start,cert):
    try:
        if not isinstance(cert,dict) or set(cert)!={'kind','classification'} or cert['kind']!='integer-sign':return None
        r=cert['classification']
        if isinstance(r,dict) and set(r)=={'outcome','witness','signs'} and r['outcome']=='refuted':
            x=r['witness']
            if not isinstance(x,str) or len(x)>160 or not x.isdigit() or str(int(x))!=x or int(x)<start:return None
            ss=[sign(value(p,Q(x))) for p in raw]
            return 'refuted' if ss==r['signs'] and ss[-1]<0 and all(s==0 if rel=='zero' else s>=0 for rel,s in zip(relations,ss)) else None
        expected=classify(raw,relations,start)
        return 'proved' if expected==r and expected['outcome']=='proved' else None
    except (ValueError,TypeError,KeyError,ArithmeticError,AttributeError):return None
