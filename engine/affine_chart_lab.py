"""Exact affine-coordinate discovery on box-constrained polynomial problems.

Eliminate affine equations, keeping every eliminated coordinate's bounds.
A chart is a parametrization of the entire equality slice, not a sampled
or locally fitted representation. Certificates bind to the original claim.
"""
import json
from itertools import combinations
from fractions import Fraction as Q
from affine import rational
from inequality_invention import add,mul,discover,replay as cone_replay
from box_bernstein import search as box_search,replay as box_replay
from affine_face_lab import parse_statement,data
from discovery import check,frontier,record,fingerprint

def constant(n,v):
    return {(0,)*n:Q(v)} if v else {}

def variable(n,j):
    return {tuple(int(i==j) for i in range(n)):Q(1)}

def scaled(p,w):
    return {e:v*w for e,v in p.items() if v*w}

def checked_mul(a,b):
    if len(a)*len(b)>16384:
        raise OverflowError('chart product budget')
    c=mul(a,b)
    if len(c)>128 or any(sum(e)>12 or v.numerator.bit_length()>256 or v.denominator.bit_length()>256 for e,v in c.items()):
        raise OverflowError('chart expansion budget')
    return c

def substitute(p,images,d):
    out={}
    for e,w in p.items():
        t=constant(d,w)
        for k,img in zip(e,images):
            for _ in range(k):
                t=checked_mul(t,img)
        out=add(out,t)
        if len(out)>128 or any(v.numerator.bit_length()>256 or v.denominator.bit_length()>256 for v in out.values()):
            raise OverflowError('chart expansion budget')
    return out

def chart(A,b,n,order):
    """RREF in the specified column order; free coordinates are original x_j."""
    if sorted(order)!=list(range(n)) or len(order)!=n:
        raise ValueError('column permutation')
    a=[[Q(r[i]) for i in order]+[Q(v)] for r,v in zip(A,b)]
    piv=[]
    for j in range(n):
        k=next((k for k in range(len(piv),len(a)) if a[k][j]),None)
        if k is None:continue
        i=len(piv);a[i],a[k]=a[k],a[i]
        z=a[i][j];a[i]=[v/z for v in a[i]]
        for k in range(len(a)):
            if k!=i:
                z=a[k][j];a[k]=[v-z*w for v,w in zip(a[k],a[i])]
        piv.append(j)
    if any(not any(r[:-1]) and r[-1] for r in a):
        raise ValueError('inconsistent equalities')
    free=[j for j in range(n) if j not in piv];d=len(free)
    if not 1<=d<n:
        raise ValueError('no nontrivial dimension reduction')
    imgs=[None]*n
    for i,j in enumerate(free):
        imgs[order[j]]=variable(d,i)
    for i,j in enumerate(piv):
        q=constant(d,a[i][-1])
        for k,f in enumerate(free):
            q=add(q,scaled(variable(d,k),-a[i][f]))
        imgs[order[j]]=q
    # Check that every original equation holds identically after substitution.
    for r,v in zip(A,b):
        q=constant(d,-v)
        for w,img in zip(r,imgs):
            q=add(q,scaled(img,w))
        if q:raise ArithmeticError('chart identity failure')
    return [order[j] for j in free],imgs

def constraints(images,d):
    """Select all nontrivial original bounds, removing duplicates only."""
    out=[];seen=set()
    for q in images:
        for h in (q,add(constant(d,1),scaled(q,-1))):
            if not h:continue
            sig=tuple(sorted(h.items()))
            if sig not in seen:
                seen.add(sig);out.append(h)
    return out

def atoms(q,assumptions,d):
    out=[];seen=set()
    def push(p):
        key=tuple(sorted(p.items()))
        if p and key not in seen:
            seen.add(key);out.append(p)
    vs=[variable(d,j) for j in range(d)]
    for v in vs:
        push(v);push(add(constant(d,1),scaled(v,-1)))
    for h in assumptions:push(h)
    for x,y in combinations(vs,2):
        push(add(x,y));push(add(x,scaled(y,-1)))
    # Square roots of positive even monomials can reveal non-obvious atoms.
    for e,v in sorted(q.items()):
        if v>0 and all(k%2==0 for k in e):
            push({tuple(k//2 for k in e):Q(1)})
    return out[:24]

def decode_polynomial(raw,d):
    if not isinstance(raw,list) or len(raw)>128:raise ValueError('term count')
    q={}
    for e,w in raw:
        if not isinstance(e,list) or len(e)!=d or any(type(k) is not int or k<0 for k in e) or sum(e)>12:
            raise ValueError('exponents')
        e=tuple(e);q[e]=q.get(e,Q(0))+rational(w)
    return {e:v for e,v in q.items() if v}

def encode_polynomial(q):
    return [[list(e),str(v)] for e,v in sorted(q.items())]

def replay(s,cert):
    try:
        n,A,b,p=data(s)
        if not isinstance(cert,dict) or set(cert)!={'order','proof'} or not isinstance(cert['order'],list) or any(type(i) is not int for i in cert['order']):
            return None
        free,im=chart(A,b,n,cert['order']);d=len(free)
        q=substitute(p,im,d);proof=cert['proof']
        if not isinstance(proof,dict):return None
        if set(proof)=={'kind','tree'} and proof['kind']=='box':
            return 'proved' if box_replay(q,d,proof['tree']) else None
        if set(proof)!={'kind','atoms','weights'} or proof['kind']!='cone':
            return None
        hs=constraints(im,d)
        if len(hs)>12 or not isinstance(proof['atoms'],list) or len(proof['atoms'])>24 or not isinstance(proof['weights'],list) or len(proof['weights'])>256:
            return None
        ps=[decode_polynomial(t,d) for t in proof['atoms']]
        rows=[]
        for ids,j,w in proof['weights']:
            if not isinstance(ids,list):return None
            rows.append((ids,j,rational(w)))
        return 'proved' if cone_replay(q,d,hs,ps,rows) else None
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,OverflowError):
        return None

def solve(s,budget=8,depth=2):
    if type(budget) is not int or not 1<=budget<=16:
        raise ValueError('chart budget')
    n,A,b,p=data(s)
    if not A:return dict(status='unknown',tested=0)
    # Different pivot orders produce different lower-dimensional expressions.
    orders=[list(range(n)),list(reversed(range(n)))]
    for i in range(1,n):orders.append(list(range(i,n))+list(range(i)))
    tested=0;seen=set()
    for order in orders:
        if tested>=budget:break
        try:
            free,im=chart(A,b,n,order);d=len(free)
            sig=tuple(free)
            if sig in seen:continue
            seen.add(sig);tested+=1
            q=substitute(p,im,d);r=box_search(q,d,depth)
            proof=None
            if r['status']=='proved':
                proof=dict(kind='box',tree=r['certificate'])
            else:
                hs=constraints(im,d)
                if len(hs)<=12:
                    ps=atoms(q,hs,d);c=discover(q,d,hs,ps,degree=min(12,max(map(sum,q),default=0)+2))
                    if c is not None:
                        proof=dict(kind='cone',atoms=[encode_polynomial(t) for t in ps],
                                   weights=[[list(ids),j,str(w)] for ids,j,w in c])
            if proof is not None:
                cert=dict(order=order,proof=proof)
                if len(json.dumps(cert))<=15000 and replay(s,cert)=='proved':
                    return dict(status='proved',certificate=cert,tested=tested)
        except (ValueError,OverflowError):continue
    return dict(status='unknown',tested=tested,scope='bounded exact affine chart search')

def auto_discharge(g,limit=1):
    check(g);count=0
    for i in frontier(g):
        if count>=limit:break
        if i not in frontier(g):continue
        try:s=parse_statement(g['nodes'][i]['statement'])
        except (ValueError,TypeError):continue
        if any(o['focus']==i and oid.startswith('affine-chart-') for oid,o in g['observations'].items()):continue
        r=solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True)
        oid='affine-chart-'+fingerprint(i+'\n'+detail)[:32]
        ops=[dict(op='observe',id=oid,focus=i,kind='proof_sketch' if status=='proved' else 'experiment',detail=detail)]
        if status=='proved':
            ops.append(dict(op='review_claim',id=i,decision='established',evidence='Exact affine coordinate certificate '+oid))
        g=record(g,'reformulate',i,ops,trusted=True);count+=1
    return g
