"""Dimension-free weighted tensor squares with structural zero marginals."""
import json
from itertools import combinations,product
import random
from fractions import Fraction as Q
import indexed_algebra as ia
from affine import rational
from runtime import strict_json
from rational_cone import solve as cone
PREFIX='Constrained tensor inequality: '

def normalize(s):
    if not isinstance(s,dict) or set(s)!={'tensors','terms','nonnegative','centered'}:raise ValueError('claim')
    a=ia.normalize({k:s[k] for k in ('tensors','terms')});ts=a['tensors']
    nn=s['nonnegative'];zz=s['centered']
    if not isinstance(nn,list) or any(not isinstance(x,str) or x not in ts or ts[x]['symmetry']=='alternating' for x in nn) or len(set(nn))!=len(nn):raise ValueError('nonnegative symbols')
    if not isinstance(zz,dict) or any(x not in ts or ts[x]['symmetry']!='none' for x in zz):raise ValueError('centered symbols')
    for x,slots in zz.items():
        if not isinstance(slots,list) or not slots or any(type(i) is not int or not 0<=i<ts[x]['rank'] for i in slots) or len(set(slots))!=len(slots):raise ValueError('centered slots')
    return dict(a,nonnegative=sorted(nn),centered={x:sorted(v) for x,v in sorted(zz.items())})

def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))
def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('not constrained tensor')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical tensor')
    return s
def context(s):return {k:s[k] for k in ('tensors','nonnegative','centered')}
def normal(s,terms=None):
    s=normalize(s);ts=s['tensors'];out={}
    raw=ia.normalize(dict(tensors=ts,terms=s['terms'] if terms is None else terms))['terms']
    key=tuple((name,t['symmetry']) for name,t in ts.items())
    for t in raw:
        power,fs=ia.eliminate_deltas(t,ts)
        occ={}
        for name,ix in fs:
            for j,i in enumerate(ix):occ.setdefault(i,[]).append((name,j))
        # Sum over a singleton binder in a declared zero marginal.
        if any(len(v)==1 and v[0][1] in s['centered'].get(v[0][0],[]) for v in occ.values()):continue
        k,sign=ia.canonical(key,fs)
        if sign:out[(power,k)]=out.get((power,k),Q(0))+sign*Q(t['coefficient'])
    return {k:v for k,v in out.items() if v}
def inds(fs):return {i for _,ix in fs for i in ix}
def expand(s,atom):
    s=normalize(s);ts=s['tensors']
    if not isinstance(atom,dict) or set(atom)!={'free','power','weight','square'}:raise ValueError('atom')
    free=atom['free'];power=atom['power'];weight=atom['weight'];raw=atom['square']
    if not isinstance(free,list) or any(type(i) is not int or not 0<=i<ia.MAX_INDICES for i in free) or len(set(free))!=len(free):raise ValueError('free indices')
    if type(power) is not int or not 0<=power<=8 or not isinstance(raw,list) or not 1<=len(raw)<=4:raise ValueError('atom limits')
    w=ia.normalize(dict(tensors=ts,terms=[dict(coefficient='1',n_power=0,factors=weight)]))['terms'][0]['factors']
    if any(name not in s['nonnegative'] and ts[name]['symmetry']!='delta' for name,_ in w) or not inds(w)<=set(free):raise ValueError('weight not manifestly nonnegative')
    raw=ia.normalize(dict(tensors=ts,terms=raw))['terms'];fixed={i:j for j,i in enumerate(free)};rows=[]
    for a in raw:
        for b in raw:
            used=inds(w);fs=[[name,[fixed[i] for i in ix]] for name,ix in w];m=len(free)
            for t in (a,b):
                ix=inds(t['factors']);used|=ix&set(free);mp=dict(fixed)
                for i in sorted(ix-set(free)):mp[i]=m;m+=1
                fs.extend([name,[mp[i] for i in v]] for name,v in t['factors'])
            if m>ia.MAX_INDICES or len(fs)>ia.MAX_FACTORS:raise ValueError('expanded size')
            rows.append(dict(coefficient=str(Q(a['coefficient'])*Q(b['coefficient'])),n_power=power+a['n_power']+b['n_power']+len(set(free)-used),factors=fs))
    return normal(s,rows)

def term(fs,c=1):return dict(coefficient=str(c),n_power=0,factors=fs)
def atom(free,power,weight,square):return dict(free=sorted(free),power=power,weight=weight,square=square)
def candidates(s,budget=128):
    s=normalize(s);ts=s['tensors'];seen=set();count=0
    for t in sorted(s['terms'],key=lambda t:(Q(t['coefficient'])>=0,len(t['factors']))):
        fs=t['factors'];n=len(fs);nonneg=[i for i,(name,_) in enumerate(fs) if name in s['nonnegative'] or ts[name]['symmetry']=='delta']
        for k in range(len(nonneg)+1):
            for ix in combinations(nonneg,k):
                w=[fs[i] for i in ix];rest=[v for i,v in enumerate(fs) if i not in ix];f=inds(w)
                if not rest:pool=[atom(f,t['n_power'],w,[term([])])]
                else:
                    pool=[]
                    for z in range(len(rest)+1):
                        for ids in combinations(range(len(rest)),z):
                            a=[v for i,v in enumerate(rest) if i in ids];b=[v for i,v in enumerate(rest) if i not in ids]
                            if max(len(a),len(b))>3:continue
                            free=f|(inds(a)&inds(b))
                            pool.extend([atom(free,t['n_power'],w,[term(a)]),atom(free,t['n_power'],w,[term(b)])])
                            for sign in (-1,1):pool.append(atom(free,t['n_power'],w,[term(a),term(b,sign)]))
                for v in pool:
                    sig=json.dumps(v,sort_keys=True)
                    if sig in seen:continue
                    seen.add(sig);count+=1
                    if count>budget:return
                    yield v
def add(total,q,w):
    for k,v in q.items():total[k]=total.get(k,Q(0))+w*v
def clean(q):return {k:v for k,v in q.items() if v}
def point_value(s,cert):
    if set(cert)!={'n','arrays'} or type(cert['n']) is not int or not 1<=cert['n']<=3:raise ValueError('point size')
    n=cert['n'];ts=s['tensors'];raw=cert['arrays'];arrays={}
    if not isinstance(raw,dict) or set(raw)!=set(ts):raise ValueError('array symbols')
    for name,t in ts.items():
        keys=ia.allowed_keys(t,n);v=raw[name]
        if not isinstance(v,list) or len(v)!=len(keys):raise ValueError('array size')
        a=dict(zip(keys,map(rational,v)))
        if name in s['nonnegative'] and any(x<0 for x in a.values()):raise ValueError('negative entry')
        for slot in s['centered'].get(name,[]):
            for rest in product(range(n),repeat=t['rank']-1):
                if sum(a[rest[:slot]+(i,)+rest[slot:]] for i in range(n)):raise ValueError('nonzero marginal')
        arrays[name]=a
    return sum((ia.eval_term(t,ts,n,arrays) for t in s['terms']),Q(0))

def probe(s):
    rng=random.Random(0);ts=s['tensors']
    for k in range(18):
        n=1+k%3;raw={}
        for name,t in ts.items():
            keys=ia.allowed_keys(t,n);nn=name in s['nonnegative'];zz=s['centered'].get(name,[])
            a={ix:Q(0 if nn and zz else rng.randint(0 if nn else -2,2)) for ix in keys}
            for slot in zz:
                # The integer centering operators on distinct slots commute.
                a={ix:n*v-sum(a[ix[:slot]+(j,)+ix[slot+1:]] for j in range(n)) for ix,v in a.items()}
            raw[name]=[str(a[ix]) for ix in keys]
        cert=dict(n=n,arrays=raw)
        if point_value(s,cert)<0 and replay(s,cert)=='refuted':return cert
    return None

def replay(s,cert):
    try:
        s=normalize(s)
        if isinstance(cert,dict) and set(cert)=={'n','arrays'} and len(json.dumps(cert))<=15000:
            return 'refuted' if point_value(s,cert)<0 else None
        if not isinstance(cert,dict) or set(cert)!={'atoms'} or not isinstance(cert['atoms'],list) or len(cert['atoms'])>64 or len(json.dumps(cert))>15000:return None
        total={}
        for row in cert['atoms']:
            if not isinstance(row,list) or len(row)!=2:return None
            w=rational(row[0])
            if w<=0:return None
            add(total,expand(s,row[1]),w)
        return 'proved' if clean(total)==normal(s) else None
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,OverflowError,RecursionError):return None
def pool(s):
    a=[];cols=[]
    for x in candidates(s):
        try:q=expand(s,x)
        except (ValueError,OverflowError):continue
        if q and q not in cols:a.append(x);cols.append(q)
    return a,cols
def solve(s):
    s=normalize(s);witness=probe(s)
    if witness is not None:return dict(status='counterexample',certificate=witness)
    a,cols=pool(s)
    try:w,_=cone(cols,normal(s),pivot_budget=160)
    except ValueError:w=None
    if w is not None:
        c=dict(atoms=[[str(v),x] for x,v in zip(a,w) if v])
        if replay(s,c)=='proved':return dict(status='proved',certificate=c)
    return dict(status='unknown',scope='bounded weighted tensor cone')
def auto_discharge(g,limit=1):
    from deep_invention_dispatch import discharge
    return discharge(g,parse_statement,solve,replay,'constrained-tensor-',limit)
