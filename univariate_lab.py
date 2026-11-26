"""A separate exact sign decision adapter for univariate nonnegativity."""
import json
from fractions import Fraction as Q
import polynomial as p
import univariate_sign as us
from discovery import check,frontier,record,fingerprint

def coefficients(s):
    s=p.normalize(s)
    if len(s['variables'])!=1 or s['relation']!='nonnegative':raise ValueError('not a univariate sign problem')
    terms=p.terms(s['terms'],1)
    return [terms.get((k,),Q(0)) for k in range(1+max((e[0] for e in terms),default=0))]

def replay(s,cert):
    try:return us.replay(coefficients(s),s['domain'],cert)
    except (ValueError,TypeError,KeyError):return None

def solve(s):
    try:
        result=us.classify(coefficients(s),s['domain'])
    except ValueError:return dict(status='unknown')
    cert=dict(kind='sturm-sign',classification=result)
    if replay(s,cert)!=result['outcome']:raise ArithmeticError('sign replay failed')
    return dict(status=result['outcome'],certificate=cert)

def auto_discharge(g,limit=2):
    check(g);count=0
    for i in frontier(g):
        if count>=limit:break
        if i not in frontier(g):continue
        try:s=p.parse_statement(g['nodes'][i]['statement']);coefficients(s)
        except (ValueError,TypeError):continue
        if any(o['focus']==i and oid.startswith('sturm-') for oid,o in g['observations'].items()):continue
        r=solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True)
        oid='sturm-'+fingerprint(i+'\n'+detail)[:32]
        kind={'proved':'proof_sketch','refuted':'counterexample','unknown':'experiment'}[status]
        ops=[dict(op='observe',id=oid,focus=i,kind=kind,detail=detail)]
        if status!='unknown':ops.append(dict(op='review_claim',id=i,decision='established' if status=='proved' else 'refuted',evidence='Exact Sturm sign classification (negative existence, not necessarily a point): '+oid))
        g=record(g,'falsify' if status=='refuted' else 'forward',i,ops,trusted=True);count+=1
    return g
