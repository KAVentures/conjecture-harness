"""Shared bounded graph dispatcher for exact discovery families."""
import json
def discharge(g,parser,solve,replay,prefix,limit=1):
    from discovery import check,frontier,record,fingerprint
    check(g);count=0
    for focus in frontier(g):
        if count>=limit:break
        if focus not in frontier(g):continue
        try:s=parser(g['nodes'][focus]['statement'])
        except (ValueError,TypeError):continue
        if any(o['focus']==focus and i.startswith(prefix) for i,o in g['observations'].items()):continue
        r=solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True)
        if len(detail)>20000:continue
        oid=prefix+fingerprint(focus+'\n'+detail)[:32]
        ops=[dict(op='observe',id=oid,focus=focus,kind={'proved':'proof_sketch','counterexample':'counterexample','unknown':'experiment'}[status],detail=detail)]
        if status!='unknown':
            expected='proved' if status=='proved' else 'refuted'
            if replay(s,r['certificate'])!=expected:raise ArithmeticError('certificate replay failed')
            ops.append(dict(op='review_claim',id=focus,decision='established' if expected=='proved' else 'refuted',evidence='Exact certificate '+oid))
        g=record(g,'falsify' if status=='counterexample' else 'forward',focus,ops,trusted=True);count+=1
    return g
