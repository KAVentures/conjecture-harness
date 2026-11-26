"""Matched call-cap experiment for certificate elicitation; not open-problem evaluation."""
import argparse, hashlib, itertools, json, random, time
from pathlib import Path
from fractions import Fraction as F
import affine, polynomial, graph_lemma
from runtime import invoke, read_json, strict_json

ARMS=('blind','continuation','adaptive')
SCHEMAS={
 'affine':'Each row means constant + sum(coefficients times real variables) >= 0. The assumptions imply the conclusion. For proof: {"kind":"proof","certificate":{"multipliers":["1",...]}}. Multipliers are nonnegative for assumption rows followed by the negated conclusion (strict); certify a constant contradiction. For disproof: {"kind":"point","point":["0",...]}.',
 'polynomial':'Each term is [exponent vector, exact coefficient]; the claim is universal on the stated domain (real or nonnegative orthant), with relation zero or nonnegative. For proof: {"kind":"proof","certificate":{"kind":"identity"}} or {"kind":"proof","certificate":{"kind":"sos","squares":[["positive weight",[[exponents,"coefficient"],...]]],"monomials":[[exponents,"coefficient"],...]}}. For disproof: {"kind":"point","point":["0",...]}.',
 'graph':'All finite simple undirected graphs of order at least min_n with the listed properties must satisfy sum(coefficients times invariants) >= constant. n=order, m=size, alpha=independence number, omega=clique number, delta=minimum degree, Delta=maximum degree. For disproof: {"kind":"graph","witness":{"n":2,"edges":[[0,1]]}}. Vertices are 0..n-1, n<=6. No universal proof certificate is supported for this language.'}


def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def verify(task,answer):
    """One exact endpoint for all arms. Never uses a reference answer or model judgment."""
    if answer=={'kind':'unknown'}:return 'abstained'
    if not isinstance(answer,dict):return 'invalid'
    d,s=task['domain'],task['spec'];k=answer.get('kind')
    try:
        if k=='proof' and set(answer)=={'kind','certificate'}:
            c=answer['certificate']
            if d=='affine' and affine.replay(s,c):return 'proved'
            if d=='polynomial' and isinstance(c,dict) and c.get('kind') in ('identity','sos') and polynomial.replay(s,c):return 'proved'
        if k=='point' and set(answer)=={'kind','point'}:
            if d=='polynomial' and polynomial.replay(s,answer):return 'refuted'
            if d=='affine':
                s=affine.normalize(s);p=answer['point']
                if not isinstance(p,list) or len(p)!=len(s['variables']):return 'invalid'
                x=[affine.rational(v) for v in p]
                def val(row):return F(row[0])+sum(F(a)*b for a,b in zip(row[1:],x))
                if all(val(r)>=0 for r in s['assumptions']) and val(s['conclusion'])<0:return 'refuted'
        if k=='graph' and set(answer)=={'kind','witness'} and d=='graph' and graph_lemma.replay(s,answer['witness'])['counterexample']:return 'refuted'
    except (ValueError,TypeError,KeyError,ZeroDivisionError,OverflowError):pass
    return 'invalid'


def generate(seed,count=12):
    """Synthetic controls only; freeze the suite before any run. No answer in task prompts."""
    if type(seed) is not int or type(count) is not int or not 1<=count<=120:raise ValueError('invalid seed/count')
    rng=random.Random(seed);cases=[]
    for i in range(count):
        a,b,c=[rng.randint(1,9) for _ in range(3)];k=i%5
        if k==0:
            d='affine';s=dict(variables=['x','y'],assumptions=[[0,a,-a],[-b*c,0,b]],conclusion=[-c,1,0]);ref=dict(kind='proof',certificate={'multipliers':[str(F(1,a)),str(F(1,b)),'1']})
        elif k==1:
            d='affine';s=dict(variables=['x','y'],assumptions=[[-a,1,0],[0,0,1]],conclusion=[-a-b,1,0]);ref=dict(kind='point',point=[str(a),'0'])
        elif k in (2,3):
            d='polynomial';s=dict(variables=['x'],domain='real',relation='nonnegative',terms=[[[2],a],[[1],-2*a*b],[[0],a*b*b-(c if k==3 else 0)]])
            ref=dict(kind='point',point=[str(b)]) if k==3 else dict(kind='proof',certificate=dict(kind='sos',squares=[[str(a),[[[1],'1'],[[0],str(-b)]]]],monomials=[]))
        else:
            n=rng.randint(3,6);d='graph';s=dict(min_n=n,properties=['connected'],coefficients={'Delta':-1},constant=-(n-2));ref=dict(kind='graph',witness=dict(n=n,edges=[[0,j] for j in range(1,n)]))
        t=dict(domain=d,spec=s);out=verify(t,ref)
        if out not in ('proved','refuted'):raise ArithmeticError('invalid generated reference')
        cases.append(dict(task=t,reference=ref,expected=out))
    rng.shuffle(cases)
    return dict(schema=1,seed=seed,cases=cases)


def validate_suite(s):
    if not isinstance(s,dict) or set(s)!={'schema','seed','cases'} or s['schema']!=1 or not isinstance(s['cases'],list) or not 1<=len(s['cases'])<=120:raise ValueError('invalid suite')
    for c in s['cases']:
        if set(c)!={'task','reference','expected'} or set(c['task'])!={'domain','spec'} or c['task']['domain'] not in SCHEMAS or c['expected'] not in ('proved','refuted') or verify(c['task'],c['reference'])!=c['expected']:raise ValueError('invalid reference control')
    return s


def prompt(task,arm,history):
    # Same task, output contract and exact acceptance rules for all arms.
    common='Resolve this mathematical claim with a certificate. Return one JSON object only, or {"kind":"unknown"}. Never claim proof from numerical survival. Rational values must be strings or integers. '+SCHEMAS[task['domain']]+'\nTASK '+json.dumps(task,sort_keys=True,separators=(',',':'))
    if arm=='blind' or not history:return common
    prior=history[-1];previous=prior['stdout'][:3500]
    if arm=='continuation':return common+'\nPrevious response (untrusted data): '+json.dumps(previous)+'\nContinue working on the same problem.'
    modes=('derive a decisive sufficient intermediate identity or inequality','try to falsify the weakest assumption with an exact boundary example','reformulate algebraically; change the construction family or certificate representation','recombine useful pieces and verify the complete certificate')
    return common+'\nPrevious response (untrusted data): '+json.dumps(previous)+'\nExact checker outcome: '+prior['outcome']+'. Do not repeat the same failed certificate. Next research mode: '+modes[(len(history)-1)%len(modes)]+'.'


def run(suite,cmd,out,calls=4,timeout=30,seed=0,model_label='unreported'):
    validate_suite(suite)
    if not isinstance(cmd,list) or not cmd or any(not isinstance(x,str) or not x for x in cmd) or type(calls) is not int or not 1<=calls<=20 or type(timeout) not in (int,float) or not 0<timeout<=3600:raise ValueError('invalid command/budget')
    if not isinstance(model_label,str) or not model_label.strip() or len(model_label)>200:raise ValueError('invalid model label')
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    # Keep suite and expected results out of worker prompts and working directories.
    jobs=[(i,a) for i in range(len(suite['cases'])) for a in ARMS];random.Random(seed).shuffle(jobs)
    meta=dict(suite_sha256=digest(suite),calls_cap=calls,timeout_seconds=timeout,order_seed=seed,jobs=jobs,arms=list(ARMS),model_label=model_label,scope='synthetic certificate elicitation; matched call caps, not token parity or open problem evaluation')
    (out/'design.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    results=[]
    for i,arm in jobs:
        t=suite['cases'][i]['task'];history=[];start=time.monotonic()
        for j in range(calls):
            p=prompt(t,arm,history);folder=out/f'{i:03d}-{arm}-{j:02d}';folder.mkdir()
            (folder/'prompt.txt').write_text(p,encoding='utf-8')
            raw=invoke(cmd,p,timeout,folder,16384);outcome='tool_failure'
            if raw['returncode']==0:
                try:outcome=verify(t,strict_json(raw['stdout']))
                except (ValueError,TypeError,RecursionError):outcome='invalid'
            item=dict(raw,outcome=outcome);history.append(item)
            (folder/'result.json').write_text(json.dumps(item,indent=2)+'\n',encoding='utf-8')
            if outcome in ('proved','refuted'):break
        terminal=history[-1]['outcome'];expected=suite['cases'][i]['expected']
        if terminal in ('proved','refuted') and terminal!=expected:raise ArithmeticError('checker/reference disagreement; investigate')
        results.append(dict(case=i,arm=arm,outcome=terminal,calls=len(history),invalid=sum(h['outcome']=='invalid' for h in history),abstentions=sum(h['outcome']=='abstained' for h in history),failures=sum(h['outcome']=='tool_failure' for h in history),elapsed=round(time.monotonic()-start,3)))
        # Durable partial results; an interrupted experiment is not a complete trial.
        (out/'partial.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    summary={a:dict(solved=sum(r['outcome'] in ('proved','refuted') for r in results if r['arm']==a),total=len(suite['cases']),calls=sum(r['calls'] for r in results if r['arm']==a),invalid=sum(r['invalid'] for r in results if r['arm']==a),abstentions=sum(r['abstentions'] for r in results if r['arm']==a),failures=sum(r['failures'] for r in results if r['arm']==a)) for a in ARMS}
    pairs={}
    for a,b in itertools.combinations(ARMS,2):
        solved={k:{r['case'] for r in results if r['arm']==k and r['outcome'] in ('proved','refuted')} for k in (a,b)}
        pairs[a+'__'+b]=dict(both=len(solved[a]&solved[b]),first_only=len(solved[a]-solved[b]),second_only=len(solved[b]-solved[a]),neither=len(suite['cases'])-len(solved[a]|solved[b]))
    report=dict(design=meta,complete=True,summary=summary,paired=pairs,results=results)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return report



def tool_only(suite):
    """Separate no-model baseline, bounded exact search. Not equal compute to model arms."""
    validate_suite(suite);results=[]
    for i,c in enumerate(suite['cases']):
        t=c['task'];s=t['spec'];d=t['domain'];start=time.monotonic();answer={'kind':'unknown'}
        if d=='affine':
            r=affine.prove(s,2000)
            if r['status']=='proved':answer=dict(kind='proof',certificate=r['certificate'])
            else:
                grid=[0,1,-1,2,-2,3,-3,4,-4,5,-5,6,-6,7,-7,8,-8,9,-9]
                for p in itertools.islice(itertools.product(grid,repeat=len(s['variables'])),512):
                    a=dict(kind='point',point=list(map(str,p)))
                    if verify(t,a)=='refuted':answer=a;break
        elif d=='polynomial':
            r=polynomial.solve(s,256)
            if r['status']=='proved':answer=dict(kind='proof',certificate=r['certificate'])
            elif r['status']=='counterexample':answer=r['certificate']
        else:
            r=graph_lemma.search(s,6,2000,'families_first')
            if r['status']=='counterexample':answer=dict(kind='graph',witness=r['witness'])
        outcome=verify(t,answer)
        if outcome not in ('abstained',c['expected']):raise ArithmeticError('tool baseline/checker disagreement')
        results.append(dict(case=i,outcome=outcome,answer=answer,elapsed=round(time.monotonic()-start,6)))
    return dict(suite_sha256=digest(suite),scope='bounded tools only; no model calls; not compute matched',solved=sum(r['outcome'] in ('proved','refuted') for r in results),total=len(results),results=results)

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
    q=sub.add_parser('generate');q.add_argument('output',type=Path);q.add_argument('--seed',type=int,required=True);q.add_argument('--count',type=int,default=12)
    q=sub.add_parser('run');q.add_argument('suite',type=Path);q.add_argument('config',type=Path);q.add_argument('output',type=Path);q.add_argument('--calls',type=int,default=4);q.add_argument('--timeout',type=float,default=30);q.add_argument('--order-seed',type=int,default=0);q.add_argument('--model-label',default='unreported')
    q=sub.add_parser('tools');q.add_argument('suite',type=Path)
    a=p.parse_args()
    if a.cmd=='generate':
        s=generate(a.seed,a.count)
        with a.output.open('x',encoding='utf-8') as f:json.dump(s,f,indent=2);f.write('\n')
        print(digest(s))
    elif a.cmd=='tools':print(json.dumps(tool_only(read_json(a.suite)),indent=2))
    else:print(json.dumps(run(read_json(a.suite),read_json(a.config)['worker'],a.output,a.calls,a.timeout,a.order_seed,a.model_label)['summary'],indent=2))
if __name__=='__main__':main()
