"""Install exact weighted AM-GM polynomial certificates."""
import json
import polynomial as p
import amgm_certificates as a
from discovery import check,frontier,record,fingerprint

def replay(s,cert):
    try:
        s=p.normalize(s)
        return 'proved' if s['relation']=='nonnegative' and a.replay(p.terms(s['terms'],len(s['variables'])),s['domain'],cert) else None
    except (ValueError,TypeError,KeyError,ArithmeticError):return None

def solve(s,budget=512):
    s=p.normalize(s)
    if s['relation']!='nonnegative':return dict(status='unknown')
    cert,tested=a.solve(p.terms(s['terms'],len(s['variables'])),s['domain'],budget)
    if cert is None:return dict(status='unknown',tested=tested)
    if replay(s,cert)!='proved':raise ArithmeticError('AM-GM claim replay failed')
    return dict(status='proved',certificate=cert,tested=tested)

def auto_discharge(g,limit=2):
    check(g);count=0
    for i in frontier(g):
        if count>=limit:break
        if i not in frontier(g):continue
        try:s=p.parse_statement(g['nodes'][i]['statement'])
        except (ValueError,TypeError):continue
        if s['relation']!='nonnegative' or any(o['focus']==i and oid.startswith('amgm-') for oid,o in g['observations'].items()):continue
        r=solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True)
        if len(detail)>20000:continue
        oid='amgm-'+fingerprint(i+'\n'+detail)[:32]
        ops=[dict(op='observe',id=oid,focus=i,kind='proof_sketch' if status=='proved' else 'experiment',detail=detail)]
        if status=='proved':ops.append(dict(op='review_claim',id=i,decision='established',evidence='Exact weighted AM-GM certificate '+oid))
        g=record(g,'forward',i,ops,trusted=True);count+=1
    return g
