"""Proof graph adapter for universal nonlinear graph consequences."""
import json
import graph_nonlinear as gn
from discovery import check,frontier,record,fingerprint

def auto_discharge(g,limit=2):
    check(g);count=0
    for i in frontier(g):
        if count>=limit:break
        if i not in frontier(g):continue
        try:s=gn.parse_statement(g['nodes'][i]['statement'])
        except (ValueError,TypeError):continue
        if any(o['focus']==i and oid.startswith('graph-polynomial-') for oid,o in g['observations'].items()):continue
        r=gn.solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True)
        if len(detail)>20000:continue
        oid='graph-polynomial-'+fingerprint(i+'\n'+detail)[:32]
        ops=[dict(op='observe',id=oid,focus=i,kind='proof_sketch' if status=='proved' else 'experiment',detail=detail)]
        if status=='proved':
            if gn.replay(s,r['certificate'])!='proved':raise ArithmeticError('graph polynomial replay failed')
            ops.append(dict(op='review_claim',id=i,decision='established',evidence='Exact polynomial consequence of applicable graph theorems '+oid))
        g=record(g,'forward',i,ops,trusted=True);count+=1
    return g
