"""Exact consequences of multivariate equality constraints."""
import json
from fractions import Fraction as Q
import polynomial as p
import conditional_theorems as ct
import ideal_consequences as ic
from symbolic_discovery import terms,encode
from discovery import check,frontier,record,fingerprint

def inputs(s):
    s=ct.normalize(s);n=len(s['variables'])
    g=[p.terms(h['terms'],n) for h in s['assumptions'] if h['relation']=='zero']
    if not g:raise ValueError('no equality hypotheses')
    return n,g,p.terms(s['conclusion'],n)

def residual_spec(s,rem):
    return p.normalize(dict(variables=s['variables'],domain=s['domain'],relation='nonnegative',terms=p.encode(rem)))

def replay(s,cert):
    """Verify an identity in the ORIGINAL equality generators, not a basis."""
    try:
        s=ct.normalize(s);n,g,target=inputs(s)
        if not isinstance(cert,dict) or set(cert)!={'kind','power','multipliers','residual'}:return None
        raw=cert['multipliers'];k=cert['power'];kind=cert['kind']
        if not isinstance(raw,list) or len(raw)!=len(g) or type(k) is not int:return None
        total=ic.identity(g,[terms(q,n,12) for q in raw],n)
        if kind=='inconsistent':
            return 'proved' if k==1 and cert['residual'] is None and total=={(0,)*n:Q(1)} else None
        if kind=='zero-power':
            if k not in (2,3) or cert['residual'] is not None:return None
            q=target
            for _ in range(k-1):q=ic.mul(q,target)
            return 'proved' if q==total else None
        if kind!='residual' or k!=1:return None
        rem=ic.add(target,total,Q(-1))
        c=cert['residual']
        if not isinstance(c,dict) or c.get('kind')!='sos':return None
        return 'proved' if p.replay(residual_spec(s,rem),c) else None
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError):return None

def solve(s,pair_budget=96):
    s=ct.normalize(s)
    try:
        n,g,target=inputs(s)
        for kind,k,rem,ms,tested in ic.candidates(g,target,n,pair_budget):
            res=None
            if kind=='residual':
                try:r=p.solve(residual_spec(s,rem),budget=1)
                except ValueError:continue
                if r['status']!='proved':continue
                res=r['certificate']
            try:cert=dict(kind=kind,power=k,multipliers=[encode(q) for q in ms],residual=res)
            except ValueError:continue
            if len(json.dumps(cert))>15000:continue
            if replay(s,cert)!='proved':raise ArithmeticError('ideal certificate failed replay')
            return dict(status='proved',certificate=cert,pairs=tested)
    except ValueError:pass
    return dict(status='unknown',scope='bounded equality-ideal search; not a full real quantifier elimination procedure')

def auto_discharge(g,limit=2):
    check(g);count=0
    for i in frontier(g):
        if count>=limit:break
        if i not in frontier(g):continue
        try:s=ct.parse_statement(g['nodes'][i]['statement']);inputs(s)
        except (ValueError,TypeError):continue
        if any(o['focus']==i and oid.startswith('ideal-consequence-') for oid,o in g['observations'].items()):continue
        r=solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True)
        oid='ideal-consequence-'+fingerprint(i+'\n'+detail)[:32]
        ops=[dict(op='observe',id=oid,focus=i,kind='proof_sketch' if status=='proved' else 'experiment',detail=detail)]
        if status=='proved':ops.append(dict(op='review_claim',id=i,decision='established',evidence='Exact original-generator identity '+oid))
        g=record(g,'forward',i,ops,trusted=True);count+=1
    return g
