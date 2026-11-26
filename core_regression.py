"""Deterministic cross-domain controls for the exact discovery engine.

These are deliberately transparent synthetic controls, not historical
conjectures, novelty claims, or evidence of improved model reasoning.
"""
import argparse,json,time
from pathlib import Path
import affine,polynomial as p,symbolic_discovery as sy,dynamics_discovery as dy
import indexed_algebra as ix,simplex_discovery as sx,conditional_theorems as ct
import equational as eq
import graph_structure as gs
from discovery import new
from discovery_run import auto_discharge
from proof_audit import audit
from historical_eval import digest

def cases():
    rows=[]
    def add(name,domain,m,s,expected):
        rows.append(dict(id=name,domain=domain,statement=m.statement(s),expected=expected))
    def poly(terms,domain='real',relation='nonnegative',vs=None):
        return dict(variables=vs or ['x'],domain=domain,relation=relation,terms=terms)
    add('affine-bound','affine',affine,dict(variables=['x'],assumptions=[[0,1]],conclusion=[1,2]),'proved')
    add('polynomial-quartic','polynomial',p,poly([[[4,0],1],[[2,2],-2],[[0,4],1]],vs=['x','y']),'proved')
    add('polynomial-narrow-negative','polynomial',p,poly([[[4],1],[[3],'-17/2'],[[2],'867/32'],[[1],'-4913/128'],[[0],'1336335/65536']]),'refuted')
    add('symbolic-sum','symbolic',sy,dict(parameters=['x'],relation='zero',summand=[[[1,1],2],[[0,1],1]],rhs=[[[2,1],1]]),'proved')
    add('symbolic-sum-false','symbolic',sy,dict(parameters=[],relation='zero',summand=[[[0],1]],rhs=[[[1],2]]),'refuted')
    fib=dict(variables=['x','y'],transition=[[[[0,1],1]],[[[1,0],1],[[0,1],1]]],observable=[[[1,0],1]],kind='recurrence')
    add('recurrence','dynamics',dy,dict(fib,weights=['-1','-1','1']),'proved')
    add('recurrence-false','dynamics',dy,dict(fib,weights=['-1','1']),'refuted')
    add('nonlinear-inductive-ideal','dynamics',dy,dict(kind='orbit-zero',variables=['x','y'],transition=[[[[2,0],1],[[0,1],1]],[[[0,2],1]]],observable=[[[1,0],1]],initial=[0,0]),'proved')
    add('indexed-symmetry','indexed',ix,dict(tensors={'S':dict(rank=2,symmetry='symmetric'),'A':dict(rank=2,symmetry='alternating')},terms=[dict(coefficient=1,n_power=0,factors=[['S',[0,1]],['A',[0,1]]])]),'proved')
    add('indexed-dimension-false','indexed',ix,dict(tensors={'D':dict(rank=2,symmetry='delta')},terms=[dict(coefficient=1,n_power=0,factors=[['D',[0,1]]]),dict(coefficient=-1,n_power=2,factors=[])]),'refuted')
    add('simplex-boundary-split','simplex',sx,dict(variables=['x','y'],terms=[[[2,0],1],[[1,1],-2],[[0,2],1]]),'proved')
    add('simplex-false','simplex',sx,dict(variables=['x','y'],terms=[[[0,0],-1],[[2,0],1]]),'refuted')
    add('conditional-product','conditional',ct,dict(variables=['x','y'],domain='real',assumptions=[dict(relation='nonnegative',terms=[[[1,0],1]]),dict(relation='nonnegative',terms=[[[0,1],1]])],conclusion=[[[1,1],1]]),'proved')
    add('conditional-false','conditional',ct,dict(variables=['x'],domain='real',assumptions=[dict(relation='nonnegative',terms=[[[1],1]])],conclusion=[[[1],-1]]),'refuted')
    add('univariate-sturm-positive','polynomial',p,poly([[[0],1],[[1],1],[[2],1],[[3],1],[[4],1]]),'proved')
    add('univariate-sturm-narrow-false','polynomial',p,poly([[[4],1],[[3],-8],[[2],24],[[1],-32],[[0],'159999/10000']]),'refuted')
    add('conditional-irrational-refutation','conditional',ct,dict(variables=['x'],domain='real',assumptions=[dict(relation='zero',terms=[[[2],1],[[0],-2]])],conclusion=[[[1],1],[[0],-2]]),'refuted')
    add('conditional-irrational-positive','conditional',ct,dict(variables=['x'],domain='nonnegative',assumptions=[dict(relation='zero',terms=[[[2],1],[[0],-2]])],conclusion=[[[2],1],[[0],-1]]),'proved')
    add('binary-homogeneous-algebraic-refutation','conditional',ct,dict(variables=['x','y'],domain='real',assumptions=[dict(relation='zero',terms=[[[2,0],1],[[0,2],-2]])],conclusion=[[[0,2],-1]]),'refuted')
    add('binary-homogeneous-algebraic-positive','conditional',ct,dict(variables=['x','y'],domain='real',assumptions=[dict(relation='zero',terms=[[[2,0],1],[[0,2],-2]])],conclusion=[[[2,0],1],[[0,2],-1]]),'proved')
    assoc=[['m',['m','x','y'],'z'],['m','x',['m','y','z']]];comm=[['m','x','y'],['m','y','x']]
    algebra=dict(variables=['x','y','z'],operations={'m':2})
    add('equational-associative-commutative','equational',eq,dict(algebra,axioms=[assoc,comm],conclusion=[['m',['m','x','y'],'z'],['m','z',['m','y','x']]]),'proved')
    add('equational-finite-countermodel','equational',eq,dict(algebra,axioms=[assoc],conclusion=comm),'refuted')
    cycle=[[0,1],[1,2],[2,3],[3,4],[0,4]]
    add('structural-odd-cycle-bound','graph',gs,dict(n=5,edges=cycle,invariant='alpha',upper=2),'proved')
    add('structural-odd-cycle-clique-refutation','graph',gs,dict(n=5,edges=cycle,invariant='omega',upper=1),'refuted')
    return rows

def run(passes=4,output=None):
    if type(passes) is not int or not 1<=passes<=12:raise ValueError('pass limit')
    output=Path(output) if output is not None else None
    if output:output.mkdir(parents=True,exist_ok=False)
    rows=[]
    for c in cases():
        start=time.monotonic();g=new(c['statement']);count=0;reason='pass_limit'
        try:
            for _ in range(passes):
                report=audit(g)
                if report['status'] in ('proved','refuted','conflict'):reason='audit_terminal';break
                h=auto_discharge(g);count+=1
                if h==g:reason='fixed_point';break
                g=h
            report=audit(g)
            status=report['status'];invalid=report['invalid_observations']
            error=None
        except Exception as exc:
            status='error';reason='exception';invalid=[];error=type(exc).__name__+': '+str(exc)[:500]
        row=dict(id=c['id'],domain=c['domain'],expected=c['expected'],actual=status,passed=status==c['expected'] and not invalid,passes=count,reason=reason,elapsed_seconds=round(time.monotonic()-start,3),invalid_observations=invalid,error=error,state_sha256=digest(g))
        rows.append(row)
        if output:(output/(c['id']+'.json')).write_text(json.dumps(g,indent=2),encoding='utf-8')
    result=dict(total=len(rows),passed=sum(r['passed'] for r in rows),model_calls=0,cases=rows,scope='transparent exact-engine regression controls; not a historical benchmark or a discovery performance estimate')
    if output:(output/'report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--passes',type=int,default=4);a.add_argument('--output');q=a.parse_args()
    r=run(q.passes,q.output);print(json.dumps(r,indent=2))
    if r['passed']!=r['total']:a.exit(1)
if __name__=='__main__':main()
