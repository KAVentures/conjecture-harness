"""Counterexample-guided exact synthesis of shared inequality parameters.

Existential rational constants are chosen once; all polynomial inequalities
must hold on the entire same affine box. Finite cuts guide discovery but
never establish universality. A finite contradiction certificate can refute
the whole template, not an unrelated parent conjecture.
"""
import json
from fractions import Fraction as Q
from affine import rational
from runtime import strict_json
from affine_face_lab import normalize as face_normalize, data as face_data, solve as face_solve, replay as face_replay
from affine_chart_lab import decode_polynomial,encode_polynomial,solve as chart_solve,replay as chart_replay
from inequality_invention import add
from rational_cone import solve as cone_solve
from discovery import check,frontier,record,fingerprint

PREFIX='Shared rational inequality template: '

def normalize(s):
    if not isinstance(s,dict) or set(s)!={'dimension','rows','rhs','parameter_bounds','parameter_equalities','parameter_rhs','polynomials'}:
        raise ValueError('template shape')
    domain=face_normalize(dict(dimension=s['dimension'],rows=s['rows'],rhs=s['rhs'],terms=[]))
    n=domain['dimension'];bounds=s['parameter_bounds'];eq=s['parameter_equalities'];rhs=s['parameter_rhs'];ps=s['polynomials']
    if not isinstance(bounds,list) or not 1<=len(bounds)<=6 or not isinstance(eq,list) or len(eq)>8 or not isinstance(rhs,list) or len(eq)!=len(rhs) or not isinstance(ps,list) or not 1<=len(ps)<=6:
        raise ValueError('template bounds')
    m=len(bounds);bs=[]
    for pair in bounds:
        if not isinstance(pair,list) or len(pair)!=2:raise ValueError('parameter interval')
        l,u=map(rational,pair)
        if l>u:raise ValueError('empty parameter interval')
        bs.append([str(l),str(u)])
    if any(not isinstance(r,list) or len(r)!=m for r in eq):
        raise ValueError('parameter equality width')
    rows=[[str(rational(v)) for v in r] for r in eq];b=[str(rational(v)) for v in rhs]
    polys=[]
    for p in ps:
        if not isinstance(p,dict) or set(p)!={'base','directions'} or not isinstance(p['directions'],list) or len(p['directions'])!=m:
            raise ValueError('polynomial template shape')
        polys.append(dict(base=encode_polynomial(decode_polynomial(p['base'],n)),
                          directions=[encode_polynomial(decode_polynomial(q,n)) for q in p['directions']]))
    return dict(dimension=n,rows=domain['rows'],rhs=domain['rhs'],parameter_bounds=bs,
                parameter_equalities=rows,parameter_rhs=b,polynomials=polys)

def statement(s):
    return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))

def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('wrong statement type')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical statement')
    return s

def domain(s,terms):
    return dict(dimension=s['dimension'],rows=s['rows'],rhs=s['rhs'],terms=terms)

def evaluate(p,x):
    from math import prod
    return sum((c*prod(v**k for v,k in zip(x,e)) for e,c in p.items()),Q(0))

def feasible_point(s,raw):
    if not isinstance(raw,list) or len(raw)!=s['dimension']:raise ValueError('point size')
    x=list(map(rational,raw))
    if any(not 0<=v<=1 for v in x) or any(sum(Q(a)*v for a,v in zip(row,x))!=Q(b) for row,b in zip(s['rows'],s['rhs'])):
        raise ValueError('point outside original domain')
    return x

def constraints(s,cuts):
    """Rows c+a.theta>=0 necessary for all valid parameter choices."""
    m=len(s['parameter_bounds']);rows=[]
    for i,(l,u) in enumerate(s['parameter_bounds']):
        d=[Q(j==i) for j in range(m)]
        rows.append([-Q(l)]+d);rows.append([Q(u)]+[-v for v in d])
    for a,b in zip(s['parameter_equalities'],s['parameter_rhs']):
        row=[-Q(b)]+list(map(Q,a));rows.extend([row,[-v for v in row]])
    if not isinstance(cuts,list) or len(cuts)>48:raise ValueError('cut count')
    for cut in cuts:
        if not isinstance(cut,dict) or set(cut)!={'inequality','point'}:raise ValueError('cut shape')
        i=cut['inequality']
        if type(i) is not int or not 0<=i<len(s['polynomials']):raise ValueError('inequality index')
        x=feasible_point(s,cut['point']);p=s['polynomials'][i];n=s['dimension']
        rows.append([evaluate(decode_polynomial(q,n),x) for q in [p['base'],*p['directions']]])
    return rows

def parameter_ok(rows,theta):
    return all(r[0]+sum(a*v for a,v in zip(r[1:],theta))>=0 for r in rows)

def instantiate(s,i,theta):
    p=s['polynomials'][i];n=s['dimension'];q=decode_polynomial(p['base'],n)
    for r,w in zip(p['directions'],theta):
        q=add(q,decode_polynomial(r,n),w)
    return face_normalize(domain(s,encode_polynomial(q)))

def candidate(s,rows):
    """Exact finite feasibility via shifted nonnegative variables and slacks."""
    m=len(s['parameter_bounds']);lo=[Q(l) for l,_ in s['parameter_bounds']]
    cols=[{i:r[j+1] for i,r in enumerate(rows) if r[j+1]} for j in range(m)]
    cols.extend({i:Q(-1)} for i in range(len(rows)))
    target={i:-r[0]-sum(a*v for a,v in zip(r[1:],lo)) for i,r in enumerate(rows)}
    w,_=cone_solve(cols,target,512)
    if w is None:return None
    theta=[l+v for l,v in zip(lo,w)]
    if not parameter_ok(rows,theta):raise ArithmeticError('parameter feasibility replay failed')
    return theta

def contradiction(rows):
    # A nonnegative combination of necessary inequalities yields -1>=0.
    columns=[{j:v for j,v in enumerate(r) if v} for r in rows]
    w,_=cone_solve(columns,{0:Q(-1)},512)
    return w

def replay(s,cert):
    try:
        s=normalize(s);m=len(s['parameter_bounds'])
        if not isinstance(cert,dict):return None
        if set(cert)=={'cuts','multipliers'}:
            rows=constraints(s,cert['cuts']);raw=cert['multipliers']
            if not isinstance(raw,list) or len(raw)!=len(rows):return None
            w=list(map(rational,raw))
            if any(v<0 for v in w):return None
            total=[sum(v*r[j] for v,r in zip(w,rows)) for j in range(m+1)]
            return 'refuted' if total==[Q(-1)]+[Q(0)]*m else None
        if set(cert)!={'parameters','proofs'} or not isinstance(cert['parameters'],list) or len(cert['parameters'])!=m:
            return None
        theta=list(map(rational,cert['parameters']))
        if not parameter_ok(constraints(s,[]),theta):return None
        proofs=cert['proofs']
        if not isinstance(proofs,list) or len(proofs)!=len(s['polynomials']):return None
        for i,row in enumerate(proofs):
            if not isinstance(row,dict) or set(row)!={'method','certificate'}:return None
            q=instantiate(s,i,theta)
            verifier={'face':face_replay,'chart':chart_replay}.get(row['method'])
            if verifier is None or verifier(q,row['certificate'])!='proved':return None
        return 'proved'
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,OverflowError):
        return None

def solve(s,budget=8):
    if type(budget) is not int or not 1<=budget<=24:raise ValueError('round budget')
    s=normalize(s);cuts=[];seen=set();tested=0
    for _ in range(budget):
        rows=constraints(s,cuts)
        try:theta=candidate(s,rows)
        except (ValueError,OverflowError):break
        if theta is None:
            try:w=contradiction(rows)
            except (ValueError,OverflowError):break
            if w is not None:
                cert=dict(cuts=cuts,multipliers=[str(v) for v in w])
                if len(json.dumps(cert))<=15000 and replay(s,cert)=='refuted':
                    return dict(status='counterexample',certificate=cert,tested=tested)
            break
        sig=tuple(theta)
        if sig in seen:break
        seen.add(sig);tested+=1;proofs=[];new=[];unknown=False
        for i in range(len(s['polynomials'])):
            try:q=instantiate(s,i,theta)
            except (ValueError,OverflowError):unknown=True;continue
            # The face solver also searches exact feasible points.
            try:r=face_solve(q,budget=48,direction_budget=4,depth=1)
            except (ValueError,OverflowError):r={'status':'unknown'}
            method='face'
            if r['status']=='unknown':
                try:r=chart_solve(q,budget=4,depth=1)
                except (ValueError,OverflowError):r={'status':'unknown'}
                method='chart'
            if r['status']=='counterexample' and face_replay(q,r['certificate'])=='refuted':
                cut=dict(inequality=i,point=r['certificate']['point'])
                if cut not in cuts and cut not in new:new.append(cut)
            elif r['status']=='proved':
                proofs.append(dict(method=method,certificate=r['certificate']))
            else:unknown=True
        if new:
            if len(cuts)+len(new)>48:break
            cuts.extend(new);continue
        if not unknown and len(proofs)==len(s['polynomials']):
            cert=dict(parameters=[str(v) for v in theta],proofs=proofs)
            if len(json.dumps(cert))<=15000 and replay(s,cert)=='proved':
                return dict(status='proved',certificate=cert,tested=tested)
        break
    return dict(status='unknown',tested=tested,cuts=cuts,scope='bounded counterexample-guided rational template synthesis')

def auto_discharge(g,limit=1):
    check(g);count=0
    for i in frontier(g):
        if count>=limit:break
        if i not in frontier(g):continue
        try:s=parse_statement(g['nodes'][i]['statement'])
        except (ValueError,TypeError):continue
        if any(o['focus']==i and oid.startswith('shared-template-') for oid,o in g['observations'].items()):continue
        r=solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True)
        if len(detail)>20000:continue
        oid='shared-template-'+fingerprint(i+'\n'+detail)[:32]
        ops=[dict(op='observe',id=oid,focus=i,kind={'proved':'proof_sketch','counterexample':'counterexample','unknown':'experiment'}[status],detail=detail)]
        if status!='unknown':
            ops.append(dict(op='review_claim',id=i,decision='established' if status=='proved' else 'refuted',evidence='Exact shared-parameter certificate '+oid))
        g=record(g,'falsify' if status=='counterexample' else 'recombine',i,ops,trusted=True);count+=1
    return g
