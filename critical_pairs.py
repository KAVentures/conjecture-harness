"""Bounded proof-producing critical-pair lemma invention for equations."""
import itertools,json
import equational as e


def rename(t,prefix):
    return prefix+t if isinstance(t,str) else (t[0],*(rename(x,prefix) for x in t[1:]))

def apply(t,env):
    if isinstance(t,str):return apply(env[t],env) if t in env else t
    return (t[0],*(apply(x,env) for x in t[1:]))

def unify(a,b):
    """First-order syntactic unification with occurs check."""
    todo=[(a,b)];env={}
    while todo:
        x,y=todo.pop();x=apply(x,env);y=apply(y,env)
        if x==y:continue
        if isinstance(y,str) and not isinstance(x,str):x,y=y,x
        if isinstance(x,str):
            if x in e.variables(y):return None
            env[x]=y
        elif isinstance(y,str):raise ArithmeticError('unification orientation')
        elif x[0]!=y[0] or len(x)!=len(y):return None
        else:todo.extend(zip(x[1:],y[1:]))
    return env

def lemmas(spec,budget=128,limit=12):
    s=e.normalize(spec);ax,_=e.parts(s);vs=s['variables'];out=[];seen=set();tested=0
    if type(budget) is not int or not 1<=budget<=512 or type(limit) is not int or not 1<=limit<=32:raise ValueError('lemma budget')
    # Favor reducing orientations, but retain equal-size identities.
    rules=[(i,d,eq[d],eq[1-d]) for i,eq in enumerate(ax) for d in (0,1) if not isinstance(eq[d],str) and e.size(eq[d])>=e.size(eq[1-d])]
    for (i,d,a,b),(j,f,c,h) in itertools.product(rules,repeat=2):
        a,b,c,h=rename(a,'A_'),rename(b,'A_'),rename(c,'B_'),rename(h,'B_')
        for path,node in e.positions(a):
            if isinstance(node,str):continue
            if tested>=budget:break
            tested+=1;env=unify(node,c)
            if env is None:continue
            common=apply(a,env);left=apply(b,env);right=apply(e.replace(a,path,h),env)
            if left==right:continue
            needed=sorted(e.variables(common)|e.variables(left)|e.variables(right)|set().union(*(e.variables(apply(x,env)) for x in e.variables(a)|e.variables(b)|e.variables(c)|e.variables(h))))
            if len(needed)>len(vs):continue
            names=dict(zip(needed,vs));common,left,right=[e.substitute(t,names) for t in (common,left,right)]
            if max(map(e.size,(common,left,right)))>e.MAX_TERM:continue
            # Reverse the outer rewrite to common, then perform inner rewrite.
            subst1={x[2:]:e.wire(e.substitute(apply(x,env),names)) for x in sorted(e.variables(a)|e.variables(b))}
            subst2={x[2:]:e.wire(e.substitute(apply(x,env),names)) for x in sorted(e.variables(c)|e.variables(h))}
            cert=dict(kind='rewrite-chain',steps=[dict(axiom=i,direction=1-d,path=[],substitution=subst1),dict(axiom=j,direction=f,path=list(path),substitution=subst2)])
            claim=dict(s,conclusion=[e.wire(left),e.wire(right)])
            if e.replay(claim,cert)!='proved':raise ArithmeticError('critical pair replay failed')
            key=tuple(sorted((json.dumps(e.wire(left)),json.dumps(e.wire(right)))))
            if key in seen:continue
            seen.add(key)
            if any({left,right}==set(pair) for pair in ax):continue
            out.append(dict(conclusion=claim['conclusion'],certificate=cert))
        if tested>=budget:break
    out.sort(key=lambda x:(sum(e.size(e.parse_term(t,vs,s['operations'])) for t in x['conclusion']),json.dumps(x['conclusion'])))
    return out[:limit]

def expand(spec,derived,cert):
    """Replace each derived rewrite by its original-axiom proof chain."""
    s=e.normalize(spec);n=len(s['axioms']);steps=[]
    if cert.get('kind')!='rewrite-chain':return None
    for step in cert['steps']:
        j=step['axiom']
        if j<n:steps.append(step);continue
        item=derived[j-n];inner=item['certificate']['steps'];direction=step['direction']
        if direction:inner=[dict(st,direction=1-st['direction']) for st in reversed(inner)]
        # Unused variables in the lemma's proof may be instantiated by any
        # target variable, since the original axiom equations are universal.
        env={x:e.parse_term(step['substitution'].get(x,s['variables'][0]),s['variables'],s['operations']) for x in s['variables']}
        for st in inner:
            sub={k:e.wire(e.substitute(e.parse_term(v,s['variables'],s['operations']),env)) for k,v in st['substitution'].items()}
            steps.append(dict(st,path=step['path']+st['path'],substitution=sub))
        if len(steps)>e.MAX_PATH:return None
    result=dict(kind='rewrite-chain',steps=steps)
    return result if e.replay(s,result)=='proved' else None

def prove(spec,budget=128):
    s=e.normalize(spec);available=8-len(s['axioms'])
    if available<=0:return None,0,0
    derived=lemmas(s,limit=available)
    if not derived:return None,0,0
    extended=dict(s,axioms=s['axioms']+[x['conclusion'] for x in derived])
    cert,expanded=e.prove(extended,budget)
    return (expand(s,derived,cert) if cert else None),expanded,len(derived)

def main():
    import argparse
    from runtime import read_json
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('spec');p.add_argument('--budget',type=int,default=128);a=p.parse_args()
    print(json.dumps(lemmas(read_json(a.spec),a.budget),indent=2))
if __name__=='__main__':main()
