"""Finite bound proof-state adapter. Never upgrades finite proof to capacity proof."""
import json
from discovery import check,frontier,record,fingerprint
from finite_power import parse_statement,search,replay,packing,find_symmetry


def auto_discharge(g,limit=1):
    check(g);count=0
    for i in frontier(g):
        if count>=limit:break
        if i not in frontier(g):continue
        try:s=parse_statement(g['nodes'][i]['statement'])
        except (ValueError,TypeError):continue
        if any(k.startswith('finite-power-') and o['focus']==i for k,o in g['observations'].items()):continue
        count+=1;r=search(s,budget=500,perms=find_symmetry(s));detail=json.dumps(r,sort_keys=True);oid='finite-power-'+fingerprint(i+'\n'+detail)[:24]
        if len(detail)>20000:continue
        status=r['status'];ops=[dict(op='observe',id=oid,focus=i,kind={'proved':'proof_sketch','counterexample':'counterexample','unknown':'experiment'}[status],detail=detail)]
        if status!='unknown':
            ok=replay(s,r['certificate']) if status=='proved' else len(r['witness'])>s['upper'] and packing(s,r['witness'])
            if not ok:raise ArithmeticError('finite certificate failed replay')
            ops.append(dict(op='review_claim',id=i,decision='established' if status=='proved' else 'refuted',evidence='Exact finite strong-power certificate in '+oid))
        g=record(g,'falsify' if status=='counterexample' else 'forward',i,ops,trusted=True)
    return g
