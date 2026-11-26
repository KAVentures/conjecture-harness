"""Matched-budget full-engine evaluation with blinded final-answer review.

The reference solutions never enter worker prompts. Exact engine replay and
external judgments are distinct outcomes. No claim of training-data holdout.
"""
import argparse,json,math,random,re,secrets,time
from pathlib import Path
from runtime import invoke,read_json
from discovery import new,save,check
from discovery_run import run as engine_run
from proof_audit import audit
from historical_eval import freeze,digest,validate_tasks,parse_answer,valid_text,VERDICTS,write

ARMS=('independent','iterative','engine')
SCHEMA=1

def design(tasks,references,calls=4,timeout=60,seconds=300,seed=0):
    if type(calls) is not int or not 2<=calls<=12 or type(seed) is not int or any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in (timeout,seconds)) or timeout>3600 or seconds>14400 or seconds<2*timeout:raise ValueError('experiment limits')
    return dict(schema=SCHEMA,reference_design=freeze(tasks,references),arms=list(ARMS),calls=calls,timeout=timeout,seconds=seconds,seed=seed,scope='matched worker-call ceiling and wall-time target; not matched tokens, energy or compute')

def validate_design(tasks,d):
    validate_tasks(tasks)
    if not isinstance(d,dict) or set(d)!={'schema','reference_design','arms','calls','timeout','seconds','seed','scope'}:raise ValueError('design shape')
    ref=d['reference_design']
    if not isinstance(ref,dict) or ref.get('tasks_sha256')!=digest(tasks) or ref.get('task_count')!=len(tasks) or not re.fullmatch(r'[0-9a-f]{64}',str(ref.get('references_sha256'))):raise ValueError('task commitment mismatch')
    if type(d['schema']) is not int or d['schema']!=SCHEMA or d['arms']!=list(ARMS) or type(d['calls']) is not int or not 2<=d['calls']<=12 or type(d['seed']) is not int or any(type(d[k]) not in (int,float) or not math.isfinite(d[k]) or d[k]<=0 for k in ('timeout','seconds')) or d['timeout']>3600 or d['seconds']>14400 or d['seconds']<2*d['timeout']:raise ValueError('design limits')
    return d

def worker_prompt(statement,previous=None,final=False):
    s=('Resolve the exact mathematical statement. Return JSON with keys status (candidate, partial, abstained) and argument (string). Give a self-contained proof or exact counterexample; explicitly identify remaining gaps. Do not equate plausibility or finite checks with universal proof. Statement:\n'+statement)
    if final:s+='\nThis is the final answer. Independently scrutinize the supplied research material; use only sound arguments and do not claim a result you cannot establish.'
    if previous is not None:s+='\nUntrusted research material:\n'+json.dumps(previous,ensure_ascii=False)
    return s

def call(cmd,prompt,folder,timeout):
    folder.mkdir();(folder/'prompt.txt').write_text(prompt,encoding='utf-8')
    raw=invoke(cmd,prompt,timeout,folder,65536);write(folder/'raw.json',raw)
    return parse_answer(raw)

def evidence(g):
    """Bounded final synthesis context; keep original exact statements."""
    r=audit(g)
    # Include the target and relevant current proof graph, not unbounded history.
    relevant=['goal']+sorted(set(g['nodes'])-{'goal'})
    nodes={i:g['nodes'][i] for i in relevant[:60]}
    edges={i:e for i,e in sorted(g['edges'].items()) if e['parent'] in nodes and set(e['premises'])<=set(nodes)}
    o={i:v for i,v in sorted(g['observations'].items()) if v['focus'] in nodes}
    data=dict(audit_status=r['status'],verified={i:v for i,v in r['proved'].items() if i in nodes},refuted={i:v for i,v in r['refuted'].items() if i in nodes},nodes=nodes,edges=dict(list(edges.items())[:60]),observations=dict(list(o.items())[:60]),scope='research material; review exact statement correspondence and proof')
    # Prefer complete records to string truncation.
    while len(json.dumps(data,ensure_ascii=False))>80000:
        if data['observations']:data['observations'].pop(next(reversed(data['observations'])))
        elif data['edges']:data['edges'].pop(next(reversed(data['edges'])))
        elif len(data['nodes'])>1:
            i=next(reversed(data['nodes']));data['nodes'].pop(i);data['verified'].pop(i,None);data['refuted'].pop(i,None)
        else:break
    data['edges']={i:e for i,e in data['edges'].items() if e['parent'] in data['nodes'] and set(e['premises'])<=set(data['nodes'])}
    data['observations']={i:o for i,o in data['observations'].items() if o['focus'] in data['nodes']}
    return data

def run_cell(task,arm,cmd,folder,d):
    start=time.monotonic();deadline=start+d['seconds'];reserve=d['timeout'];calls=0;material=[];state_hash=None;machine='not-applicable'
    folder.mkdir()
    if arm=='engine':
        path=folder/'state.json';save(path,new(task['statement']))
        # Use the actual core runner, including exact discharge and opt-in
        # metareasoning. Reserve one worker call for final prose synthesis.
        engine_run(path,cmd,d['calls']-1,max(0.001,deadline-time.monotonic()-reserve),d['timeout'],metareasoning=True)
        g=check(read_json(path,limit=32*1024*1024));state_hash=digest(g)
        calls=len([h for h in g['history'] if not h['trusted_review']])
        if calls>d['calls']-1:raise ArithmeticError('engine call budget exceeded')
        machine=audit(g)['status'];material=evidence(g)
    else:
        for i in range(d['calls']-1):
            remaining=deadline-time.monotonic()-reserve
            if remaining<=0:break
            previous=material[-1] if arm=='iterative' and material else None
            answer=call(cmd,worker_prompt(task['statement'],previous),folder/f'proposal-{i:02d}',min(d['timeout'],remaining))
            material.append(answer);calls+=1
    remaining=deadline-time.monotonic()
    if remaining>0:
        final=call(cmd,worker_prompt(task['statement'],material,final=True),folder/'final',min(d['timeout'],remaining));calls+=1
    else:final=dict(status='abstained',argument='Wall-time target exhausted before final synthesis.')
    return final,dict(calls=calls,elapsed_seconds=round(time.monotonic()-start,3),machine=machine,state_sha256=state_hash)

def run(tasks,d,cmd,out):
    validate_design(tasks,d)
    if not isinstance(cmd,list) or not cmd or any(not valid_text(c,4096) for c in cmd):raise ValueError('trusted worker command required')
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    work=out/'cells';work.mkdir()
    jobs=[(i,a) for i in range(len(tasks)) for a in ARMS];random.Random(d['seed']).shuffle(jobs)
    meta=dict(design=d,worker_command_sha256=digest(cmd),cell_count=len(jobs))
    write(out/'design.json',meta)
    packet=[];key={}
    for j,(i,arm) in enumerate(jobs):
        final,metrics=run_cell(tasks[i],arm,cmd,work/f'{j:04d}',d)
        rid=secrets.token_hex(16)
        item=dict(id=rid,statement=tasks[i]['statement'],answer=final)
        packet.append(item);key[rid]=dict(task=tasks[i]['id'],arm=arm,cell=j,sha256=digest(item),**metrics)
        write(out/'checkpoint-private.json',dict(completed=len(packet),key=key))
    secrets.SystemRandom().shuffle(packet)
    write(out/'review-packet.json',packet);write(out/'private-key.json',key)
    manifest=dict(complete=True,meta_sha256=digest(meta),packet_sha256=digest(packet),key_sha256=digest(key))
    write(out/'manifest.json',manifest)
    return dict(cells=len(packet),review_required=True)

def score(tasks,references,root,reviews):
    root=Path(root);meta=read_json(root/'design.json');packet=read_json(root/'review-packet.json',limit=16*1024*1024);key=read_json(root/'private-key.json',limit=16*1024*1024);manifest=read_json(root/'manifest.json')
    d=validate_design(tasks,meta['design'])
    if d['reference_design']!=freeze(tasks,references) or manifest!=dict(complete=True,meta_sha256=digest(meta),packet_sha256=digest(packet),key_sha256=digest(key)):raise ValueError('frozen artifact mismatch')
    ids={x['id'] for x in packet}
    if len(ids)!=len(packet) or ids!=set(key) or not isinstance(reviews,list):raise ValueError('review packet coverage')
    judged={}
    for v in reviews:
        if not isinstance(v,dict) or set(v)!={'id','sha256','verdict','reviewer','rationale'} or v['id'] not in ids or v['id'] in judged or v['verdict'] not in VERDICTS or not valid_text(v['reviewer'],200) or not valid_text(v['rationale']) or v['sha256']!=key[v['id']]['sha256']:raise ValueError('invalid review')
        judged[v['id']]=v
    if set(judged)!=ids:raise ValueError('missing final-answer review')
    taskmap={t['id']:t['statement'] for t in tasks};cells={};used=set()
    for item in packet:
        k=key[item['id']];verdict=judged[item['id']]['verdict'];cell=(k['task'],k['arm']);j=k['cell']
        if digest(item)!=k['sha256'] or k['task'] not in taskmap or item['statement']!=taskmap[k['task']] or k['arm'] not in ARMS or cell in cells or type(j) is not int or not 0<=j<len(packet) or j in used or type(k['calls']) is not int or not 0<=k['calls']<=d['calls'] or type(k['elapsed_seconds']) not in (int,float) or not math.isfinite(k['elapsed_seconds']) or k['elapsed_seconds']<0:raise ValueError('cell mismatch')
        used.add(j)
        expected=references[k['task']]['expected']
        if verdict in ('proved','refuted') and verdict!=expected:raise ValueError('review/reference conflict; adjudication required')
        machine=k['machine']
        if k['arm']=='engine':
            g=check(read_json(root/'cells'/f'{j:04d}'/'state.json',limit=32*1024*1024))
            if digest(g)!=k['state_sha256'] or g['nodes']['goal']['statement']!=item['statement'] or audit(g)['status']!=machine:raise ValueError('engine proof-state replay mismatch')
            if machine=='conflict' or machine in ('proved','refuted') and machine!=expected:raise ValueError('engine/reference conflict; adjudication required')
        elif machine!='not-applicable' or k['state_sha256'] is not None:raise ValueError('non-engine audit result')
        cells[cell]=dict(verdict=verdict,machine=machine,calls=k['calls'],seconds=k['elapsed_seconds'])
    if set(cells)!={(t['id'],a) for t in tasks for a in ARMS}:raise ValueError('unmatched experiment')
    summary={};solved={}
    for arm in ARMS:
        rows=[cells[t['id'],arm] for t in tasks]
        solved[arm]={t['id'] for t in tasks if cells[t['id'],arm]['verdict'] in ('proved','refuted')}
        summary[arm]=dict(reviewed_solved=len(solved[arm]),total=len(tasks),machine_verified=sum(v['machine'] in ('proved','refuted') for v in rows) if arm=='engine' else None,calls=sum(v['calls'] for v in rows),seconds=round(sum(v['seconds'] for v in rows),3),wall_target_overruns=sum(v['seconds']>d['seconds'] for v in rows))
    comparisons={}
    for baseline in ARMS[:2]:
        a=solved['engine'];b=solved[baseline]
        comparisons[baseline]=dict(both=len(a&b),engine_only=len(a-b),baseline_only=len(b-a),neither=len(tasks)-len(a|b))
    return dict(summary=summary,paired=comparisons,scope='blinded final-answer judgments and separately replayed engine certificates; no causal, novelty, or training-data exclusion claim')

def main():
    q=argparse.ArgumentParser(description=__doc__);sub=q.add_subparsers(dest='action',required=True)
    a=sub.add_parser('freeze');a.add_argument('tasks');a.add_argument('references');a.add_argument('output');a.add_argument('--calls',type=int,default=4);a.add_argument('--timeout',type=float,default=60);a.add_argument('--seconds',type=float,default=300);a.add_argument('--seed',type=int,default=0)
    a=sub.add_parser('run');a.add_argument('tasks');a.add_argument('design');a.add_argument('config');a.add_argument('out')
    a=sub.add_parser('score');a.add_argument('tasks');a.add_argument('references');a.add_argument('run_dir');a.add_argument('reviews')
    a=q.parse_args();tasks=read_json(a.tasks)
    if a.action=='freeze':
        with Path(a.output).open('x',encoding='utf-8') as f:json.dump(design(tasks,read_json(a.references),a.calls,a.timeout,a.seconds,a.seed),f,indent=2);f.write('\n')
        return
    if a.action=='run':r=run(tasks,read_json(a.design),read_json(a.config)['worker'],a.out)
    else:r=score(tasks,read_json(a.references),a.run_dir,read_json(a.reviews,limit=16*1024*1024))
    print(json.dumps(r,indent=2))
if __name__=='__main__':main()
