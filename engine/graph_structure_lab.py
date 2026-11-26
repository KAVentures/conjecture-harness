"""Install checked fixed-graph structural bounds in the discovery graph."""
import json
import graph_structure as gs
from discovery import check,frontier,record,fingerprint

def auto_discharge(g,limit=2):
    check(g);count=0
    for i in frontier(g):
        if count>=limit:break
        if i not in frontier(g):continue
        try:s=gs.parse_statement(g['nodes'][i]['statement'])
        except (ValueError,TypeError):continue
        if any(o['focus']==i and oid.startswith('structure-') for oid,o in g['observations'].items()):continue
        r=gs.solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True,separators=(',',':'))
        if len(detail)>20000:continue
        oid='structure-'+fingerprint(i+'\n'+detail)[:32]
        kind={'proved':'proof_sketch','refuted':'counterexample','unknown':'experiment'}[status]
        ops=[dict(op='observe',id=oid,focus=i,kind=kind,detail=detail)]
        if status!='unknown':
            if gs.replay(s,r['certificate'])!=status:raise ArithmeticError('structural replay failed')
            ops.append(dict(op='review_claim',id=i,decision='established' if status=='proved' else 'refuted',evidence='Exact graph structural certificate '+oid))
        g=record(g,'falsify' if status=='refuted' else 'forward',i,ops,trusted=True);count+=1
    return g
