"""Run a canonical research target end-to-end with audit and reproducible evidence.

No model calls by default. A model-free fixed point is not a proof or a
negative answer to an open conjecture. External worker configuration is
optional and must be operator-supplied.
"""
import argparse,json,subprocess,sys,time
from pathlib import Path
from discovery import new,save,check
from discovery_tools import run as exact_run
from proof_audit import audit
from runtime import read_json
from proof_bundle import export as bundle_export,replay as bundle_replay

def revision():
    try:return subprocess.check_output(['git','rev-parse','HEAD'],text=True,stderr=subprocess.DEVNULL,timeout=3).strip()
    except (OSError,subprocess.SubprocessError):return None

def execute(statement,output,passes=4,seconds=60,worker=None,attempts=4,timeout=30):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    state=output/'state.json';save(state,new(statement));start=time.monotonic()
    report=exact_run(state,passes,seconds)
    g=check(read_json(state,limit=32*1024*1024));r=audit(g);model_report=None
    if worker is not None and r['status']=='unverified' and not r['conflicts'] and time.monotonic()-start<seconds:
        from discovery_run import run
        model_report=run(state,worker,attempts,max(.01,seconds-(time.monotonic()-start)),timeout,metareasoning=True)
        g=check(read_json(state,limit=32*1024*1024));r=audit(g)
    bundle=None
    if r['status']=='proved' and not r['invalid_observations']:
        try:
            b=bundle_export(g)
            if bundle_replay(b,statement):
                (output/'proof-bundle.json').write_text(json.dumps(b,indent=2),encoding='utf-8');bundle='proof-bundle.json'
        except ValueError:pass
    result=dict(revision=revision(),python=sys.version,target_sha256=g['target_sha256'],exact_run=report,model_run=model_report,
                audit=r,proof_bundle=bundle,elapsed_seconds=round(time.monotonic()-start,3),
                scope='audit status is definitive only for supported replay; unknown/fixed point is not a proof; no novelty claim')
    (output/'report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--statement-file');a.add_argument('--target',choices=['lih-wang'])
    a.add_argument('--output',required=True);a.add_argument('--passes',type=int,default=4);a.add_argument('--seconds',type=float,default=60)
    a.add_argument('--worker-config');a.add_argument('--attempts',type=int,default=4);a.add_argument('--timeout',type=float,default=30)
    q=a.parse_args()
    if bool(q.statement_file)==bool(q.target):a.error('choose exactly one target source')
    if q.target=='lih-wang':
        import matrix_permanent as m
        statement=m.statement(dict(kind='lih-wang'))
    else:statement=Path(q.statement_file).read_text(encoding='utf-8').strip()
    worker=read_json(q.worker_config)['worker'] if q.worker_config else None
    r=execute(statement,q.output,q.passes,q.seconds,worker,q.attempts,q.timeout)
    print(json.dumps(r,indent=2))
    if r['audit']['conflicts'] or r['audit']['invalid_observations']:a.exit(1)
if __name__=='__main__':main()
