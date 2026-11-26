"""Bounded exact positive rational synthesis of nonnegative polynomial lemmas."""
import itertools,json
from fractions import Fraction as F
import polynomial as p
from hypothesis import compatible,coefficients,add
from discovery import check,closure,frontier,record,fingerprint
def replay(goal,premises,cert):
    try:
        goal=p.normalize(goal)
        if not isinstance(premises,list) or not 1<=len(premises)<=4 or not isinstance(cert,dict) or set(cert)!={'weights'} or not isinstance(cert['weights'],list) or len(cert['weights'])!=len(premises):return False
        total={}
        for s,w in zip(premises,cert['weights']):
            s=p.normalize(s);w=p.rational(w)
            if w<=0 or not compatible(goal,s):return False
            total=add(total,coefficients(s),w)
        return total==coefficients(goal)
    except (ValueError,TypeError,KeyError,ArithmeticError):return False
def weights(goal,premises):
    a=coefficients(goal);bs=[coefficients(s) for s in premises];k=len(bs)
    es=sorted(set(a).union(*(set(b) for b in bs)))
    rows=[[b.get(e,F(0)) for b in bs]+[a.get(e,F(0))] for e in es]
    rank=0
    for j in range(k):
        at=next((i for i in range(rank,len(rows)) if rows[i][j]),None)
        if at is None:return None
        rows[rank],rows[at]=rows[at],rows[rank];v=rows[rank][j];rows[rank]=[x/v for x in rows[rank]]
        for i in range(len(rows)):
            if i==rank:continue
            v=rows[i][j]
            if v:rows[i]=[x-v*y for x,y in zip(rows[i],rows[rank])]
        if any(x.numerator.bit_length()>256 or x.denominator.bit_length()>256 for row in rows for x in row):return None
        rank+=1
    if any(not any(r[:-1]) and r[-1] for r in rows):return None
    w=[rows[i][-1] for i in range(k)]
    if any(x<=0 for x in w):return None
    cert=dict(weights=list(map(str,w)))
    return cert if replay(goal,premises,cert) else None
def synthesize(goal,pool,budget=256):
    goal=p.normalize(goal)
    if type(budget) is not int or not 1<=budget<=1024 or not isinstance(pool,dict) or len(pool)>24:raise ValueError('synthesis limits')
    valid=[]
    for i,s in sorted(pool.items()):
        s=p.normalize(s)
        if compatible(goal,s) and coefficients(s) and coefficients(s)!=coefficients(goal):valid.append((i,s))
    tested=0
    for size in range(1,min(4,len(valid))+1):
        for subset in itertools.combinations(valid,size):
            if tested>=budget:return None
            tested+=1;ids,ss=zip(*subset);cert=weights(goal,list(ss))
            if cert:return dict(premises=list(ids),certificate=cert,tested=tested)
    return None
def auto_discharge(g,limit=2):
    check(g);count=0
    for focus in frontier(g):
        if count>=limit:break
        if focus not in frontier(g):continue
        try:goal=p.parse_statement(g['nodes'][focus]['statement'])
        except (ValueError,TypeError):continue
        if goal['relation']!='nonnegative':continue
        pool={}
        for i in sorted(closure(g)):
            try:s=p.parse_statement(g['nodes'][i]['statement'])
            except (ValueError,TypeError):continue
            if compatible(goal,s):pool[i]=s
            if len(pool)>=24:break
        r=synthesize(goal,pool)
        if r is None:continue
        ids=r['premises'];tag='synthesis-'+fingerprint(focus+'\n'+'\n'.join(ids))[:32]
        old=next((i for i,e in sorted(g['edges'].items()) if e['parent']==focus and set(e['premises'])==set(ids) and e['rule']!='rejected'),None)
        if old is not None and g['edges'][old]['rule']=='accepted':continue
        eid=old or tag
        if old is not None:
            order=g['edges'][old]['premises'];w=dict(zip(ids,r['certificate']['weights']));ids=order;r=dict(r,premises=ids,certificate=dict(weights=[w[i] for i in ids]))
        if not replay(goal,[pool[i] for i in ids],r['certificate']):raise ArithmeticError('synthesis replay failed')
        ops=[] if old else [dict(op='derive',id=eid,parent=focus,premises=ids,argument='Exact positive rational combination of polynomial lemmas on the same quantified domain.')]
        detail=json.dumps(dict(edge=eid,**r),sort_keys=True)
        if tag in g['observations']:continue
        ops.extend([dict(op='observe',id=tag,focus=focus,kind='proof_sketch',detail=detail),dict(op='review_edge',id=eid,decision='accepted',evidence='Exact conic identity '+tag)])
        try:g=record(g,'recombine',focus,ops,trusted=True)
        except ValueError:continue
        count+=1
    return g
