"""Canonical index-dependent induction claims and backward invariant invention."""
import json
from fractions import Fraction as Q
from affine import rational
from runtime import strict_json
from inductive_invention import normalize as normalize_data,discover,replay as replay_induction,pullback,initial
from discovery import check,frontier,record,fingerprint

PREFIX='Index-dependent affine recurrence inequality: '

def decode(s):
    if not isinstance(s,dict) or set(s)!={'matrix','offset','initial','goal'}:
        raise ValueError('claim shape')
    def p(a):
        if not isinstance(a,list):
            raise ValueError('polynomial list')
        return [rational(v) for v in a]
    M=[[p(v) for v in r] for r in s['matrix']]
    b=[p(v) for v in s['offset']]
    x=[rational(v) for v in s['initial']]
    c=[p(v) for v in s['goal']]
    return normalize_data(M,b,x,[c])

def encode(p):
    return [str(v) for v in p]

def normalize(s):
    M,b,x,c=decode(s)
    return dict(matrix=[[encode(v) for v in r] for r in M],offset=[encode(v) for v in b],
                initial=encode(x),goal=[encode(v) for v in c[0]])

def statement(s):
    return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))

def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):
        raise ValueError('wrong statement type')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:
        raise ValueError('noncanonical statement')
    return s

def replay(s,cert):
    try:
        M,b,x,c=decode(s)
        if not isinstance(cert,dict) or set(cert)!={'auxiliary','steps'} or not isinstance(cert['auxiliary'],list) or len(cert['auxiliary'])>11:
            return None
        claims=c+[[[rational(v) for v in p] for p in a] for a in cert['auxiliary']]
        steps=[[(i,k,rational(w)) for i,k,w in step] for step in cert['steps']]
        return 'proved' if replay_induction(M,b,x,claims,steps) else None
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError):
        return None

def solve(s,budget=20):
    if type(budget) is not int or not 1<=budget<=64:
        raise ValueError('attempt budget')
    M,b,x,c=decode(s);d=len(x);attempts=0
    goal=c[0]
    def trial(claims):
        nonlocal attempts
        if attempts>=budget:
            return None
        attempts+=1
        try:r=discover(M,b,x,claims,degree=2)
        except (ValueError,ArithmeticError):return None
        if r is None:
            return None
        cert=dict(auxiliary=[[encode(p) for p in a] for a in claims[1:]],
                  steps=[[[i,k,str(w)] for i,k,w in step] for step in r])
        if replay(s,cert)=='proved' and len(json.dumps(cert))<=15000:
            return dict(status='proved',certificate=cert,attempts=attempts)
        return None
    r=trial(c)
    if r:return r
    # Backward pullbacks can expose a hidden invariant. Coordinate and
    # pairwise difference candidates supply cheap auxiliary state relations.
    pool=[]
    def propose(a):
        if a!=goal and a not in pool and len(a)==d+1 and all(len(p)<=7 for p in a) and initial(a,x)>=0:
            pool.append(a)
    for i in range(d):
        for sign in (1,-1):
            a=[() for _ in range(d+1)];a[i+1]=(Q(sign),);propose(a)
    for i in range(d):
        for j in range(d):
            if i!=j:
                a=[() for _ in range(d+1)];a[i+1]=(Q(1),);a[j+1]=(Q(-1),);propose(a)
    a=goal
    for _ in range(3):
        try:a=pullback(M,b,a)
        except ValueError:break
        propose(a)
    # First test groups so coupled invariants are not starved by singleton search.
    for group in (pool[:11],pool[-11:]):
        if group:
            r=trial([goal]+group)
            if r:return r
    for a in pool:
        if attempts>=budget:break
        r=trial([goal,a])
        if r:return r
    return dict(status='unknown',attempts=attempts,scope='bounded auxiliary invariant invention')

def auto_discharge(g,limit=1):
    check(g);count=0
    for i in frontier(g):
        if count>=limit:break
        if i not in frontier(g):continue
        try:s=parse_statement(g['nodes'][i]['statement'])
        except (ValueError,TypeError):continue
        if any(o['focus']==i and oid.startswith('inductive-invention-') for oid,o in g['observations'].items()):continue
        r=solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True)
        oid='inductive-invention-'+fingerprint(i+'\n'+detail)[:32]
        ops=[dict(op='observe',id=oid,focus=i,kind='proof_sketch' if status=='proved' else 'experiment',detail=detail)]
        if status=='proved':
            ops.append(dict(op='review_claim',id=i,decision='established',evidence='Exact simultaneous induction '+oid))
        g=record(g,'forward',i,ops,trusted=True);count+=1
    return g
