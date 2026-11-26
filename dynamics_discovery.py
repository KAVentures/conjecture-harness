"""Exact recurrence and invariant discovery for rational polynomial dynamical systems.

A finite symbolic Krylov relation implies a recurrence for every iterate and
every real initial state. Candidate invariant bases are checked by substitution.
Unsupported degree growth or a failed search is unknown, never a proof.
"""
import itertools,json,re
from fractions import Fraction as Q
from affine import rational
from runtime import strict_json
from representation_transfer import constant,mul,power
from symbolic_discovery import terms,encode,add,evaluate

PREFIX='Polynomial dynamics claim: '
MAX_ORDER=6
MAX_DEGREE=8

def system(s):
    if not isinstance(s,dict) or set(s)!={'variables','transition'}:raise ValueError('system shape')
    vs=s['variables'];ts=s['transition']
    if not isinstance(vs,list) or not 1<=len(vs)<=4 or any(not isinstance(v,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,15}',v) for v in vs) or len(set(vs))!=len(vs):raise ValueError('variables')
    if not isinstance(ts,list) or len(ts)!=len(vs):raise ValueError('transition shape')
    return dict(variables=vs,transition=[encode(terms(t,len(vs),2)) for t in ts])

def weights(raw):
    if not isinstance(raw,list) or not 2<=len(raw)<=MAX_ORDER+1:raise ValueError('recurrence order')
    w=list(map(rational,raw))
    if w[-1]!=1:raise ValueError('recurrence must be monic')
    return w

def normalize(s):
    if not isinstance(s,dict) or s.get('kind') not in ('recurrence','orbit-zero'):raise ValueError('claim kind')
    k=s['kind'];common={'kind','variables','transition','observable'}
    if set(s)!=common|({'weights'} if k=='recurrence' else {'initial'}):raise ValueError('claim shape')
    a=system({i:s[i] for i in ('variables','transition')});n=len(a['variables'])
    a.update(kind=k,observable=encode(terms(s['observable'],n,MAX_DEGREE)))
    if k=='recurrence':a['weights']=list(map(str,weights(s['weights'])))
    else:
        if not isinstance(s['initial'],list) or len(s['initial'])!=n:raise ValueError('initial state')
        a['initial']=list(map(str,map(rational,s['initial'])))
    return a

def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))
def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('not dynamics')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical dynamics claim')
    return s

def bounded(p):
    if len(p)>512 or any(sum(e)>MAX_DEGREE or c.numerator.bit_length()>256 or c.denominator.bit_length()>256 for e,c in p.items()):raise ValueError('symbolic growth limit')
    return p

def substitute(p,images):
    n=len(images);out={}
    for e,c in p.items():
        term=constant(n,c)
        for k,img in zip(e,images):
            if k:term=mul(term,power(img,k,n))
            if not term:break
        out=bounded(add(out,term))
    return out

def linear_combination(ps,ws):
    out={}
    for p,w in zip(ps,ws):
        if w:out=bounded(add(out,p,w))
    return out

def iterates(s,order):
    n=len(s['variables']);images=[terms(t,n,2) for t in s['transition']]
    ps=[terms(s['observable'],n,MAX_DEGREE)]
    for _ in range(order):ps.append(substitute(ps[-1],images))
    return ps

def eval_poly(p,x):
    return evaluate(p,x[0],x[1:])

def step(images,x):
    y=[eval_poly(p,x) for p in images]
    if any(v.numerator.bit_length()>512 or v.denominator.bit_length()>512 for v in y):raise ValueError('orbit growth limit')
    return y

def orbit_values(s,initial,count):
    n=len(s['variables']);images=[terms(t,n,2) for t in s['transition']];obs=terms(s['observable'],n,MAX_DEGREE)
    x=list(initial);out=[]
    for i in range(count):
        v=eval_poly(obs,x)
        if v.numerator.bit_length()>4096 or v.denominator.bit_length()>4096:raise ValueError('observable growth limit')
        out.append(v)
        if i+1<count:x=step(images,x)
    return out

def nullspace(columns):
    """Exact reduced row echelon nullspace; columns are sparse polynomials."""
    if not columns:return []
    k=len(columns);es=sorted(set().union(*(set(p) for p in columns)))
    if k>40 or len(es)>512:raise ValueError('linear system limit')
    a=[[p.get(e,Q(0)) for p in columns] for e in es]
    pivots=[];rank=0
    for j in range(k):
        at=next((i for i in range(rank,len(a)) if a[i][j]),None)
        if at is None:continue
        a[rank],a[at]=a[at],a[rank];v=a[rank][j];a[rank]=[x/v for x in a[rank]]
        for i in range(len(a)):
            if i==rank:continue
            v=a[i][j]
            if v:a[i]=[x-v*y for x,y in zip(a[i],a[rank])]
        if any(x.numerator.bit_length()>256 or x.denominator.bit_length()>256 for r in a for x in r):raise ValueError('elimination growth limit')
        pivots.append(j);rank+=1
    result=[]
    for j in range(k):
        if j in pivots:continue
        w=[Q(0)]*k;w[j]=Q(1)
        for i,p in enumerate(pivots):w[p]=-a[i][j]
        result.append(w)
    return result

def recurrence(s,max_order=MAX_ORDER):
    """Find a monic annihilating polynomial for the observable under substitution."""
    if type(max_order) is not int or not 1<=max_order<=MAX_ORDER:raise ValueError('order limit')
    n=len(s['variables']);images=[terms(t,n,2) for t in s['transition']];ps=[terms(s['observable'],n,MAX_DEGREE)]
    for _ in range(max_order):
        try:
            ps.append(substitute(ps[-1],images))
            for w in nullspace(ps):
                if not w[-1]:continue
                w=[v/w[-1] for v in w]
                if not linear_combination(ps,w) and all(len(str(v))<=80 for v in w):return list(map(str,w))
        except ValueError:break
    return None

def replay(s,cert):
    """Replay the global identity and (if needed) the exact initial conditions."""
    try:
        s=normalize(s);n=len(s['variables'])
        if not isinstance(cert,dict):return None
        if cert.get('kind')=='recurrence-identity' and set(cert)=={'kind','weights'}:
            ws=weights(cert['weights']);order=len(ws)-1
            if s['kind']=='recurrence' and list(map(str,ws))!=s['weights']:return None
            if linear_combination(iterates(s,order),ws):return None
            if s['kind']=='orbit-zero' and any(orbit_values(s,list(map(Q,s['initial'])),order)):return None
            return 'proved'
        if cert.get('kind')=='initial-witness' and set(cert)=={'kind','initial'} and s['kind']=='recurrence':
            x=cert['initial']
            if not isinstance(x,list) or len(x)!=n:return None
            x=list(map(rational,x));ws=list(map(Q,s['weights']))
            return 'refuted' if sum(w*v for w,v in zip(ws,orbit_values(s,x,len(ws)))) else None
        if cert.get('kind')=='orbit-witness' and set(cert)=={'kind','index'} and s['kind']=='orbit-zero':
            j=cert['index']
            if type(j) is not int or not 0<=j<=16:return None
            return 'refuted' if orbit_values(s,list(map(Q,s['initial'])),j+1)[-1] else None
    except (ValueError,TypeError,KeyError,ArithmeticError,AttributeError):pass
    return None

def solve(s,budget=128):
    s=normalize(s)
    if type(budget) is not int or not 1<=budget<=512:raise ValueError('witness budget')
    ws=s['weights'] if s['kind']=='recurrence' else recurrence(s)
    if ws:
        c=dict(kind='recurrence-identity',weights=ws)
        if replay(s,c)=='proved':return dict(status='proved',certificate=c,tested=0)
    if s['kind']=='orbit-zero':
        candidates=(dict(kind='orbit-witness',index=j) for j in range(17))
    else:
        n=len(s['variables']);grid=('0','1','-1','2','-2','1/2')
        candidates=(dict(kind='initial-witness',initial=list(x)) for x in itertools.product(grid,repeat=n))
    tested=0
    for cert in candidates:
        if tested>=budget:break
        tested+=1
        if replay(s,cert)=='refuted':return dict(status='counterexample',certificate=cert,tested=tested)
    return dict(status='unknown',tested=tested,scope='bounded symbolic degree/order and rational witness search')

def invariant_basis(s,degree=2):
    """Find all polynomial invariants in the selected degree space, modulo constants.

    Complete for this degree if the bounded symbolic expansion/elimination
    succeeds; this is not a classification of arbitrary-degree invariants.
    """
    s=system(s);n=len(s['variables'])
    if type(degree) is not int or not 1<=degree<=3:raise ValueError('invariant degree')
    images=[terms(t,n,2) for t in s['transition']]
    es=[e for e in itertools.product(range(degree+1),repeat=n) if 0<sum(e)<=degree]
    bs=[{e:Q(1)} for e in es]
    try:
        cols=[add(substitute(b,images),b,Q(-1)) for b in bs]
        basis=[]
        for w in nullspace(cols):
            p=linear_combination(bs,w);obs=encode(p)
            claim=dict(s,kind='recurrence',observable=obs,weights=['-1','1'])
            cert=dict(kind='recurrence-identity',weights=['-1','1'])
            if replay(claim,cert)!='proved':raise ArithmeticError('invariant replay failed')
            basis.append(dict(spec=normalize(claim),certificate=cert))
        return dict(status='complete_degree_space',degree=degree,basis=basis)
    except ValueError:return dict(status='unknown',degree=degree,basis=[])

def discover(s,max_order=MAX_ORDER):
    if not isinstance(s,dict) or set(s)!={'variables','transition','observable'}:raise ValueError('discovery shape')
    a=system({k:s[k] for k in ('variables','transition')})
    a['observable']=encode(terms(s['observable'],len(a['variables']),MAX_DEGREE))
    ws=recurrence(a,max_order)
    if ws is None:return dict(status='unknown')
    claim=normalize(dict(a,kind='recurrence',weights=ws));cert=dict(kind='recurrence-identity',weights=ws)
    if replay(claim,cert)!='proved':raise ArithmeticError('recurrence replay failed')
    return dict(status='proved',spec=claim,certificate=cert)

def main():
    import argparse
    from runtime import read_json
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('spec');p.add_argument('--mode',choices=('solve','recurrence','invariants'),default='solve');p.add_argument('--degree',type=int,default=2);p.add_argument('--order',type=int,default=MAX_ORDER);a=p.parse_args()
    s=read_json(a.spec);r=solve(s) if a.mode=='solve' else discover(s,a.order) if a.mode=='recurrence' else invariant_basis(s,a.degree)
    print(json.dumps(r,indent=2))
if __name__=='__main__':main()
