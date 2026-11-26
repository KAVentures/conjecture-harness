"""Exact bounded counterexample search for a small, declarative graph language.
No eval, generated code or claim of proof from finite survival.
"""
import argparse, itertools, json, math
from runtime import read_json

FIELDS = ('n','m','alpha','omega','delta','Delta')
PROPS = ('connected','triangle_free')


def validate(spec):
    if not isinstance(spec,dict) or set(spec)!={'min_n','properties','coefficients','constant'}:
        raise ValueError('invalid graph lemma schema')
    n=spec['min_n']; p=spec['properties']; c=spec['coefficients']; b=spec['constant']
    if type(n) is not int or not 1<=n<=100: raise ValueError('invalid minimum order')
    if not isinstance(p,list) or any(x not in PROPS for x in p) or len(set(p))!=len(p): raise ValueError('invalid properties')
    if not isinstance(c,dict) or not c or any(k not in FIELDS or type(v) is not int or not -1000<=v<=1000 or v==0 for k,v in c.items()): raise ValueError('invalid coefficients')
    if type(b) is not int or abs(b)>1000: raise ValueError('invalid constant')
    # Divide out positive common factors; preserve direction.
    d=math.gcd(*c.values(),b)
    return {'min_n':n,'properties':sorted(p),'coefficients':{k:c[k]//d for k in FIELDS if k in c},'constant':b//d}


def statement(spec):
    s=validate(spec)
    terms=' + '.join(f'({v})*{k}' for k,v in s['coefficients'].items())
    props=', '.join(s['properties']) or 'none'
    return f'For every finite simple undirected graph with n >= {s["min_n"]} and required properties [{props}], {terms} >= {s["constant"]}. Here n is order, m is size, alpha is independence number, omega is clique number, delta is minimum degree and Delta is maximum degree.'


def properties(n, edges):
    if type(n) is not int or not 1<=n<=6 or not isinstance(edges,list): raise ValueError('witness order must be 1..6')
    a=[0]*n
    for e in edges:
        if not isinstance(e,list) or len(e)!=2 or any(type(v) is not int for v in e): raise ValueError('invalid edge')
        u,v=e
        if not 0<=u<v<n or a[u]>>v&1: raise ValueError('noncanonical or duplicate edge')
        a[u]|=1<<v; a[v]|=1<<u
    seen=1
    while True:
        more=seen
        for i in range(n):
            if seen>>i&1: more|=a[i]
        if more==seen: break
        seen=more
    alpha=omega=0
    for mask in range(1,1<<n):
        size=mask.bit_count()
        if all(not (a[i]&mask) for i in range(n) if mask>>i&1): alpha=max(alpha,size)
        if all((a[i]&mask).bit_count()==size-1 for i in range(n) if mask>>i&1): omega=max(omega,size)
    ds=[v.bit_count() for v in a]
    return {'n':n,'m':len(edges),'alpha':alpha,'omega':omega,'delta':min(ds),'Delta':max(ds),'connected':seen==(1<<n)-1,'triangle_free':omega<3}


def independent(n,edges):
    # Separate set-based implementation; called only on validated witnesses.
    es={tuple(e) for e in edges}; sets=[set() for _ in range(n)]
    for u,v in es: sets[u].add(v); sets[v].add(u)
    reached={0}
    for _ in range(n): reached|=set().union(*(sets[i] for i in reached))
    alpha=omega=0
    for k in range(1,n+1):
        for vs in itertools.combinations(range(n),k):
            pairs=list(itertools.combinations(vs,2))
            if not any(e in es for e in pairs): alpha=k
            if all(e in es for e in pairs): omega=k
    ds=list(map(len,sets))
    return dict(n=n,m=len(es),alpha=alpha,omega=omega,delta=min(ds),Delta=max(ds),connected=len(reached)==n,triangle_free=omega<3)


def replay(spec,witness):
    s=validate(spec)
    if not isinstance(witness,dict) or set(witness)!={'n','edges'}: raise ValueError('invalid witness')
    n=witness['n']; e=witness['edges']; p=properties(n,e)
    if p!=independent(n,e): raise ValueError('checker disagreement')
    lhs=sum(p[k]*v for k,v in s['coefficients'].items())
    return {'counterexample':n>=s['min_n'] and all(p[x] for x in s['properties']) and lhs<s['constant'],'invariants':p,'lhs':lhs,'rhs':s['constant']}


def family_masks(n,pairs):
    """Deterministic structural seeds, including complements. No completeness claim."""
    full=(1<<len(pairs))-1
    for predicate in (lambda u,v:False,lambda u,v:True,lambda u,v:u==0,
                      lambda u,v:v==u+1,lambda u,v:v==u+1 or (u==0 and v==n-1),
                      *(lambda u,v,k=k:u<k<=v for k in range(1,n)),
                      *(lambda u,v,k=k:(u<k)==(v<k) for k in range(1,n))):
        mask=sum(1<<i for i,(u,v) in enumerate(pairs) if predicate(u,v))
        yield mask;yield full^mask


def search(spec,max_n=5,budget=40000,strategy='exhaustive'):
    s=validate(spec)
    if type(max_n) is not int or not 1<=max_n<=6 or type(budget) is not int or not 1<=budget<=40000: raise ValueError('bounded search: order <=6, 1..40000 graphs')
    if strategy not in ('exhaustive','families_first'): raise ValueError('unknown search strategy')
    tested=0; eligible=0; complete_through=None
    def result(status,w=None,certificate=None):
        return {'status':status,'spec':s,'statement':statement(s),'strategy':strategy,'tested':tested,'eligible':eligible,'complete_through':complete_through,'witness':w,'replay':certificate,'universal_proof':False}
    for n in range(s['min_n'],max_n+1):
        pairs=list(itertools.combinations(range(n),2))
        seeds=list(dict.fromkeys(family_masks(n,pairs))) if strategy=='families_first' else []
        used=set(seeds)
        for mask in itertools.chain(seeds,(m for m in range(1<<len(pairs)) if m not in used)):
            if tested>=budget: return result('budget_exhausted')
            edges=[list(e) for i,e in enumerate(pairs) if mask>>i&1]; tested+=1
            p=properties(n,edges)
            if not all(p[x] for x in s['properties']): continue
            eligible+=1
            if sum(p[k]*v for k,v in s['coefficients'].items())<s['constant']:
                w={'n':n,'edges':edges}; cert=replay(s,w)
                if not cert['counterexample']: raise ValueError('checker disagreement')
                return result('counterexample',w,cert)
        complete_through=n
    return result('no_counterexample_in_scope' if tested else 'empty_scope')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('spec');p.add_argument('--max-n',type=int,default=5);p.add_argument('--budget',type=int,default=40000);p.add_argument('--replay');p.add_argument('--strategy',choices=['exhaustive','families_first'],default='exhaustive');a=p.parse_args()
    s=read_json(a.spec);print(json.dumps(replay(s,read_json(a.replay)) if a.replay else search(s,a.max_n,a.budget,a.strategy),indent=2))
if __name__=='__main__':main()
