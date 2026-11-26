"""Graph-dispatched simultaneous square-product search for conditional claims."""
import itertools,json
from fractions import Fraction as Q
import polynomial as p
import conditional_theorems as ct
from inequality_invention import discover,replay as replay_cone
from discovery import check,frontier,record,fingerprint

def inputs(s):
    s=ct.normalize(s); n=len(s['variables']);a=[]
    for h in s['assumptions']:
        q=p.terms(h['terms'],n);a.append(q)
        if h['relation']=='zero':
            a.append({e:-v for e,v in q.items()})
    if s['domain']=='nonnegative':
        a.extend({tuple(int(i==j) for i in range(n)):Q(1)} for j in range(n))
    if len(a)>12:
        raise ValueError('too many expanded hypotheses')
    return n,a,p.terms(s['conclusion'],n)

def atoms(n,target):
    # Generate squared monomials, signed differences and sums, prioritizing
    # low degree and support that occurs in the target.
    zero=(0,)*n
    es=[zero]+[e for e in itertools.product(range(3),repeat=n) if 1<=sum(e)<=2]
    es.sort(key=lambda e:(sum(e),e))
    out=[{e:Q(1)} for e in es]
    pairs=[]
    for i,e in enumerate(es):
        for f in es[i+1:]:
            g=tuple(x+y for x,y in zip(e,f))
            if g in target:
                c=1 if target[g]>0 else -1
                pairs.append({e:Q(1),f:Q(c)})
    # Reserve room for cancellation-aware binomial squares.
    return (out[:12]+pairs[:12]+out[12:])[:24]

def replay(s,cert):
    try:
        n,a,t=inputs(s)
        if not isinstance(cert,dict) or set(cert)!={'kind','atoms','weights'} or cert['kind']!='square-cone':
            return None
        if not isinstance(cert['atoms'],list) or len(cert['atoms'])>24 or not isinstance(cert['weights'],list) or len(cert['weights'])>256:
            return None
        q=[p.terms(x,n) for x in cert['atoms']]
        rows=[]
        for row in cert['weights']:
            if not isinstance(row,list) or len(row)!=3 or not isinstance(row[0],list):
                return None
            ids,j,w=row
            rows.append((ids,j,p.rational(w)))
        return 'proved' if replay_cone(t,n,a,q,rows) else None
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError):
        return None

def solve(s):
    try:
        n,a,t=inputs(s);q=atoms(n,t)
        c=discover(t,n,a,q,degree=min(12,max(map(sum,t),default=0)+2))
        if c is not None:
            cert=dict(kind='square-cone',atoms=[p.encode(x) for x in q],
                      weights=[[list(ids),j,str(w)] for ids,j,w in c])
            if len(json.dumps(cert))<=15000 and replay(s,cert)=='proved':
                return dict(status='proved',certificate=cert)
    except (ValueError,OverflowError):
        pass
    return dict(status='unknown',scope='bounded square-product cone; no completeness claim')

def auto_discharge(g,limit=1):
    check(g);count=0
    for i in frontier(g):
        if count>=limit:break
        if i not in frontier(g):continue
        try:s=ct.parse_statement(g['nodes'][i]['statement']);inputs(s)
        except (ValueError,TypeError):continue
        if any(o['focus']==i and oid.startswith('square-cone-') for oid,o in g['observations'].items()):continue
        r=solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True)
        oid='square-cone-'+fingerprint(i+'\n'+detail)[:32]
        ops=[dict(op='observe',id=oid,focus=i,kind='proof_sketch' if status=='proved' else 'experiment',detail=detail)]
        if status=='proved':
            ops.append(dict(op='review_claim',id=i,decision='established',evidence='Exact square-product cone '+oid))
        g=record(g,'forward',i,ops,trusted=True);count+=1
    return g
