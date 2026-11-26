"""Exact, non-model checkers. Never executes candidate-supplied code."""
from fractions import Fraction as F
from itertools import combinations
import argparse, json
from pathlib import Path

ALPHABET = tuple(combinations(range(5),2))

def packing(words):
    if not isinstance(words,list) or not words or not isinstance(words[0],list) or not words[0]:
        raise ValueError('nonempty list of nonempty words required')
    n=len(words[0]); clean=[]
    if n>64 or len(words)>2000: raise ValueError('packing exceeds checker limits (64 coordinates, 2000 words)')
    for w in words:
        if not isinstance(w,list) or len(w)!=n or any(type(x) is not int or not 0<=x<10 for x in w):
            raise ValueError('words must have equal length and symbols 0..9')
        clean.append(tuple(w))
    if len(set(clean))!=len(clean): raise ValueError('duplicate words')
    for a,b in combinations(clean,2):
        if not any(set(ALPHABET[x]).isdisjoint(ALPHABET[y]) for x,y in zip(a,b)):
            raise ValueError(f'confusable pair: {a}, {b}')
    m=len(clean)
    return {'verified_packing':True,'n':n,'size':m,'beats_cuberoot_12':m**3>12**n,'full_capacity_resolved':False}

def rational(x):
    if type(x) not in (str,int): raise ValueError('use exact integer or fraction strings, never floats')
    if len(str(x))>128: raise ValueError('rational input exceeds 128 characters')
    return F(x)

def permanent(a):
    n=len(a); total=F(0)
    for mask in range(1,1<<n):
        prod=F(1)
        for row in a:
            prod*=sum(row[j] for j in range(n) if mask>>j&1)
        total+=prod if (n-mask.bit_count())%2==0 else -prod
    return total

def lih_wang(matrix,t):
    if not isinstance(matrix,list) or not 3<=len(matrix)<=12: raise ValueError('checker supports n=3..12')
    n=len(matrix)
    if any(not isinstance(r,list) or len(r)!=n for r in matrix): raise ValueError('square matrix required')
    a=[[rational(x) for x in r] for r in matrix]; t=rational(t)
    if not F(1,2)<=t<=1: raise ValueError('t outside domain')
    if any(x<0 for r in a for x in r) or any(sum(r)!=1 for r in a) or any(sum(c)!=1 for c in zip(*a)):
        raise ValueError('matrix is not doubly stochastic')
    j=[[F(1,n)]*n for _ in range(n)]
    b=[[t/n+(1-t)*x for x in r] for r in a]
    gap=permanent(b)-t*permanent(j)-(1-t)*permanent(a)
    return {'valid_instance':True,'lhs_minus_rhs':str(gap),'verified_counterexample':gap>0}

def check(target,witness):
    if target=='shannon': return packing(witness['words'])
    if target=='lih-wang': return lih_wang(witness['matrix'],witness['t'])
    raise ValueError('unknown target')

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('target'); p.add_argument('file',type=Path); a=p.parse_args()
    print(json.dumps(check(a.target,json.loads(a.file.read_text())),indent=2))
