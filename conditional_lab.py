"""Dispatch exact conditional theorem claims and bind certificate evidence."""
import json
from discovery import check,frontier,record,fingerprint
import conditional_theorems as ct

def auto_discharge(g,limit=2):
    check(g);count=0
    for focus in frontier(g):
        if count>=limit:break
        if focus not in frontier(g):continue
        try:s=ct.parse_statement(g['nodes'][focus]['statement'])
        except (ValueError,TypeError):continue
        if any(o['focus']==focus and k.startswith('conditional-') for k,o in g['observations'].items()):continue
        r=ct.solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True)
        if len(detail)>20000:continue
        oid='conditional-'+fingerprint(focus+'\n'+detail)[:32]
        ops=[dict(op='observe',id=oid,focus=focus,kind={'proved':'proof_sketch','counterexample':'counterexample','unknown':'experiment'}[status],detail=detail)]
        if status!='unknown':
            expected='proved' if status=='proved' else 'refuted'
            if ct.replay(s,r['certificate'])!=expected:raise ArithmeticError('conditional theorem replay failed')
            ops.append(dict(op='review_claim',id=focus,decision='established' if expected=='proved' else 'refuted',evidence='Exact conditional certificate '+oid))
        g=record(g,'falsify' if status=='counterexample' else 'forward',focus,ops,trusted=True);count+=1
    return g
