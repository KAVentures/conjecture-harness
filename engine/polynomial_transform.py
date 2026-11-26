"""Exact real univariate translation, with original-statement certificate replay."""
from fractions import Fraction as F
from math import comb
import json
import polynomial as p
from discovery import check,frontier,record,fingerprint


def shift(terms,offset):
    """Return coefficients of Q(z)=P(z+offset), in exact rational arithmetic."""
    out={}
    for (k,),c in terms.items():
        for j in range(k+1):
            e=(j,);out[e]=out.get(e,F(0))+c*comb(k,j)*offset**(k-j)
    return {e:c for e,c in out.items() if c}


def transport(cert,h):
    k=cert['kind']
    if k=='identity':return cert
    if k=='point':return dict(kind='point',point=[str(F(cert['point'][0])+h)])
    if k!='sos':raise ValueError('unsupported certificate')
    # A nonnegative even monomial is a weighted square. Translate each square.
    squares=list(cert['squares'])+[[str(c),[[[e[0]//2],'1']]] for e,c in p.terms(cert['monomials'],1).items()]
    if len(squares)>32:raise ValueError('translated certificate too large')
    return dict(kind='sos',monomials=[],squares=[[w,p.encode(shift(p.terms(q,1,4),-h))] for w,q in squares])


def solve(s,budget=64):
    s=p.normalize(s)
    unknown=dict(status='unknown',certificate=None,translation=None,tested=0)
    if s['domain']!='real' or len(s['variables'])!=1:return unknown
    terms=p.terms(s['terms'],1)
    d=max((e[0] for e in terms),default=0)
    if d<2:return unknown
    h=-terms.get((d-1,),F(0))/(d*terms[(d,)])
    if not h or len(str(h))>80:return unknown
    try:
        shifted=dict(s,terms=p.encode(shift(terms,h)))
        result=p.solve(shifted,budget)
        if result['status']=='unknown':return dict(unknown,translation=str(h),tested=result['tested'])
        cert=transport(result['certificate'],h)
        # Recheck on the original statement, not merely the transformed problem.
        if not p.replay(s,cert):raise ArithmeticError('translated certificate failed replay')
        return dict(status=result['status'],certificate=cert,translation=str(h),tested=result['tested'])
    except ValueError:return unknown


def auto_discharge(g,limit=2):
    check(g);count=0
    for i in frontier(g):
        if count>=limit:break
        if i not in frontier(g):continue
        try:s=p.parse_statement(g['nodes'][i]['statement'])
        except (ValueError,TypeError):continue
        if s['domain']!='real' or len(s['variables'])!=1:continue
        prior=[o for k,o in g['observations'].items() if o['focus']==i and k.startswith('poly-')]
        if not prior or any(o['focus']==i and k.startswith('shift-') for k,o in g['observations'].items()):continue
        count+=1;r=solve(s);detail=json.dumps(r,sort_keys=True)
        if len(detail)>20000:continue
        ident='shift-'+fingerprint(i+'\n'+detail)[:32];status=r['status']
        ops=[dict(op='observe',id=ident,focus=i,kind={'proved':'proof_sketch','counterexample':'counterexample','unknown':'experiment'}[status],detail=detail)]
        if status!='unknown':
            if not p.replay(s,r['certificate']):raise ArithmeticError('original certificate failed replay')
            ops.append(dict(op='review_claim',id=i,decision='established' if status=='proved' else 'refuted',evidence='Exact translated certificate replayed on original claim: '+ident))
        g=record(g,'falsify' if status=='counterexample' else 'forward',i,ops,trusted=True)
    return g
