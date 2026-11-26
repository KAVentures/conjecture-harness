"""Exact rational univariate sign classification by square-free factors and Sturm.

Coefficients are ascending powers. A positive leading coefficient and no
odd-multiplicity roots in the interior of the domain imply nonnegativity.
An odd-multiplicity interior root certifies a sign change, not a sampled point.
"""
from fractions import Fraction as Q

MAX_BITS=4096

def trim(p):
    p=list(p)
    while p and not p[-1]:p.pop()
    if any(v.numerator.bit_length()>MAX_BITS or v.denominator.bit_length()>MAX_BITS for v in p):raise ValueError('coefficient growth limit')
    return p

def monic(p):return trim([x/p[-1] for x in p]) if p else []
def derivative(p):return trim([i*p[i] for i in range(1,len(p))])
def multiply(p,q):
    if not p or not q:return []
    out=[Q(0)]*(len(p)+len(q)-1)
    for i,a in enumerate(p):
        for j,b in enumerate(q):out[i+j]+=a*b
    return trim(out)

def divide(p,q):
    if not q:raise ValueError('division by zero')
    r=trim(p);out=[Q(0)]*max(0,len(r)-len(q)+1)
    while len(r)>=len(q):
        k=len(r)-len(q);a=r[-1]/q[-1];out[k]=a
        for i,b in enumerate(q):r[i+k]-=a*b
        r=trim(r)
    return trim(out),r

def exact_divide(p,q):
    a,r=divide(p,q)
    if r:raise ArithmeticError('nonexact square-free division')
    return a

def gcd(p,q):
    while q:_,r=divide(p,q);p,q=q,r
    return monic(p)

def odd_part(p):
    """Product of monic square-free factors of odd multiplicity (Yun)."""
    f=monic(p)
    if len(f)<=1:return [Q(1)]
    g=gcd(f,derivative(f));w=exact_divide(f,g);i=1;out=[Q(1)]
    while len(w)>1:
        y=gcd(w,g);z=exact_divide(w,y)
        if i%2:out=multiply(out,z)
        w=y;g=exact_divide(g,y);i+=1
        if i>len(f):raise ArithmeticError('square-free decomposition did not terminate')
    if len(g)>1:raise ArithmeticError('incomplete square-free decomposition')
    return out

def sturm(p):
    a=trim(p);b=derivative(a);seq=[a]
    while b:
        seq.append(b);_,r=divide(a,b);a,b=b,trim([-v for v in r])
    return seq

def sign(v):return (v>0)-(v<0)
def boundary_sign(p,where):
    if where=='plus':return sign(p[-1])
    if where=='minus':return sign(p[-1])*(-1)**(len(p)-1)
    if where=='zero-plus':return sign(next(v for v in p if v))
    raise ValueError('boundary')

def variation(seq,where):
    signs=[boundary_sign(p,where) for p in seq]
    return sum(a!=b for a,b in zip(signs,signs[1:]))

def classify(coefficients,domain):
    """Exact classification for rational degree <=8, barring growth limits."""
    if domain not in ('real','nonnegative') or not isinstance(coefficients,(list,tuple)) or len(coefficients)>9:raise ValueError('unsupported sign problem')
    if any(type(x) not in (int,Q) for x in coefficients):raise ValueError('exact coefficients required')
    p=trim([Q(v) for v in coefficients])
    if not p:return dict(outcome='proved',reason='zero-polynomial',odd_roots=0)
    if p[-1]<0:return dict(outcome='refuted',reason='negative-positive-tail',odd_roots=None)
    odd=odd_part(p);seq=sturm(odd)
    lower='minus' if domain=='real' else 'zero-plus'
    count=variation(seq,lower)-variation(seq,'plus')
    if count<0:raise ArithmeticError('negative Sturm root count')
    return dict(outcome='refuted' if count else 'proved',reason='odd-interior-root' if count else 'no-odd-interior-root',odd_roots=count)

def replay(coefficients,domain,cert):
    try:
        if not isinstance(cert,dict) or set(cert)!={'kind','classification'} or cert['kind']!='sturm-sign':return None
        r=classify(coefficients,domain)
        return r['outcome'] if cert['classification']==r else None
    except (ValueError,TypeError,ArithmeticError,KeyError):return None
