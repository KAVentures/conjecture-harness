"""Bounded equational theorem search and independently checked finite countermodels.

All axioms and the conclusion are universally quantified over a nonempty
single-sorted algebra. Terms are variable strings or [operation, arguments...].
"""
import itertools,json,re,random
from collections import deque
from runtime import strict_json

PREFIX='Universal equational theorem: '
MAX_TERM=24
MAX_PATH=48
MAX_MODEL=3


def size(t):return 1 if isinstance(t,str) else 1+sum(size(x) for x in t[1:])
def variables(t):return {t} if isinstance(t,str) else set().union(*(variables(x) for x in t[1:]))
def parse_term(t,vs,ops,depth=0):
    if depth>=MAX_TERM:raise ValueError('term depth')
    if isinstance(t,str) and t in vs:return t
    if not isinstance(t,(list,tuple)) or not t or not isinstance(t[0],str) or t[0] not in ops or len(t)!=ops[t[0]]+1:raise ValueError('term syntax')
    out=(t[0],*(parse_term(x,vs,ops,depth+1) for x in t[1:]))
    if size(out)>MAX_TERM:raise ValueError('term size')
    return out

def wire(t):return t if isinstance(t,str) else [t[0],*(wire(x) for x in t[1:])]
def name(x):return isinstance(x,str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,15}',x) is not None
def normalize(s):
    if not isinstance(s,dict) or set(s)!={'variables','operations','axioms','conclusion'}:raise ValueError('claim shape')
    vs=s['variables'];ops=s['operations'];ax=s['axioms']
    if not isinstance(vs,list) or not 1<=len(vs)<=4 or any(not name(v) for v in vs) or len(set(vs))!=len(vs):raise ValueError('variables')
    if not isinstance(ops,dict) or not 1<=len(ops)<=5 or any(not name(k) or k in vs or type(a) is not int or not 0<=a<=2 for k,a in ops.items()):raise ValueError('operations')
    if not isinstance(ax,list) or len(ax)>8:raise ValueError('axiom limit')
    def eq(e):
        if not isinstance(e,list) or len(e)!=2:raise ValueError('equation shape')
        return [wire(parse_term(t,vs,ops)) for t in e]
    return dict(variables=vs,operations=dict(sorted(ops.items())),axioms=[eq(e) for e in ax],conclusion=eq(s['conclusion']))

def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))
def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('not equational')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical equation')
    return s

def parts(s):
    vs=s['variables'];ops=s['operations']
    return [[parse_term(t,vs,ops) for t in e] for e in s['axioms']], [parse_term(t,vs,ops) for t in s['conclusion']]

def substitute(t,env):return env[t] if isinstance(t,str) else (t[0],*(substitute(x,env) for x in t[1:]))
def match(pattern,t,env):
    if isinstance(pattern,str):
        if pattern in env:return env[pattern]==t
        env[pattern]=t;return True
    return not isinstance(t,str) and pattern[0]==t[0] and all(match(a,b,env) for a,b in zip(pattern[1:],t[1:]))

def positions(t,path=()):
    yield path,t
    if not isinstance(t,str):
        for i,x in enumerate(t[1:]):yield from positions(x,path+(i,))

def replace(t,path,x):
    if not path:return x
    if isinstance(t,str) or type(path[0]) is not int or not 0<=path[0]<len(t)-1:raise ValueError('rewrite position')
    i=path[0]+1
    return t[:i]+(replace(t[i],path[1:],x),)+t[i+1:]

def rewrite(t,ax,step,vs,ops):
    if not isinstance(step,dict) or set(step)!={'axiom','direction','path','substitution'}:raise ValueError('rewrite step')
    j=step['axiom'];d=step['direction'];path=step['path'];sub=step['substitution']
    if type(j) is not int or not 0<=j<len(ax) or type(d) is not int or d not in (0,1) or not isinstance(path,list) or len(path)>=MAX_TERM or any(type(i) is not int or i<0 for i in path):raise ValueError('rewrite locator')
    lhs,rhs=ax[j][d],ax[j][1-d];needed=variables(lhs)|variables(rhs)
    if not isinstance(sub,dict) or set(sub)!=needed:raise ValueError('substitution coverage')
    env={k:parse_term(v,vs,ops) for k,v in sub.items()}
    target=dict(positions(t)).get(tuple(path))
    if target is None or substitute(lhs,env)!=target:raise ValueError('rewrite mismatch')
    result=replace(t,path,substitute(rhs,env))
    if size(result)>MAX_TERM:raise ValueError('rewrite term limit')
    return result

def evaluate(t,env,tables,n):
    if isinstance(t,str):return env[t]
    i=0
    for x in t[1:]:i=n*i+evaluate(x,env,tables,n)
    return tables[t[0]][i]

def valuations(vs,n):
    for x in itertools.product(range(n),repeat=len(vs)):yield dict(zip(vs,x))

def check_model(s,cert):
    if set(cert)!={'kind','size','tables','assignment'}:return False
    n=cert['size'];tables=cert['tables'];env=cert['assignment'];vs=s['variables'];ops=s['operations']
    if type(n) is not int or not 1<=n<=MAX_MODEL or not isinstance(tables,dict) or set(tables)!=set(ops) or not isinstance(env,dict) or set(env)!=set(vs):return False
    if any(not isinstance(tables[k],list) or len(tables[k])!=n**a or any(type(v) is not int or not 0<=v<n for v in tables[k]) for k,a in ops.items()) or any(type(v) is not int or not 0<=v<n for v in env.values()):return False
    ax,(a,b)=parts(s)
    if any(evaluate(a0,v,tables,n)!=evaluate(b0,v,tables,n) for a0,b0 in ax for v in valuations(sorted(variables(a0)|variables(b0)),n)):return False
    return evaluate(a,env,tables,n)!=evaluate(b,env,tables,n)

def replay(s,cert):
    try:
        s=normalize(s);ax,(a,b)=parts(s)
        if not isinstance(cert,dict):return None
        if cert.get('kind')=='rewrite-chain' and set(cert)=={'kind','steps'}:
            steps=cert['steps']
            if not isinstance(steps,list) or len(steps)>MAX_PATH:return None
            for step in steps:a=rewrite(a,ax,step,s['variables'],s['operations'])
            return 'proved' if a==b else None
        if cert.get('kind')=='finite-algebra':return 'refuted' if check_model(s,cert) else None
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,RecursionError):pass
    return None

def neighbors(t,ax,pool):
    seen=set();count=0
    for path,node in positions(t):
        for j,eq in enumerate(ax):
            for d in (0,1):
                lhs,rhs=eq[d],eq[1-d];env={}
                if not match(lhs,node,env):continue
                missing=sorted(variables(rhs)-set(env))
                # Missing variables are universally quantified, but search
                # chooses only a bounded set of concrete terms for them.
                for xs in itertools.islice(itertools.product(pool,repeat=len(missing)),16):
                    e=dict(env,**dict(zip(missing,xs)))
                    out=replace(t,path,substitute(rhs,e))
                    if out==t or size(out)>MAX_TERM or out in seen:continue
                    seen.add(out);count+=1
                    yield out,dict(axiom=j,direction=d,path=list(path),substitution={k:wire(v) for k,v in sorted(e.items())})
                    if count>=192:return

def prove(s,budget):
    ax,(a,b)=parts(s)
    if a==b:return dict(kind='rewrite-chain',steps=[]),0
    pool=list(dict.fromkeys([*s['variables'],*((k,) for k,v in s['operations'].items() if v==0),*(t for _,t in positions(a)),*(t for _,t in positions(b))]))[:12]
    maps=[{a:(None,None,0)},{b:(None,None,0)}];queues=[deque([a]),deque([b])];expanded=0
    def path(i,t):
        out=[]
        while maps[i][t][0] is not None:
            prev,step,_=maps[i][t];out.append(step);t=prev
        return list(reversed(out))
    while expanded<budget and all(queues):
        i=0 if len(queues[0])<=len(queues[1]) else 1;t=queues[i].popleft();expanded+=1
        depth=maps[i][t][2]
        if depth>=MAX_PATH//2:continue
        for q,step in neighbors(t,ax,pool):
            if q in maps[i]:continue
            if len(maps[i])>=budget*12:break
            maps[i][q]=(t,step,depth+1);queues[i].append(q)
            if q in maps[1-i]:
                left=path(0,q);right=path(1,q)
                cert=dict(kind='rewrite-chain',steps=left+[dict(st,direction=1-st['direction']) for st in reversed(right)])
                if replay(s,cert)!='proved':raise ArithmeticError('rewrite chain replay failed')
                return cert,expanded
    return None,expanded

def model_search(s,budget):
    ax,(a,b)=parts(s);ops=s['operations'];vs=s['variables'];rng=random.Random(137);tested=0
    for n in (2,3):
        width=sum(n**arity for arity in ops.values());space=n**width
        cap=(budget+1)//2 if n==2 else budget-tested
        if space<=cap:rows=itertools.product(range(n),repeat=width)
        else:
            def samples():
                # Projections, constants and random operation tables.
                for option in (0,1,2,3):
                    out=[]
                    for arity in ops.values():
                        for xs in itertools.product(range(n),repeat=arity):
                            out.append(xs[0] if option==2 and xs else xs[-1] if option==3 and xs else option%n)
                    yield tuple(out)
                for _ in range(cap):yield tuple(rng.randrange(n) for _ in range(width))
            rows=samples()
        for row in itertools.islice(rows,cap):
            if tested>=budget:return None,tested
            tested+=1;offset=0;tables={}
            for k,arity in ops.items():
                length=n**arity;tables[k]=list(row[offset:offset+length]);offset+=length
            if any(evaluate(x,v,tables,n)!=evaluate(y,v,tables,n) for x,y in ax for v in valuations(sorted(variables(x)|variables(y)),n)):continue
            for env in valuations(vs,n):
                if evaluate(a,env,tables,n)!=evaluate(b,env,tables,n):
                    cert=dict(kind='finite-algebra',size=n,tables=tables,assignment=env)
                    if replay(s,cert)!='refuted':raise ArithmeticError('finite model replay failed')
                    return cert,tested
    return None,tested

def solve(s,rewrite_budget=128,model_budget=128):
    s=normalize(s)
    if type(rewrite_budget) is not int or not 1<=rewrite_budget<=512 or type(model_budget) is not int or not 1<=model_budget<=1024:raise ValueError('search limits')
    cert,tested=model_search(s,model_budget)
    if cert:return dict(status='refuted',certificate=cert,models=tested,expanded=0)
    direct_budget=max(1,(rewrite_budget+1)//2)
    cert,expanded=prove(s,direct_budget)
    if cert:return dict(status='proved',certificate=cert,models=tested,expanded=expanded)
    if expanded<rewrite_budget and rewrite_budget>1:
        from critical_pairs import prove as invent_and_prove
        cert,extra,derived=invent_and_prove(s,rewrite_budget-expanded)
        expanded+=extra
        if cert:return dict(status='proved',certificate=cert,models=tested,expanded=expanded,derived_lemmas=derived)
    return dict(status='unknown',models=tested,expanded=expanded,scope='bounded rewrite, critical-pair and finite-model search; no completeness claim')

def main():
    import argparse
    from runtime import read_json
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('spec');p.add_argument('--rewrite-budget',type=int,default=128);p.add_argument('--model-budget',type=int,default=128);a=p.parse_args()
    print(json.dumps(solve(read_json(a.spec),a.rewrite_budget,a.model_budget),indent=2))
if __name__=='__main__':main()
