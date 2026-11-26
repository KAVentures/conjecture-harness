"""Exact sign-cell discharge for structured univariate implications."""
import json
from fractions import Fraction as Q
import polynomial as p
import conditional_theorems as ct
import sign_cells as sc
from discovery import check,frontier,record,fingerprint

def inputs(s):
    s=ct.normalize(s)
    if len(s['variables'])!=1:raise ValueError('not univariate')
    def dense(ts):
        q=p.terms(ts,1)
        return [q.get((k,),Q(0)) for k in range(1+max((e[0] for e in q),default=0))]
    return [dense(h['terms']) for h in s['assumptions']]+[dense(s['conclusion'])],[h['relation'] for h in s['assumptions']],s['domain']

def replay(s,cert):
    try:return sc.replay(*inputs(s),cert)
    except (ValueError,TypeError,KeyError):return None

def solve(s):
    try:classification=sc.classify(*inputs(s))
    except ValueError:return dict(status='unknown')
    cert=dict(kind='sign-cells',classification=classification)
    if len(json.dumps(cert))>15000:return dict(status='unknown')
    if replay(s,cert)!=classification['outcome']:raise ArithmeticError('sign-cell replay failed')
    return dict(status=classification['outcome'],certificate=cert)

def auto_discharge(g,limit=2):
    check(g);count=0
    for i in frontier(g):
        if count>=limit:break
        if i not in frontier(g):continue
        try:s=ct.parse_statement(g['nodes'][i]['statement']);inputs(s)
        except (ValueError,TypeError):continue
        if any(o['focus']==i and oid.startswith('sign-cell-') for oid,o in g['observations'].items()):continue
        r=solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True)
        oid='sign-cell-'+fingerprint(i+'\n'+detail)[:32]
        kind={'proved':'proof_sketch','refuted':'counterexample','unknown':'experiment'}[status]
        ops=[dict(op='observe',id=oid,focus=i,kind=kind,detail=detail)]
        if status!='unknown':ops.append(dict(op='review_claim',id=i,decision='established' if status=='proved' else 'refuted',evidence='Exact sign-invariant cell certificate: '+oid))
        g=record(g,'falsify' if status=='refuted' else 'forward',i,ops,trusted=True);count+=1
    return g
