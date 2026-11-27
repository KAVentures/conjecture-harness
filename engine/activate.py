"""Single entrypoint for bounded local research, with execution receipts.

No network, model invocation or publication by default. Receipts describe local
actions, not independent proof, chat compliance or scientific effectiveness.
"""
import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path
from activation_contract import ROOT, contract, public_contract, digest, registry, suggest

def revision():
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
            stderr=subprocess.DEVNULL, timeout=3).decode().strip()
    except (OSError, subprocess.SubprocessError):
        return None

def plan(target):
    if not isinstance(target, str) or not target.strip():
        raise ValueError('nonempty target required')
    return dict(schema=1, revision=revision(), contract_sha256=digest(contract()),
                public_contract_sha256=digest(public_contract()),
                registry_sha256=digest((ROOT/'CAPABILITIES.json').read_bytes()),
                target_sha256=digest(target.encode()), target=target,
                routes=suggest(target), commands=registry()['commands'],
                scope='Routing suggestions only; no mathematical tool executed.')

def write_new(path, obj):
    with path.open('x', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write('\n')

def execute(output, target=None, passes=4, seconds=60, worker=None, attempts=4, timeout=30):
    from discovery import check, save, new
    from discovery_tools import run as exact_run
    from proof_audit import audit
    from research_checkpoint import report
    from runtime import read_json
    from harness import coordinator_lock
    if type(passes) is not int or not 1<=passes<=100 or type(attempts) is not int or attempts<1:
        raise ValueError('invalid pass/attempt limits')
    if not all(type(v) in (int,float) and math.isfinite(v) and v>0 for v in (seconds,timeout)):
        raise ValueError('positive finite budgets required')
    if worker is not None and (not isinstance(worker,list) or not worker or
                              not all(isinstance(x,str) and x for x in worker)):
        raise ValueError('trusted worker command array required')
    output=Path(output).resolve()
    if target is not None:
        p=plan(target); g=new(target)
        output.mkdir(parents=True,exist_ok=False)
        write_new(output/'activation.json',p)
        save(output/'state.json',g)
    state=output/'state.json'
    # Separate outer coordinator lock; existing exact/model runners use their own.
    with coordinator_lock(output):
        g=check(read_json(state,limit=32*1024*1024))
        p=plan(g['nodes']['goal']['statement'])
        initial=read_json(output/'activation.json')
        if initial['target_sha256']!=p['target_sha256']:
            raise ValueError('activation target mismatch')
        before=digest(state.read_bytes())
        log=state.with_name(state.name+'.runs')
        old=set(log.glob('*/raw.json')) if log.exists() else set()
        index=0
        while (output/f'receipt-{index:04d}.json').exists():index+=1
        start=time.monotonic()
        exact=exact_run(state,passes,seconds)
        g=check(read_json(state,limit=32*1024*1024)); a=audit(g)
        model=None
        remaining=seconds-(time.monotonic()-start)
        if worker is not None and remaining>0 and a['status']=='unverified' and not a['conflicts']:
            from discovery_run import run
            model=run(state,worker,attempts,remaining,timeout,metareasoning=True)
            g=check(read_json(state,limit=32*1024*1024));a=audit(g)
        logs=[]
        for path in sorted(set(log.glob('*/raw.json'))-old):
            entry=dict(path=str(path.relative_to(output)),sha256=digest(path.read_bytes()))
            prompt=path.with_name('prompt.txt')
            if prompt.is_file():entry['prompt_sha256']=digest(prompt.read_bytes())
            logs.append(entry)
        checkpoint=output/f'checkpoint-{index:04d}.json'
        write_new(checkpoint,report(g))
        receipt=dict(schema=1,mode='runtime' if worker is not None else 'coding',
            activation=p, initial_revision=initial['revision'],
            prior_state_sha256=before,state_sha256=digest(state.read_bytes()),
            exact_execution=exact, model_execution=model, worker_logs=logs,
            audit=a,checkpoint=checkpoint.name,checkpoint_sha256=digest(checkpoint.read_bytes()),
            elapsed_seconds=round(time.monotonic()-start,3),
            skipped=['external model: not configured'] if worker is None else
                (['external model: no unresolved audited frontier or remaining budget'] if model is None else []),
            scope='Local execution evidence, not independent verification of arbitrary prose, novelty or proof of instruction compliance.')
        write_new(output/f'receipt-{index:04d}.json',receipt)
        return receipt

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('plan');p.add_argument('--target',required=True)
    for name in ('run','resume'):
        p=sub.add_parser(name);p.add_argument('--output',required=True)
        if name=='run':p.add_argument('--target',required=True)
        p.add_argument('--passes',type=int,default=4);p.add_argument('--seconds',type=float,default=60)
        p.add_argument('--worker-config');p.add_argument('--attempts',type=int,default=4)
        p.add_argument('--timeout',type=float,default=30)
    a=parser.parse_args()
    if a.command=='plan':result=plan(a.target)
    else:
        worker=None
        if a.worker_config:
            from runtime import read_json
            worker=read_json(a.worker_config)['worker']
        result=execute(a.output,getattr(a,'target',None),a.passes,a.seconds,worker,a.attempts,a.timeout)
    print(json.dumps(result,indent=2,ensure_ascii=False))
    if a.command!='plan' and (result['audit']['conflicts'] or result['audit']['invalid_observations']):
        return 1
    return 0

if __name__=='__main__':sys.exit(main())
