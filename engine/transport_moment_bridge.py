"""Exact transfer of simplex/probability moment bounds to transportation arrays.

Every source theorem stays a proof premise. Row/column normalizations and
polynomial identities are replayed; a relaxation counterexample never transfers.
"""
import json
from fractions import Fraction as Q
import polynomial as p
import transport_face_lab as tr
import moment_chart_lab as mc
import symmetric_level_lab as sl
from rational_cone import solve as cone
from affine import rational

def source(text,size):
    if text.startswith(mc.PREFIX):
        return p.terms(mc.parse_statement(text)['terms'],3,6)
    if text.startswith(sl.PREFIX):
        s=sl.parse_statement(text)
        if s['dimension']!=size:raise ValueError('simplex dimension mismatch')
        return p.terms(s['terms'],3,6)
    raise ValueError('unsupported source')

def add(a,b,w=Q(1)):
    for e,c in b.items():a[e]=a.get(e,Q(0))+w*c
def clean(a):return {e:c for e,c in a.items() if c}
def mul(a,b):
    out={}
    for e,c in a.items():
        for f,d in b.items():
            k=tuple(x+y for x,y in zip(e,f))
            if sum(k)>8:raise ValueError('transfer degree limit')
            out[k]=out.get(k,Q(0))+c*d
            if len(out)>512:raise ValueError('transfer term limit')
    return clean(out)
def instance(s,text,axis,i):
    s=tr.normalize(s);r,c=len(s['rows']),len(s['columns']);n=r*c
    if axis=='row':
        if type(i) is not int or not 0<=i<r:raise ValueError('row index')
        ids=[i*c+j for j in range(c)];mass=Q(s['rows'][i])
    elif axis=='column':
        if type(i) is not int or not 0<=i<c:raise ValueError('column index')
        ids=[j*c+i for j in range(r)];mass=Q(s['columns'][i])
    else:raise ValueError('axis')
    if mass<=0:raise ValueError('zero margin')
    q=source(text,len(ids))
    # For normalized nonnegative y with sum y=1, the size-biased law
    # puts mass y_i at y_i. Its moments are p2,p3,p4.
    images=[{tuple(k if h==j else 0 for h in range(n)):mass**(-k) for j in ids} for k in (2,3,4)]
    out={}
    for e,w in q.items():
        t={(0,)*n:w}
        for k,img in zip(e,images):
            for _ in range(k):t=mul(t,img)
        add(out,t)
        if len(out)>512:raise ValueError('transfer term limit')
    return clean(out)
def replay(goal,premises,cert):
    try:
        s=tr.parse_statement(goal);n=len(s['rows'])*len(s['columns'])
        if not isinstance(cert,dict) or set(cert)!={'instances','monomials'} or not isinstance(cert['instances'],list) or not 1<=len(cert['instances'])<=24 or not isinstance(cert['monomials'],list) or len(cert['monomials'])>64 or len(json.dumps(cert))>15000:return False
        if not isinstance(premises,list) or len(set(premises))!=len(premises) or not premises:return False
        out={};used=set()
        for row in cert['instances']:
            if not isinstance(row,list) or len(row)!=4:return False
            j,axis,i,w=row
            if type(j) is not int or not 0<=j<len(premises):return False
            w=rational(w)
            if w<=0:return False
            used.add(j);add(out,instance(s,premises[j],axis,i),w)
        q=p.terms(cert['monomials'],n,8)
        if any(c<0 for c in q.values()):return False
        add(out,q)
        return used==set(range(len(premises))) and clean(out)==p.terms(s['terms'],n,8)
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,OverflowError,RecursionError):return False
def discover(goal,sources):
    s=tr.parse_statement(goal);n=len(s['rows'])*len(s['columns']);target=p.terms(s['terms'],n,8)
    cols=[];rows=[]
    for text in dict.fromkeys(sources):
        for axis,count in [('row',len(s['rows'])),('column',len(s['columns']))]:
            for i in range(count):
                try:q=instance(s,text,axis,i)
                except (ValueError,TypeError,ArithmeticError):continue
                if q and set(q)&set(target):cols.append(q);rows.append((text,axis,i))
                if len(cols)>=64:break
            if len(cols)>=64:break
        if len(cols)>=64:break
    if not cols:return None
    mono=[e for e,w in target.items() if w>0]
    try:w,_=cone(cols+[{e:Q(1)} for e in mono],target,pivot_budget=160)
    except ValueError:return None
    if w is None:return None
    ps=[];inst=[]
    for (text,axis,i),v in zip(rows,w):
        if not v:continue
        if text not in ps:ps.append(text)
        inst.append([ps.index(text),axis,i,str(v)])
    if not ps:return None
    c=dict(instances=inst,monomials=p.encode({e:v for e,v in zip(mono,w[len(cols):]) if v}))
    return dict(premises=ps,certificate=c) if replay(goal,ps,c) else None

def auto_discharge(g,limit=1):
    from discovery import check,frontier,record,fingerprint
    from proof_audit import audit
    check(g);targets=[]
    for i in frontier(g):
        try:tr.parse_statement(g['nodes'][i]['statement']);targets.append(i)
        except (ValueError,TypeError):continue
    if not targets:return g
    report=audit(g)
    if report['conflicts']:return g
    source_ids={}
    for i in sorted(report['proved']):
        text=g['nodes'][i]['statement']
        if text.startswith((mc.PREFIX,sl.PREFIX)):source_ids.setdefault(text,i)
    count=0
    for focus in targets:
        if count>=limit:break
        if focus not in frontier(g):continue
        hit=discover(g['nodes'][focus]['statement'],list(source_ids))
        if not hit:continue
        ps=[source_ids[t] for t in hit['premises']]
        tag='transport-moment-'+fingerprint(focus+'\n'+'\n'.join(ps))[:32]
        if tag in g['observations'] or any(e['parent']==focus and set(e['premises'])==set(ps) and e['rule']!='rejected' for e in g['edges'].values()):continue
        ops=[dict(op='derive',id=tag,parent=focus,premises=ps,argument='Normalize positive-margin rows/columns to simplices, then sum nonnegative moment theorem instances and monomials with exact coefficient identity.'),dict(op='observe',id=tag,focus=focus,kind='transfer',detail=json.dumps(dict(edge=tag,certificate=hit['certificate']),sort_keys=True)),dict(op='review_edge',id=tag,decision='accepted',evidence='Exact normalized-moment identity '+tag)]
        try:g=record(g,'recombine',focus,ops,trusted=True)
        except ValueError:continue
        count+=1
    return g
