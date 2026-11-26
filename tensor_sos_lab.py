"""Dimension-free sums of squared partially contracted tensor expressions.

A square is summed over its free indices; private indices in its two factors
are renamed independently. Expansion then uses the existing indexed-algebra
normal form. Discovery is bounded; replay proves the exact inequality for
every positive integer dimension and every allowed real tensor.
"""
import json
from itertools import combinations
from fractions import Fraction as Q
import indexed_algebra as ia
from affine import rational
from runtime import strict_json
from rational_cone import solve as cone_solve
from discovery import check,frontier,record,fingerprint

PREFIX='Indexed tensor nonnegativity: '

def statement(s):
    return PREFIX+json.dumps(ia.normalize(s),sort_keys=True,separators=(',',':'))

def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):
        raise ValueError('wrong statement type')
    s=ia.normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:
        raise ValueError('noncanonical statement')
    return s

def indices(t):
    return {i for _,ix in t['factors'] for i in ix}

def expanded(tensors,square):
    if not isinstance(square,dict) or set(square)!={'free','outer_power','terms'}:
        raise ValueError('square shape')
    free=square['free'];power=square['outer_power'];raw=square['terms']
    if not isinstance(free,list) or len(free)>ia.MAX_INDICES or any(type(i) is not int or not 0<=i<ia.MAX_INDICES for i in free) or len(set(free))!=len(free):
        raise ValueError('free indices')
    if type(power) is not int or not 0<=power<=8 or not isinstance(raw,list) or not 1<=len(raw)<=6:
        raise ValueError('square limits')
    terms=ia.normalize({'tensors':tensors,'terms':raw})['terms']
    out=[]
    fixed={i:j for j,i in enumerate(free)}
    for a in terms:
        for b in terms:
            m=len(free);factors=[];used_free=set()
            for t in (a,b):
                used=indices(t);used_free.update(used.intersection(free))
                mp=dict(fixed)
                for i in sorted(used-set(free)):
                    mp[i]=m;m+=1
                factors.extend([name,[mp[i] for i in ix]] for name,ix in t['factors'])
            if m>ia.MAX_INDICES or len(factors)>ia.MAX_FACTORS:
                raise ValueError('expanded contraction size')
            # Summing a free index absent from both factors gives n.
            np=power+a['n_power']+b['n_power']+len(free)-len(used_free)
            out.append(dict(coefficient=str(Q(a['coefficient'])*Q(b['coefficient'])),n_power=np,factors=factors))
    return ia.normalize({'tensors':tensors,'terms':out})

def column(ts,sq):
    return ia.normal_form(expanded(ts,sq))

def replay(s,cert):
    try:
        s=ia.normalize(s)
        if isinstance(cert,dict) and set(cert)=={'n','arrays'}:
            n=cert['n'];raw=cert['arrays'];ts=s['tensors']
            if type(n) is not int or not 1<=n<=3 or not isinstance(raw,dict) or set(raw)!=set(ts):
                return None
            arrays={}
            for name,t in ts.items():
                keys=ia.allowed_keys(t,n);vals=raw[name]
                if not isinstance(vals,list) or len(vals)!=len(keys):
                    return None
                arrays[name]=dict(zip(keys,map(rational,vals)))
            v=sum(ia.eval_term(t,ts,n,arrays) for t in s['terms'])
            return 'refuted' if v<0 else None
        if not isinstance(cert,dict) or set(cert)!={'squares'} or not isinstance(cert['squares'],list) or len(cert['squares'])>64:
            return None
        total={}
        for row in cert['squares']:
            if not isinstance(row,list) or len(row)!=2:
                return None
            w=rational(row[0])
            if w<=0:
                return None
            for k,v in column(s['tensors'],row[1]).items():
                total[k]=total.get(k,Q(0))+w*v
        return 'proved' if {k:v for k,v in total.items() if v}==ia.normal_form(s) else None
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,OverflowError):
        return None

def atom(fs,sign=1):
    return dict(coefficient=str(sign),n_power=0,factors=fs)

def candidates(s,budget):
    seen=set();count=0
    def make(free,terms,power):
        return dict(free=sorted(free),outer_power=power,terms=terms)
    # Negative cross terms are useful hints for a binomial square. Factor
    # bipartitions include both symmetric and asymmetric private contractions.
    for t in sorted(s['terms'],key=lambda t:(Q(t['coefficient'])>=0,len(t['factors']))):
        fs=t['factors'];n=len(fs)
        if not n:
            pool=[make([], [atom([])],t['n_power'])]
        else:
            pool=[]
            for size in range(1,min(3,n)+1):
                for ix in combinations(range(n),size):
                    a=atom([fs[i] for i in ix]);b=atom([fs[i] for i in range(n) if i not in ix])
                    if len(b['factors'])>3:
                        continue
                    free=indices(a)&indices(b)
                    pool.append(make(free,[a],t['n_power']))
                    pool.append(make(free,[b],t['n_power']))
                    for sign in (-1,1):
                        pool.append(make(free,[a,dict(b,coefficient=str(sign))],t['n_power']))
        for sq in pool:
            key=json.dumps(sq,sort_keys=True)
            if key in seen:
                continue
            seen.add(key);count+=1
            if count>budget:
                return
            yield sq

def solve(s,budget=128):
    s=ia.normalize(s)
    if type(budget) is not int or not 1<=budget<=256:
        raise ValueError('candidate budget')
    target=ia.normal_form(s)
    if not target:
        return dict(status='proved',certificate={'squares':[]},tested=0)
    # Deterministic exact probes over small tensor arrays. Finite survival
    # never enters a proof certificate.
    import random
    rng=random.Random(0)
    for i in range(12):
        n=1+i%3
        arrays={name:[str(1 if i<3 else rng.randint(-2,2)) for _ in ia.allowed_keys(t,n)]
                for name,t in s['tensors'].items()}
        cert=dict(n=n,arrays=arrays)
        if replay(s,cert)=='refuted':
            return dict(status='counterexample',certificate=cert,tested=0)
    cols=[];sqs=[];seen=set();tested=0
    for sq in candidates(s,budget):
        tested+=1
        try:c=column(s['tensors'],sq)
        except ValueError:continue
        key=tuple(sorted(c.items()))
        if c and key not in seen:
            seen.add(key);cols.append(c);sqs.append(sq)
    try:weights,_=cone_solve(cols,target)
    except ValueError:weights=None
    if weights is not None:
        cert={'squares':[[str(w),sq] for w,sq in zip(weights,sqs) if w]}
        if len(json.dumps(cert))<=15000 and replay(s,cert)=='proved':
            return dict(status='proved',certificate=cert,tested=tested)
    return dict(status='unknown',tested=tested,scope='bounded contraction square search')

def auto_discharge(g,limit=1):
    check(g);count=0
    for i in frontier(g):
        if count>=limit:break
        if i not in frontier(g):continue
        try:s=parse_statement(g['nodes'][i]['statement'])
        except (ValueError,TypeError):continue
        if any(o['focus']==i and oid.startswith('tensor-sos-') for oid,o in g['observations'].items()):continue
        r=solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True)
        oid='tensor-sos-'+fingerprint(i+'\n'+detail)[:32]
        ops=[dict(op='observe',id=oid,focus=i,kind={'proved':'proof_sketch','counterexample':'counterexample','unknown':'experiment'}[status],detail=detail)]
        if status=='proved':
            ops.append(dict(op='review_claim',id=i,decision='established',evidence='Exact summed tensor squares '+oid))
        elif status=='counterexample':
            ops.append(dict(op='review_claim',id=i,decision='refuted',evidence='Exact negative tensor evaluation '+oid))
        g=record(g,'falsify' if status=='counterexample' else 'forward',i,ops,trusted=True);count+=1
    return g
