"""Bind exact graph counterexamples to canonical statements in a proof-state graph."""
import argparse,json
from pathlib import Path
from discovery import check,record,save,fingerprint
from graph_lemma import statement,search,replay
from runtime import read_json
from harness import coordinator_lock


def falsify(g, focus, spec, max_n=5, budget=40000, strategy='families_first'):
    check(g)
    if g['nodes'][focus]['statement']!=statement(spec):
        raise ValueError('claim does not exactly match canonical graph statement; no status change')
    if g['nodes'][focus]['status']!='open':raise ValueError('claim already reviewed')
    report=search(spec,max_n,budget,strategy)
    detail=json.dumps(report,sort_keys=True)
    ident='lab-'+fingerprint(focus+'\n'+detail)[:32]
    if ident in g['observations']:return g,report
    obs={'op':'observe','id':ident,'focus':focus,'kind':'counterexample' if report['status']=='counterexample' else 'experiment','detail':detail}
    ops=[obs]
    if report['status']=='counterexample':
        if not replay(spec,report['witness'])['counterexample']:raise ValueError('counterexample replay failed')
        ops.append({'op':'review_claim','id':focus,'decision':'refuted','evidence':'Exact canonical claim; graph_lemma.replay independently checked witness in observation '+ident})
    return record(g,'falsify',focus,ops,trusted=True),report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('state',type=Path);p.add_argument('focus');p.add_argument('spec',type=Path);p.add_argument('--max-n',type=int,default=5);p.add_argument('--budget',type=int,default=40000);p.add_argument('--strategy',choices=['exhaustive','families_first'],default='families_first');a=p.parse_args()
    path=a.state.resolve();log=path.with_name(path.name+'.runs');log.mkdir(exist_ok=True)
    with coordinator_lock(log):
        g,report=falsify(read_json(path,limit=32*1024*1024),a.focus,read_json(a.spec),a.max_n,a.budget,a.strategy);save(path,g)
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
