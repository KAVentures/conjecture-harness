"""Projective and segment sign decision, with explicit domain translation."""
import json
import polynomial as p,conditional_theorems as ct,simplex_discovery as sx
import projective_sign as ps
from discovery import check,frontier,record,fingerprint

def inputs(text):
    if text.startswith(p.PREFIX):
        s=p.parse_statement(text)
        if len(s['variables'])!=2 or s['relation']!='nonnegative':raise ValueError('not a binary inequality')
        raw=[p.terms(s['terms'],2)]
        for q in raw:ps.homogeneous(q)
        return 'projective-sign',(raw,[],s['domain'])
    if text.startswith(ct.PREFIX):
        s=ct.parse_statement(text)
        if len(s['variables'])!=2:raise ValueError('not a binary theorem')
        raw=[p.terms(h['terms'],2) for h in s['assumptions']]+[p.terms(s['conclusion'],2)]
        for q in raw:ps.homogeneous(q)
        return 'projective-sign',(raw,[h['relation'] for h in s['assumptions']],s['domain'])
    if text.startswith(sx.PREFIX):
        s=sx.parse_statement(text)
        if len(s['variables'])!=2:raise ValueError('not a segment')
        return 'segment-sign',(p.terms(s['terms'],2),)
    raise ValueError('unsupported projective claim')

def replay(text,cert):
    try:
        kind,args=inputs(text)
        return ps.replay_binary(*args,cert) if kind=='projective-sign' else ps.replay_simplex(*args,cert)
    except (ValueError,TypeError,KeyError):return None

def solve(text):
    try:
        kind,args=inputs(text)
        r=ps.binary(*args) if kind=='projective-sign' else ps.simplex(*args)
    except ValueError:return dict(status='unknown')
    cert=dict(kind=kind,classification=r)
    if len(json.dumps(cert))>15000:return dict(status='unknown')
    if replay(text,cert)!=r['outcome']:raise ArithmeticError('projective certificate replay failed')
    return dict(status=r['outcome'],certificate=cert)

def auto_discharge(g,limit=2):
    check(g);count=0
    for i in frontier(g):
        if count>=limit:break
        if i not in frontier(g):continue
        text=g['nodes'][i]['statement']
        try:inputs(text)
        except (ValueError,TypeError):continue
        if any(o['focus']==i and oid.startswith('projective-') for oid,o in g['observations'].items()):continue
        r=solve(text);status=r['status'];detail=json.dumps(r,sort_keys=True)
        oid='projective-'+fingerprint(i+'\n'+detail)[:32]
        kind={'proved':'proof_sketch','refuted':'counterexample','unknown':'experiment'}[status]
        ops=[dict(op='observe',id=oid,focus=i,kind=kind,detail=detail)]
        if status!='unknown':ops.append(dict(op='review_claim',id=i,decision='established' if status=='proved' else 'refuted',evidence='Exact projective or segment sign certificate: '+oid))
        g=record(g,'falsify' if status=='refuted' else 'forward',i,ops,trusted=True);count+=1
    return g
