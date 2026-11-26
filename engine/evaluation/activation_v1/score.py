"""Aggregate externally reviewed four-arm cells; no automated proof judgment."""
import argparse
import json
from pathlib import Path

ARMS=('ordinary','legacy','instruction','runtime')
VERDICTS=('proved','refuted','partial','unresolved','invalid')
def score(rows):
    if not isinstance(rows,list) or not rows:
        raise ValueError('nonempty reviewed cells required')
    cells={}
    for r in rows:
        if not isinstance(r,dict) or not isinstance(r.get('target'),str) or not r['target']:
            raise ValueError('missing target')
        if r.get('arm') not in ARMS or r.get('verdict') not in VERDICTS:
            raise ValueError('unknown arm or verdict')
        if not isinstance(r.get('reviewer'),str) or not r['reviewer'].strip():
            raise ValueError('reviewer identifier required')
        if type(r.get('trace_observed')) is not bool:
            raise ValueError('trace observation status required')
        for k in ('verified_lemmas','meaningful_pivots','tool_calls'):
            if type(r.get(k)) is not int or r[k]<0:raise ValueError('invalid metric '+k)
        key=(r['target'],r['arm'])
        if key in cells:raise ValueError('duplicate cell')
        cells[key]=r
    targets=sorted({t for t,_ in cells})
    if set(cells)!={(t,a) for t in targets for a in ARMS}:
        raise ValueError('incomplete paired design')
    summary={}
    for a in ARMS:
        rs=[cells[t,a] for t in targets]
        summary[a]=dict(reviewed_solved=sum(r['verdict'] in ('proved','refuted') for r in rs),
                        total=len(rs),observed_traces=sum(r['trace_observed'] for r in rs),
                        **{k:sum(r[k] for r in rs) for k in ('verified_lemmas','meaningful_pivots','tool_calls')})
    return dict(scope='Externally supplied reviews; not independent verification or causal inference.',arms=summary)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('reviews',type=Path);a=p.parse_args()
    print(json.dumps(score(json.loads(a.reviews.read_text())),indent=2))
