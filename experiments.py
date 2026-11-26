"""Reproducible finite searches. Evidence only, never a general proof."""
import argparse, json, random, time
from itertools import product, permutations
from fractions import Fraction as F
from pathlib import Path
from verify import packing, lih_wang, ALPHABET

DISJ=[[set(a).isdisjoint(b) for b in ALPHABET] for a in ALPHABET]

def clique_search(n,seed,restarts):
    rng=random.Random(seed); words=list(product(range(10),repeat=n)); N=len(words)
    if n>3: raise ValueError('built-in dense search only supports n<=3')
    adj=[]
    for a in words:
        mask=0
        for j,b in enumerate(words):
            if any(DISJ[x][y] for x,y in zip(a,b)): mask|=1<<j
        adj.append(mask)
    best=[]
    for trial in range(restarts):
        candidates=(1<<N)-1; chosen=[]
        if best and trial%4!=0:
            # Stochastic ruin-and-recreate from a verified incumbent.
            keep=max(0,len(best)-rng.randint(2,min(6,len(best)))) if len(best)>=2 else 0
            chosen=rng.sample(best,keep)
            for v in chosen: candidates &= adj[v]
        while candidates:
            inds=[]; c=candidates
            while c:
                bit=c&-c; inds.append(bit.bit_length()-1); c^=bit
            # Mix greedy high-degree and uniformly sampled starts; independent seeds.
            if not chosen or rng.random()<.22: v=rng.choice(inds)
            else:
                pool=rng.sample(inds,min(len(inds),32)); v=max(pool,key=lambda x:(adj[x]&candidates).bit_count()+rng.random()*.8)
            chosen.append(v); candidates &= adj[v]
        if len(chosen)>len(best): best=chosen
    return [list(words[i]) for i in best]

def shannon(seed,restarts):
    a=clique_search(2,seed,restarts); b=clique_search(3,seed+1,restarts)
    c=[x+y for x in a for y in b]
    return {'seed':seed,'restarts_per_power':restarts,'witness':{'words':c},'exact':packing(c),'component_sizes':[len(a),len(b)],'scope':'random greedy and ruin-and-recreate search in lengths 2 and 3, then Cartesian concatenation; no upper bound or direct length-five optimization'}

def lih(seed,samples):
    rng=random.Random(seed); best=None; positive=None; count=0
    for i in range(samples):
        n=3+i%5; k=rng.randint(1,8); a=[[0]*n for _ in range(n)]
        for _ in range(k):
            perm=rng.sample(range(n),n)
            for r,c in enumerate(perm): a[r][c]+=1
        matrix=[[str(F(x,k)) for x in r] for r in a]
        t=F(rng.randint(5,9),10); witness={'matrix':matrix,'t':str(t)}
        result=lih_wang(matrix,str(t)); count+=1
        gap=F(result['lhs_minus_rhs'])
        if best is None or gap>F(best['exact']['lhs_minus_rhs']): best={'witness':witness,'exact':result}
        if result['verified_counterexample']: positive={'witness':witness,'exact':result}; break
    return {'seed':seed,'instances_checked':count,'best':best,'counterexample':positive,'scope':'random equal-weight mixtures of permutation matrices, n=3..7, t=0.5..0.9; finite nonexhaustive test'}

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('target',choices=['shannon','lih-wang']); p.add_argument('--seed',type=int,default=17); p.add_argument('--trials',type=int,default=250); p.add_argument('--out',type=Path,required=True); a=p.parse_args()
    if a.trials<1:p.error('positive trials required')
    result=(shannon if a.target=='shannon' else lih)(a.seed,a.trials); a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps({k:v for k,v in result.items() if k not in ('witness','best','counterexample')},indent=2))
