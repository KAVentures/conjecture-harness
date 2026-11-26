"""Matched-call historical theorem evaluation with separately held references and blinded review.

Trusted external commands only. No automatic correctness claims for prose proofs.
"""
import argparse,hashlib,json,random,re,secrets
from pathlib import Path
from runtime import invoke,read_json,strict_json

ARMS=('blind','adaptive')
VERDICTS=('proved','refuted','partial','incorrect','abstained')
MODES=('derive a sufficient lemma and justify the bridge','seek an exact counterexample to the weakest step','switch mathematical representation and justify the transfer','recombine surviving arguments and audit every quantifier')

def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def write(path,data):
    Path(path).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def valid_text(v,limit=20000):return isinstance(v,str) and 0<len(v.strip())<=limit
def validate_tasks(tasks):
    if not isinstance(tasks,list) or not 1<=len(tasks)<=100:raise ValueError('task count')
    seen=set()
    for t in tasks:
        if not isinstance(t,dict) or set(t)!={'id','statement'} or not isinstance(t['id'],str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',t['id']) or t['id'] in seen or not valid_text(t['statement']):raise ValueError('invalid public task')
        seen.add(t['id'])
    return tasks
def freeze(tasks,references):
    """References are kept with the operator; only the hash enters the public design."""
    validate_tasks(tasks)
    if not isinstance(references,dict) or set(references)!={t['id'] for t in tasks}:raise ValueError('reference coverage')
    for r in references.values():
        if not isinstance(r,dict) or set(r)!={'expected','source','reference'} or r['expected'] not in ('proved','refuted') or not valid_text(r['source']) or not valid_text(r['reference'],100000):raise ValueError('reference record')
    return dict(schema=1,tasks_sha256=digest(tasks),references_sha256=digest(references),task_count=len(tasks),scope='operator-curated historical targets; statement-only, not guaranteed model-training holdout')

def prompt(task,arm,prior,step):
    common='Resolve the mathematical statement below. Give a complete self-contained proof or exact counterexample; if incomplete, explicitly state gaps. Return JSON with keys status (candidate, partial, abstained) and argument (string). No numerical pattern alone is a proof. Statement:\n'+task['statement']
    if arm=='blind' or not prior:return common
    return common+'\nPrevious candidate (untrusted mathematical data): '+json.dumps(prior,ensure_ascii=False)+'\nDo not repeat a failed route. Next strategy: '+MODES[(step-1)%len(MODES)]
def parse_answer(raw):
    if raw.get('returncode')!=0:return dict(status='abstained',argument='Worker invocation failed.')
    try:
        a=strict_json(raw['stdout'])
        if isinstance(a,dict) and set(a)=={'status','argument'} and a['status'] in ('candidate','partial','abstained') and valid_text(a['argument']):return a
    except (ValueError,TypeError,RecursionError):pass
    return dict(status='abstained',argument='Invalid worker response.')
def run(tasks,design,cmd,out,calls=4,timeout=60,seed=0):
    validate_tasks(tasks)
    if not isinstance(design,dict) or design.get('tasks_sha256')!=digest(tasks) or design.get('task_count')!=len(tasks) or not re.fullmatch(r'[0-9a-f]{64}',str(design.get('references_sha256'))):raise ValueError('design mismatch')
    if not isinstance(cmd,list) or not cmd or any(not valid_text(c,4096) for c in cmd) or type(calls) is not int or not 1<=calls<=12 or type(timeout) not in (int,float) or not 0<timeout<=3600 or type(seed) is not int:raise ValueError('invalid experiment limits')
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    work=out/'worker-logs';work.mkdir()
    jobs=[(i,a) for i in range(len(tasks)) for a in ARMS];random.Random(seed).shuffle(jobs)
    meta=dict(design=design,calls_per_arm=calls,timeout_seconds=timeout,order_seed=seed,arms=list(ARMS),scope='matched call cap and per-call timeout; adaptive prompting vs blind prompting, not the full discovery runner or matched tokens')
    write(out/'design.json',meta)
    packet=[];key={}
    for job,(i,arm) in enumerate(jobs):
        prior=None
        for step in range(calls):
            folder=work/f'{job:04d}-{step:02d}';folder.mkdir()
            p=prompt(tasks[i],arm,prior,step);(folder/'prompt.txt').write_text(p,encoding='utf-8')
            raw=invoke(cmd,p,timeout,folder,65536);write(folder/'raw.json',raw)
            answer=parse_answer(raw)
            # Review every response, avoiding arm-specific self-selection or oracle stopping.
            rid=secrets.token_hex(16)
            item=dict(id=rid,statement=tasks[i]['statement'],answer=answer)
            packet.append(item);key[rid]=dict(task=tasks[i]['id'],arm=arm,step=step,sha256=digest(item))
            prior=answer
        write(out/'private-key.partial.json',key)
    secrets.SystemRandom().shuffle(packet)
    write(out/'review-packet.json',packet);write(out/'private-key.json',key)
    write(out/'run-manifest.json',dict(complete=True,packet_sha256=digest(packet),key_sha256=digest(key),design_sha256=digest(meta)))
    return dict(complete=True,attempts=len(packet),review_required=True)

def score(tasks,references,meta,packet,key,manifest,reviews):
    expected=freeze(tasks,references)
    if meta.get('design')!=expected or manifest!=dict(complete=True,packet_sha256=digest(packet),key_sha256=digest(key),design_sha256=digest(meta)):raise ValueError('frozen artifact mismatch')
    if not isinstance(reviews,list) or not isinstance(packet,list) or not isinstance(key,dict):raise ValueError('review shape')
    ids={p['id'] for p in packet}
    if len(ids)!=len(packet) or ids!=set(key):raise ValueError('packet coverage')
    reviewed={}
    for r in reviews:
        if not isinstance(r,dict) or set(r)!={'id','sha256','verdict','reviewer','rationale'} or r['id'] not in ids or r['id'] in reviewed or r['verdict'] not in VERDICTS or not valid_text(r['reviewer'],200) or not valid_text(r['rationale']):raise ValueError('invalid review')
        if r['sha256']!=key[r['id']]['sha256']:raise ValueError('review is not bound to exact attempt')
        reviewed[r['id']]=r
    if set(reviewed)!=ids:raise ValueError('incomplete independent review')
    taskmap={t['id']:t['statement'] for t in tasks};cells={};attempts={}
    for p in packet:
        k=key[p['id']];r=reviewed[p['id']]
        if digest(p)!=k['sha256'] or k['task'] not in taskmap or p['statement']!=taskmap[k['task']] or k['arm'] not in ARMS or type(k['step']) is not int or not 0<=k['step']<meta['calls_per_arm']:raise ValueError('attempt mismatch')
        cell=(k['task'],k['arm'],k['step'])
        if cell in cells:raise ValueError('duplicate attempt')
        cells[cell]=r['verdict']
        if r['verdict'] in ('proved','refuted') and r['verdict']!=references[k['task']]['expected']:raise ValueError('review/reference conflict; adjudication required')
        attempts.setdefault((k['task'],k['arm']),[]).append(r['verdict'])
    expected_cells={(t['id'],a,i) for t in tasks for a in ARMS for i in range(meta['calls_per_arm'])}
    if set(cells)!=expected_cells:raise ValueError('unmatched experiment')
    summary={}
    for a in ARMS:
        solved=[t['id'] for t in tasks if any(v in ('proved','refuted') for v in attempts[t['id'],a])]
        summary[a]=dict(solved=len(solved),total=len(tasks),solved_tasks=solved,attempts=len(tasks)*meta['calls_per_arm'])
    b=set(summary['blind']['solved_tasks']);a=set(summary['adaptive']['solved_tasks'])
    return dict(summary=summary,paired=dict(both=len(a&b),adaptive_only=len(a-b),blind_only=len(b-a),neither=len(tasks)-len(a|b)),scope='external reviewer judgments; independence and correctness are not machine-certified; no novelty or training-data exclusion claim')

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    a=sub.add_parser('freeze');a.add_argument('tasks');a.add_argument('references');a.add_argument('design')
    a=sub.add_parser('run');a.add_argument('tasks');a.add_argument('design');a.add_argument('config');a.add_argument('out');a.add_argument('--calls',type=int,default=4);a.add_argument('--timeout',type=float,default=60);a.add_argument('--seed',type=int,default=0)
    a=sub.add_parser('score');a.add_argument('tasks');a.add_argument('references');a.add_argument('run_dir');a.add_argument('reviews')
    a=p.parse_args()
    if a.action=='freeze':write(a.design,freeze(read_json(a.tasks),read_json(a.references)));return
    if a.action=='run':r=run(read_json(a.tasks),read_json(a.design),read_json(a.config)['worker'],a.out,a.calls,a.timeout,a.seed)
    else:
        d=Path(a.run_dir)
        r=score(read_json(a.tasks),read_json(a.references),read_json(d/'design.json'),read_json(d/'review-packet.json'),read_json(d/'private-key.json'),read_json(d/'run-manifest.json'),read_json(a.reviews))
    print(json.dumps(r,indent=2))
if __name__=='__main__':main()
