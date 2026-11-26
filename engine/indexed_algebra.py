"""Dimension-free tensor contraction identities via alpha-renaming and symmetry.

A tensor symbol denotes an arbitrary real array with a common index range
1..n in each slot. All indices are summed independently; unused binders are
represented explicitly by n_power. No finite-dimensional test proves an
all-dimension identity. The normalizer is deliberately incomplete.
"""
import itertools,json,re
from fractions import Fraction as Q
from functools import lru_cache
from affine import rational
from runtime import strict_json

PREFIX='Indexed tensor identity: '
MAX_INDICES=5
MAX_FACTORS=6

def normalize(s):
    if not isinstance(s,dict) or set(s)!={'tensors','terms'}:raise ValueError('indexed claim shape')
    ts=s['tensors']
    if not isinstance(ts,dict) or not 1<=len(ts)<=6:raise ValueError('tensor count')
    tensors={}
    for name,t in sorted(ts.items()):
        if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,15}',name) or not isinstance(t,dict) or set(t)!={'rank','symmetry'}:raise ValueError('tensor declaration')
        r=t['rank'];sym=t['symmetry']
        if type(r) is not int or not 1<=r<=3 or sym not in ('none','symmetric','alternating','delta') or (sym=='delta' and r!=2):raise ValueError('tensor rank/symmetry')
        tensors[name]=dict(rank=r,symmetry=sym)
    rows=s['terms']
    if not isinstance(rows,list) or len(rows)>48:raise ValueError('term count')
    out=[]
    for t in rows:
        if not isinstance(t,dict) or set(t)!={'coefficient','n_power','factors'}:raise ValueError('term shape')
        c=str(rational(t['coefficient']));power=t['n_power'];fs=t['factors']
        if type(power) is not int or not 0<=power<=8 or not isinstance(fs,list) or len(fs)>MAX_FACTORS:raise ValueError('factor or dimension power limit')
        factors=[];used=set()
        for v in fs:
            if not isinstance(v,list) or len(v)!=2 or not isinstance(v[0],str) or v[0] not in tensors:raise ValueError('factor')
            name,ix=v
            if not isinstance(ix,list) or len(ix)!=tensors[name]['rank'] or any(type(i) is not int or not 0<=i<MAX_INDICES for i in ix):raise ValueError('indices')
            used.update(ix);factors.append([name,ix])
        if len(used)>MAX_INDICES:raise ValueError('index count')
        out.append(dict(coefficient=c,n_power=power,factors=factors))
    return dict(tensors=tensors,terms=out)

def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))
def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('not indexed identity')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical indexed identity')
    return s

def sign(xs):return -1 if sum(a>b for i,a in enumerate(xs) for b in xs[i+1:])%2 else 1

@lru_cache(maxsize=1024)
def canonical(tensor_key,factors):
    """Minimize over all dummy-index renamings; detect odd automorphisms."""
    ts=dict(tensor_key);used=sorted({i for _,ix in factors for i in ix})
    best=None;signs=set()
    for perm in itertools.permutations(range(len(used))):
        mp=dict(zip(used,perm));fs=[];sgn=1
        for name,ix in factors:
            v=tuple(mp[i] for i in ix);sym=ts[name]
            if sym=='alternating':
                if len(set(v))!=len(v):return None,0
                sgn*=sign(v);v=tuple(sorted(v))
            elif sym=='symmetric':v=tuple(sorted(v))
            fs.append((name,v))
        key=tuple(sorted(fs))
        if best is None or key<best:best=key;signs={sgn}
        elif key==best:signs.add(sgn)
    if len(signs)>1:return None,0
    return best,next(iter(signs))

def eliminate_deltas(t,ts):
    """Sum equality indicators by union-find; isolated classes contribute n."""
    factors=t['factors'];used={i for _,ix in factors for i in ix}
    parent={i:i for i in used}
    def find(i):
        while parent[i]!=i:i=parent[i]
        return i
    for name,ix in factors:
        if ts[name]['symmetry']=='delta':
            i,j=map(find,ix)
            if i!=j:parent[max(i,j)]=min(i,j)
    remaining=tuple((name,tuple(find(i) for i in ix)) for name,ix in factors if ts[name]['symmetry']!='delta')
    classes={find(i) for i in used};live={i for _,ix in remaining for i in ix}
    return t['n_power']+len(classes-live),remaining

def normal_form(s):
    s=normalize(s);tk=tuple((name,t['symmetry']) for name,t in s['tensors'].items());out={}
    for t in s['terms']:
        power,fs=eliminate_deltas(t,s['tensors'])
        k,sgn=canonical(tk,fs)
        if not sgn:continue
        key=(power,k)
        out[key]=out.get(key,Q(0))+sgn*Q(t['coefficient'])
    return {k:v for k,v in out.items() if v}

def eval_term(t,ts,n,arrays):
    fs=t['factors'];used=sorted({i for _,ix in fs for i in ix})
    total=Q(0)
    for indices in itertools.product(range(n),repeat=len(used)):
        mp=dict(zip(used,indices));v=Q(1)
        for name,ix in fs:
            key=tuple(mp[i] for i in ix);sym=ts[name]['symmetry']
            if sym=='delta':
                if key[0]!=key[1]:v=Q(0);break
                continue
            if sym=='alternating':
                if len(set(key))!=len(key):v=Q(0);break
                v*=sign(key);key=tuple(sorted(key))
            elif sym=='symmetric':key=tuple(sorted(key))
            v*=arrays[name].get(key,Q(0))
            if not v:break
        total+=v
    return Q(t['coefficient'])*n**t['n_power']*total

def allowed_keys(t,n):
    r=t['rank'];sym=t['symmetry']
    if sym=='delta':return []
    if sym=='symmetric':return list(itertools.combinations_with_replacement(range(n),r))
    if sym=='alternating':return list(itertools.combinations(range(n),r))
    return list(itertools.product(range(n),repeat=r))

def replay(s,cert):
    try:
        s=normalize(s)
        if cert=={'kind':'canonical-zero'}:return 'proved' if not normal_form(s) else None
        if not isinstance(cert,dict) or set(cert)!={'kind','n','arrays'} or cert['kind']!='tensor-point':return None
        n=cert['n'];raw=cert['arrays'];ts=s['tensors']
        if type(n) is not int or not 1<=n<=3 or not isinstance(raw,dict) or set(raw)!=set(ts):return None
        arrays={}
        for name,t in ts.items():
            keys=allowed_keys(t,n);vals=raw[name]
            if not isinstance(vals,list) or len(vals)!=len(keys):return None
            arrays[name]=dict(zip(keys,map(rational,vals)))
        return 'refuted' if sum(eval_term(t,ts,n,arrays) for t in s['terms']) else None
    except (ValueError,TypeError,KeyError,ArithmeticError,AttributeError):return None

def solve(s,budget=24,seed=0):
    import random
    s=normalize(s)
    if type(budget) is not int or not 1<=budget<=64 or type(seed) is not int:raise ValueError('search limits')
    if not normal_form(s):return dict(status='proved',certificate={'kind':'canonical-zero'},tested=0)
    rng=random.Random(seed)
    for i in range(budget):
        n=1+i%3
        arrays={name:[str(rng.randint(-2,2)) for _ in allowed_keys(t,n)] for name,t in s['tensors'].items()}
        cert=dict(kind='tensor-point',n=n,arrays=arrays)
        if replay(s,cert)=='refuted':return dict(status='counterexample',certificate=cert,tested=i+1)
    return dict(status='unknown',tested=budget,scope='normal form incomplete; finite survival is not proof')

def main():
    import argparse
    from runtime import read_json
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('spec');p.add_argument('--budget',type=int,default=24);p.add_argument('--seed',type=int,default=0);a=p.parse_args()
    print(json.dumps(solve(read_json(a.spec),a.budget,a.seed),indent=2))
if __name__=='__main__':main()
