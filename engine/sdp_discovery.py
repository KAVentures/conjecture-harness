"""Opt-in numerical Gram search followed by exact rational certificate replay.

Requires cvxpy at runtime only. Solver output is a proposal, never a proof.
No solver status, tolerance or approximate eigenvalue certifies positivity.
"""
from fractions import Fraction as Q
from itertools import product
from math import isfinite
from inequality_invention import replay_gram

def recover(target,basis,approx,denominators=(10,100,1000,10000)):
    """Try rational recovery; exact identity and PSD both required."""
    n=len(basis)
    if not 1<=n<=32 or len(approx)!=n or any(len(r)!=n for r in approx):
        raise ValueError('Gram shape')
    if any(not isfinite(float(v)) for r in approx for v in r):
        return None
    for den in denominators:
        if type(den) is not int or not 1<=den<=1000000:
            raise ValueError('denominator limit')
        a=[[Q(0)]*n for _ in range(n)]
        for i in range(n):
            for j in range(i,n):
                # Symmetrize before rational approximation.
                v=(float(approx[i][j])+float(approx[j][i]))/2
                a[i][j]=a[j][i]=Q(v).limit_denominator(den)
        if replay_gram(target,basis,a):
            return a
    return None

def search(target,n,degree=None,solver=None):
    if not 1<=n<=4 or any(len(e)!=n or any(type(i) is not int or i<0 for i in e) or type(c) not in (int,Q) for e,c in target.items()):
        raise ValueError('bounded exact polynomial input required')
    d=max(map(sum,target),default=0)
    degree=(d+1)//2 if degree is None else degree
    if type(degree) is not int or not 0<=degree<=4 or d>2*degree:
        raise ValueError('degree limit')
    basis=[e for e in product(range(degree+1),repeat=n) if sum(e)<=degree]
    if len(basis)>32:
        return dict(status='unknown',reason='basis limit')
    try:
        import cvxpy as cp
    except ImportError:
        return dict(status='unknown',reason='optional cvxpy not installed')
    m=len(basis);G=cp.Variable((m,m),symmetric=True);groups={}
    for i,e in enumerate(basis):
        for j,f in enumerate(basis):
            k=tuple(a+b for a,b in zip(e,f));groups.setdefault(k,[]).append(G[i,j])
    constraints=[G >> 0]
    for e,terms in groups.items():
        constraints.append(sum(terms)==float(target.get(e,0)))
    if any(e not in groups for e in target):
        return dict(status='unknown',reason='basis cannot represent target')
    problem=cp.Problem(cp.Minimize(cp.trace(G)),constraints)
    try:
        problem.solve(solver=solver) if solver else problem.solve()
    except cp.error.SolverError:
        return dict(status='unknown',reason='numerical solver error')
    if G.value is None:
        return dict(status='unknown',reason='no numerical Gram candidate')
    a=recover(target,basis,G.value.tolist())
    if a is None:
        return dict(status='unknown',reason='exact rational recovery failed')
    return dict(status='proved',basis=[list(e) for e in basis],matrix=[[str(v) for v in r] for r in a])


def replay_result(target,result):
    """Replay the JSON-compatible search output without trusting its status."""
    try:
        if result.get('status')!='proved' or set(result)!={'status','basis','matrix'}:
            return False
        return replay_gram(target,[tuple(e) for e in result['basis']],
                           [[Q(x) for x in r] for r in result['matrix']])
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError):
        return False
