"""Exact certificates for universal implications between rational affine inequalities.
Fourier–Motzkin refutes assumptions plus the strict negation of the conclusion.
Resource exhaustion is unknown, never a counterexample or a proof.
"""
import itertools, json, re
from fractions import Fraction as F

PREFIX='For all real variables, the affine assumptions imply the affine conclusion (each row [constant, coefficients in variable order] is >= 0): '


def rational(x):
    if type(x) not in (int,str) or len(str(x))>80 or not re.fullmatch(r'-?\d+(?:/[1-9]\d*)?',str(x)):
        raise ValueError('exact integer or rational required')
    return F(x)


def normalize(spec):
    if not isinstance(spec,dict) or set(spec)!={'variables','assumptions','conclusion'}:raise ValueError('invalid affine spec')
    vs=spec['variables'];ass=spec['assumptions']
    if not isinstance(vs,list) or not 1<=len(vs)<=6 or any(not isinstance(v,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,15}',v) for v in vs) or len(set(vs))!=len(vs):raise ValueError('invalid variables')
    if not isinstance(ass,list) or len(ass)>12:raise ValueError('at most 12 assumptions')
    def row(r):
        if not isinstance(r,list) or len(r)!=len(vs)+1:raise ValueError('row width mismatch')
        return [str(rational(x)) for x in r]
    return dict(variables=vs,assumptions=[row(r) for r in ass],conclusion=row(spec['conclusion']))


def statement(spec):return PREFIX+json.dumps(normalize(spec),sort_keys=True,separators=(',',':'))


def parse_statement(s):
    if not s.startswith(PREFIX):raise ValueError('not a canonical affine claim')
    spec=json.loads(s[len(PREFIX):])
    if statement(spec)!=s:raise ValueError('noncanonical claim')
    return spec


def rows(spec):
    s=normalize(spec)
    return [tuple(map(F,r)) for r in s['assumptions']]+[tuple(-F(x) for x in s['conclusion'])]


def replay(spec,cert):
    """Check a nonnegative linear combination independently of elimination."""
    rs=rows(spec)
    if not isinstance(cert,dict) or set(cert)!={'multipliers'} or not isinstance(cert['multipliers'],list) or len(cert['multipliers'])!=len(rs):raise ValueError('invalid certificate shape')
    ms=[rational(x) for x in cert['multipliers']]
    if any(m<0 for m in ms):raise ValueError('negative multiplier')
    total=[sum(m*r[j] for m,r in zip(ms,rs)) for j in range(len(rs[0]))]
    return not any(total[1:]) and (total[0]<0 or (total[0]==0 and ms[-1]>0))


def prove(spec,max_pairs=20000):
    if type(max_pairs) is not int or not 1<=max_pairs<=20000:raise ValueError('invalid pair budget')
    rs=rows(spec);k=len(rs);count=0
    live=[(r,tuple(F(i==j) for j in range(k))) for i,r in enumerate(rs)]
    def result(status,cert=None):return {'status':status,'pairs':count,'certificate':cert}
    def contradiction(items):
        for r,m in items:
            if not any(r[1:]) and (r[0]<0 or (r[0]==0 and m[-1]>0)):
                cert={'multipliers':[str(v) for v in m]}
                if any(len(v)>80 for v in cert['multipliers']):return result('budget_exhausted')
                if not replay(spec,cert):raise ArithmeticError('certificate replay failed')
                return result('proved',cert)
    for j in range(1,len(rs[0])):
        hit=contradiction(live)
        if hit:return hit
        pos=[x for x in live if x[0][j]>0];neg=[x for x in live if x[0][j]<0];out=[x for x in live if x[0][j]==0]
        # Deduplicate exact rows, preserving strictness information.
        seen={(r,m[-1]>0) for r,m in out}
        for (a,u),(b,v) in itertools.product(pos,neg):
            if count>=max_pairs:return result('budget_exhausted')
            count+=1;p=-b[j];q=a[j]
            r=tuple(p*x+q*y for x,y in zip(a,b));m=tuple(p*x+q*y for x,y in zip(u,v))
            if any(x.numerator.bit_length()>240 or x.denominator.bit_length()>240 for x in (*r,*m)):return result('budget_exhausted')
            sig=(r,m[-1]>0)
            if sig not in seen:
                seen.add(sig);out.append((r,m))
                hit=contradiction([(r,m)])
                if hit:return hit
                if len(out)>2048:return result('budget_exhausted')
        live=out
    return contradiction(live) or result('not_proved')
