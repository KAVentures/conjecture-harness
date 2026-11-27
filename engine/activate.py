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

def execute(output, target=None, passes=4, seconds=60, worker=None, attempts=4, timeout=30, campaign=None):
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
        exact=exact_run(state,passes,min(seconds,30) if campaign is not None else seconds)
        g=check(read_json(state,limit=32*1024*1024)); a=audit(g)
        model=None
        campaign_result=None
        remaining=seconds-(time.monotonic()-start)
        if campaign is not None and remaining>0 and a['status']=='unverified' and not a['conflicts'] and not a['invalid_observations']:
            from campaign import run as run_campaign
            campaign_result=run_campaign(state,campaign['commands'],attempts,remaining,timeout,
                campaign['workers'],campaign['wave_attempts'],campaign.get('reviewers',()))
            g=check(read_json(state,limit=32*1024*1024));a=audit(g)
        elif campaign is None and worker is not None and remaining>0 and a['status']=='unverified' and not a['conflicts'] and not a['invalid_observations']:
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
        receipt=dict(schema=1,mode='runtime' if worker is not None or campaign is not None else 'coding',
            activation=p, initial_revision=initial['revision'],
            prior_state_sha256=before,state_sha256=digest(state.read_bytes()),
            exact_execution=exact, model_execution=model, campaign_execution=campaign_result, worker_logs=logs,
            audit=a,checkpoint=checkpoint.name,checkpoint_sha256=digest(checkpoint.read_bytes()),
            elapsed_seconds=round(time.monotonic()-start,3),
            skipped=['external model: not configured'] if worker is None and campaign is None else
                (['external model: no unresolved audited frontier or remaining budget'] if model is None and campaign_result is None else []),
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
        p.add_argument('--passes',type=int,default=4);p.add_argument('--seconds',type=float)
        p.add_argument('--worker-config');p.add_argument('--attempts',type=int)
        p.add_argument('--timeout',type=float)
        p.add_argument('--profile',choices=['quick','research'],help='research by default with configured workers')
        p.add_argument('--workers',type=int,default=5);p.add_argument('--wave-attempts',type=int,default=10)
        p.add_argument('--verbose',action='store_true',help='emit full internal receipt instead of compact research status')
    a=parser.parse_args()
    if a.command=='plan':result=plan(a.target)
    else:
        from campaign import RESEARCH_SECONDS, RESEARCH_ATTEMPTS, RESEARCH_TIMEOUT, public_result
        worker=None;campaign=None;cfg={}
        if a.worker_config:
            from runtime import read_json
            cfg=read_json(a.worker_config)
        profile=a.profile or ('research' if a.worker_config else 'quick')
        if profile=='research':
            if not a.worker_config:parser.error('research profile requires an explicitly trusted --worker-config; otherwise use the coding loop')
            commands=cfg['workers'] if 'workers' in cfg else [cfg['worker']]
            campaign=dict(commands=commands,workers=a.workers,wave_attempts=a.wave_attempts,reviewers=cfg.get('reviewers',[]))
        elif a.worker_config:
            worker=cfg['worker'] if 'worker' in cfg else cfg['workers'][0]
        seconds=a.seconds if a.seconds is not None else (RESEARCH_SECONDS if campaign else 60)
        attempts=a.attempts if a.attempts is not None else (RESEARCH_ATTEMPTS if campaign else 4)
        timeout=a.timeout if a.timeout is not None else (RESEARCH_TIMEOUT if campaign else 30)
        result=execute(a.output,getattr(a,'target',None),a.passes,seconds,worker,attempts,timeout,campaign)
    print(json.dumps(public_result(result) if a.command!='plan' and campaign is not None and not a.verbose else result,indent=2,ensure_ascii=False))
    if a.command!='plan' and (result['audit']['conflicts'] or result['audit']['invalid_observations']):
        return 1
    return 0

if __name__=='__main__':sys.exit(main())
