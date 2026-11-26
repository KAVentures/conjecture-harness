"""Bind parameterized induction certificates to exact research claims."""
import json
from discovery import check,frontier,record,fingerprint
from symbolic_discovery import parse_statement,solve,replay
def auto_discharge(g,limit=2):
    check(g);count=0
    for i in frontier(g):
        if count>=limit:break
        if i not in frontier(g):continue
        try:s=parse_statement(g['nodes'][i]['statement'])
        except (ValueError,TypeError):continue
        if any(o['focus']==i and k.startswith('symbolic-') for k,o in g['observations'].items()):continue
        r=solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True)
        oid='symbolic-'+fingerprint(i+'\n'+detail)[:32]
        ops=[dict(op='observe',id=oid,focus=i,kind={'proved':'proof_sketch','counterexample':'counterexample','unknown':'experiment'}[status],detail=detail)]
        if status!='unknown':
            expected='proved' if status=='proved' else 'refuted'
            if replay(s,r['certificate'])!=expected:raise ArithmeticError('induction replay failed')
            ops.append(dict(op='review_claim',id=i,decision='established' if expected=='proved' else 'refuted',evidence='Symbolic induction certificate '+oid))
        g=record(g,'falsify' if status=='counterexample' else 'forward',i,ops,trusted=True);count+=1
    return g
