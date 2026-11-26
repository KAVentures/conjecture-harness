"""Transfer exact graph-capacity certificates into the immutable proof state."""
import json
from discovery import check,frontier,record,fingerprint
from capacity import parse_statement,solve,replay,replay_counterexample


def auto_discharge(g,limit=1):
    check(g);count=0
    for i in frontier(g):
        if count>=limit:break
        if i not in frontier(g):continue
        try:s=parse_statement(g['nodes'][i]['statement'])
        except (ValueError,TypeError):continue
        if any(k.startswith('capacity-') and o['focus']==i for k,o in g['observations'].items()):continue
        count+=1;r=solve(s);detail=json.dumps(r,sort_keys=True);oid='capacity-'+fingerprint(i+'\n'+detail)[:24]
        if len(detail)>20000:continue
        status=r['status'];ops=[dict(op='observe',id=oid,focus=i,kind={'proved':'proof_sketch','counterexample':'counterexample','unknown':'experiment'}[status],detail=detail)]
        if status!='unknown':
            c=r['certificate'];ok=replay(s,c) if status=='proved' else replay_counterexample(s,c['words'])
            if not ok:raise ArithmeticError('capacity replay failed')
            ops.append(dict(op='review_claim',id=i,decision='established' if status=='proved' else 'refuted',evidence='Exact graph capacity certificate in '+oid))
        g=record(g,'falsify' if status=='counterexample' else 'forward',i,ops,trusted=True)
    return g
