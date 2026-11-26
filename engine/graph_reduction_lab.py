"""Replay structural reductions on reachable canonical capacity claims."""
import json
from discovery import check,frontier,record,fingerprint
from capacity import parse_statement,replay_counterexample
from graph_reduction import solve,replay


def auto_discharge(g,limit=1):
    check(g);count=0
    for i in frontier(g):
        if count>=limit:break
        if i not in frontier(g):continue
        try:s=parse_statement(g['nodes'][i]['statement'])
        except (ValueError,TypeError):continue
        if not any(k.startswith('capacity-') and o['focus']==i for k,o in g['observations'].items()):continue
        if any(k.startswith('graph-reduction-') and o['focus']==i for k,o in g['observations'].items()):continue
        count+=1;r=solve(s);detail=json.dumps(r,sort_keys=True);oid='graph-reduction-'+fingerprint(i+'\n'+detail)[:24]
        if len(detail)>20000:continue
        status=r['status'];ops=[dict(op='observe',id=oid,focus=i,kind={'proved':'proof_sketch','counterexample':'counterexample','unknown':'experiment'}[status],detail=detail)]
        if status!='unknown':
            c=r['certificate'];ok=replay(s,c) if status=='proved' else replay_counterexample(s,c['words'])
            if not ok:raise ArithmeticError('graph reduction evidence failed replay')
            ops.append(dict(op='review_claim',id=i,decision='established' if status=='proved' else 'refuted',evidence='Exact structural capacity certificate in '+oid))
        g=record(g,'falsify' if status=='counterexample' else 'forward',i,ops,trusted=True)
    return g
