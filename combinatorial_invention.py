"""Exact weighted matching recurrences and symbolic partition contractions.

The identities hold at arbitrary dimension/order; enumeration is explicitly
budgeted. No sign claim follows from a contraction expansion alone.
"""
from collections import Counter
from fractions import Fraction as Q
from functools import lru_cache
from math import factorial
from itertools import permutations

def partitions(k, minimum=2, budget=10000):
    """Set partitions with all block sizes >= minimum, canonical block order."""
    if type(k) is not int or not 0 <= k <= 14 or minimum < 1:
        raise ValueError("enumeration limits")
    count = 0
    def visit(i, blocks):
        nonlocal count
        count += 1
        if count > budget:
            raise OverflowError("partition search budget")
        if i == k:
            if all(len(b) >= minimum for b in blocks):
                yield tuple(tuple(b) for b in blocks)
            return
        if sum(max(0, minimum-len(b)) for b in blocks) > k-i:
            return
        for j in range(len(blocks)):
            blocks[j].append(i)
            yield from visit(i+1, blocks)
            blocks[j].pop()
        blocks.append([i])
        yield from visit(i+1, blocks)
        blocks.pop()
    yield from visit(0, [])

def mobius(p):
    z = 1
    for b in p:
        z *= (-1)**(len(b)-1)*factorial(len(b)-1)
    return z

def contraction_key(r,c):
    """Canonical bipartite multigraph, invariant under either index renaming."""
    a = [[len(set(x)&set(y)) for y in c] for x in r]
    if not a:
        return ()
    # Enumerate row order and sort columns lexicographically for that order.
    return min(tuple(sorted(tuple(a[i][j] for i in order)
                            for j in range(len(c))))
               for order in permutations(range(len(r))))

def centered_contractions(k, pair_budget=100000):
    """Coefficients of k! M_k after singleton cancellation, grouped by shape."""
    ps = list(partitions(k))
    if len(ps)**2 > pair_budget:
        raise OverflowError("contraction pair budget")
    out = Counter()
    for r in ps:
        for c in ps:
            out[contraction_key(r,c)] += mobius(r)*mobius(c)
    return dict((key,v) for key,v in out.items() if v)

def matching_coefficients(rows, state_budget=100000):
    """All weighted matching sums by row deletion, rectangular and signed."""
    a = tuple(tuple(Q(x) for x in r) for r in rows)
    n = len(a[0]) if a else 0
    if any(len(r)!=n for r in a) or len(a)>60 or n>60:
        raise ValueError("rectangular matrix required; finite size limit")
    visited = 0
    @lru_cache(None)
    def f(i, used):
        nonlocal visited
        visited += 1
        if visited > state_budget:
            raise OverflowError("matching state budget")
        if i == len(a):
            return (Q(1),)
        out = list(f(i+1, used))
        for j,x in enumerate(a[i]):
            if x and not (used >> j)&1:
                child = f(i+1, used | (1<<j))
                out.extend([Q(0)]*max(0,len(child)+1-len(out)))
                for k,v in enumerate(child):
                    out[k+1] += x*v
        return tuple(out)
    coeff = list(f(0,0))
    coeff.extend([Q(0)]*(min(len(a),n)+1-len(coeff)))
    return coeff

def recurrence_residual(rows):
    """Independent decomposition at the first row; exact finite diagnostic."""
    a = [list(map(Q,r)) for r in rows]
    if not a:
        return [Q(0)]
    full = matching_coefficients(a)
    out = full[:]
    for k,v in enumerate(matching_coefficients(a[1:])):
        out[k] -= v
    for j,x in enumerate(a[0]):
        minor = [r[:j]+r[j+1:] for r in a[1:]]
        for k,v in enumerate(matching_coefficients(minor)):
            out[k+1] -= x*v
    return out


def shape_coefficient(columns,permutation_budget=100000):
    """Coefficient of a single centered contraction at arbitrary edge order.

    Each column is a tuple of multiplicities; rows and columns are unnamed.
    The number of labeled pairs of partitions yielding this shape equals
    k! / (product(entry!) * |Aut_bipartite(shape)|).
    Both singleton-free degree constraints and multiplicities are checked.
    """
    if not columns:
        return 1
    r=len(columns[0]);c=len(columns)
    if not r or any(len(col)!=r for col in columns) or any(type(x) is not int or x<0 for col in columns for x in col):
        raise ValueError("invalid shape")
    rd=[sum(col[i] for col in columns) for i in range(r)]
    cd=[sum(col) for col in columns]
    if min(rd+cd)<2:
        return 0
    k=sum(rd)
    if k>10000 or type(permutation_budget) is not int or not 1<=permutation_budget<=1000000:
        raise ValueError("shape resource limit")
    # Transpose so that the smaller side is permuted. Only permutations
    # preserving the degree of every vertex can be automorphisms.
    if r>c:
        columns=tuple(tuple(col[i] for col in columns) for i in range(r))
        r,c=c,r
        rd,cd=cd,rd
    columns=tuple(tuple(col) for col in columns)
    groups={}
    for i,d in enumerate(rd):
        groups.setdefault(d,[]).append(i)
    group_lists=list(groups.values())
    count=1
    for g in group_lists:
        count*=factorial(len(g))
        if count>permutation_budget:
            raise OverflowError("automorphism budget")
    from itertools import product
    target=Counter(columns)
    row_automorphisms=0
    for perm in product(*(permutations(g) for g in group_lists)):
        order=list(range(r))
        for g,p in zip(group_lists,perm):
            for i,j in zip(g,p):
                order[i]=j
        if Counter(tuple(col[i] for i in order) for col in columns)==target:
            row_automorphisms+=1
    aut=row_automorphisms
    for multiplicity in target.values():
        aut*=factorial(multiplicity)
    divisor=aut
    for col in columns:
        for x in col:
            divisor*=factorial(x)
    labeled,remainder=divmod(factorial(k),divisor)
    if remainder:
        raise ArithmeticError("noninteger orbit size")
    sign=1
    for d in rd+cd:
        sign*=(-1)**(d-1)*factorial(d-1)
    return labeled*sign
