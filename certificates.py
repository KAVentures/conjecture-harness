"""Independent finite certificate replay; no model output is executed."""
from itertools import combinations, permutations
from fractions import Fraction as F
from math import prod, factorial


def replay(target, witness, result):
    if target == 'shannon':
        words = witness['words']; n = len(words[0]); m = len(words)
        masks = [sum(1 << i for i in pair) for pair in combinations(range(5), 2)]
        valid = len({tuple(w) for w in words}) == m and all(
            any(not (masks[x] & masks[y]) for x,y in zip(a,b)) for a,b in combinations(words,2))
        return {'replayed': valid and result['n']==n and result['size']==m and result['beats_cuberoot_12']==(m**3>12**n),
                'method':'independent bitmask pair check'}
    if target == 'lih-wang':
        a = [[F(x) for x in r] for r in witness['matrix']]; n = len(a); t = F(witness['t'])
        if n > 8: return {'replayed':False,'method':'permutation expansion limited to n<=8'}
        if not (F(1,2)<=t<=1 and all(sum(r)==1 for r in a) and all(sum(c)==1 for c in zip(*a)) and all(x>=0 for r in a for x in r)):
            return {'replayed':False,'method':'invalid instance'}
        def perm(m):
            return sum((prod(m[i][p[i]] for i in range(n)) for p in permutations(range(n))), F(0))
        b=[[t/n+(1-t)*x for x in r] for r in a]
        gap=perm(b)-t*F(factorial(n),n**n)-(1-t)*perm(a)
        return {'replayed':str(gap)==result['lhs_minus_rhs'] and (gap>0)==result['verified_counterexample'],
                'method':'independent permutation expansion and factorial formula'}
    return {'replayed':False,'method':'no registered independent checker'}
