"""Dispatch exact indexed and constrained-algebra adapters."""
import json
from discovery import check,frontier,record,fingerprint
import indexed_algebra,simplex_discovery

def auto_discharge(g,limit=2):
    check(g);count=0
    for focus in frontier(g):
        if count>=limit:break
        if focus not in frontier(g):continue
        text=g['nodes'][focus]['statement']
        adapter=next(((name,m) for name,m in [('indexed',indexed_algebra),('simplex',simplex_discovery)] if text.startswith(m.PREFIX)),None)
        if adapter is None:continue
        name,m=adapter
        try:s=m.parse_statement(text)
        except (ValueError,TypeError):continue
        if any(o['focus']==focus and k.startswith(name+'-') for k,o in g['observations'].items()):continue
        r=m.solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True)
        oid=name+'-'+fingerprint(focus+'\n'+detail)[:32]
        if len(detail)>20000:continue
        ops=[dict(op='observe',id=oid,focus=focus,kind={'proved':'proof_sketch','counterexample':'counterexample','unknown':'experiment'}[status],detail=detail)]
        if status!='unknown':
            expected='proved' if status=='proved' else 'refuted'
            if m.replay(s,r['certificate'])!=expected:raise ArithmeticError('structured algebra replay failed')
            ops.append(dict(op='review_claim',id=focus,decision='established' if expected=='proved' else 'refuted',evidence='Exact '+name+' certificate '+oid))
        g=record(g,'falsify' if status=='counterexample' else 'forward',focus,ops,trusted=True);count+=1
    return g
