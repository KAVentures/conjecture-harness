"""Exact recursive boundary reductions for polynomial inequalities on affine boxes.

A certificate is a tree of feasible-direction concavity reductions or direct
Bernstein/unique-point/inconsistent-system leaves. Every possible boundary
face reached by the chosen direction must be covered. No numerical status
or unproved extremizer classification is accepted.
"""
import json
from fractions import Fraction as Q
from affine import rational
from runtime import strict_json
from box_bernstein import search as box_search,replay as box_replay
from affine_extremal_invention import nullspace,curvature
from discovery import check,frontier,record,fingerprint

PREFIX='Affine box polynomial inequality: '

def normalize(s):
    if not isinstance(s,dict) or set(s)!={'dimension','rows','rhs','terms'}:
        raise ValueError('claim shape')
    n=s['dimension'];rows=s['rows'];rhs=s['rhs'];terms=s['terms']
    if type(n) is not int or not 1<=n<=16 or not isinstance(rows,list) or len(rows)>32 or not isinstance(rhs,list) or len(rhs)!=len(rows):
        raise ValueError('system size')
    if any(not isinstance(r,list) or len(r)!=n for r in rows):
        raise ValueError('row size')
    if not isinstance(terms,list) or len(terms)>128:
        raise ValueError('term count')
    p={}
    for e,w in terms:
        if not isinstance(e,list) or len(e)!=n or any(type(i) is not int or i<0 for i in e) or sum(e)>12:
            raise ValueError('exponents')
        e=tuple(e);p[e]=p.get(e,Q(0))+rational(w)
    return dict(dimension=n,rows=[[str(rational(w)) for w in r] for r in rows],
                rhs=[str(rational(w)) for w in rhs],
                terms=[[list(e),str(w)] for e,w in sorted(p.items()) if w])

def statement(s):
    return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))

def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):
        raise ValueError('wrong statement type')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:
        raise ValueError('noncanonical statement')
    return s

def data(s):
    s=normalize(s)
    return (s['dimension'],[list(map(Q,r)) for r in s['rows']],
            list(map(Q,s['rhs'])),{tuple(e):Q(w) for e,w in s['terms']})

def face_data(rows,rhs,p,face):
    free=[i for i,v in enumerate(face) if v=='*']
    ones=[i for i,v in enumerate(face) if v=='1']
    zeros=[i for i,v in enumerate(face) if v=='0']
    A=[[r[i] for i in free] for r in rows]
    b=[v-sum(r[i] for i in ones) for r,v in zip(rows,rhs)]
    out={}
    for e,w in p.items():
        if any(e[i] for i in zeros):
            continue
        f=tuple(e[i] for i in free);out[f]=out.get(f,Q(0))+w
    return free,A,b,{e:v for e,v in out.items() if v}

def reduced(A,b,n):
    """Exact RREF of augmented system, including vacuous and zero-dimensional cases."""
    a=[r[:]+[v] for r,v in zip(A,b)]
    piv=[]
    for j in range(n):
        k=next((k for k in range(len(piv),len(a)) if a[k][j]),None)
        if k is None:
            continue
        i=len(piv);a[i],a[k]=a[k],a[i]
        z=a[i][j];a[i]=[v/z for v in a[i]]
        for k,r in enumerate(a):
            if k!=i:
                z=r[j];a[k]=[v-z*w for v,w in zip(r,a[i])]
        piv.append(j)
    if any(not any(r[:-1]) and r[-1] for r in a):
        return 'empty',None
    # Interval bounds are necessary for any point in the box.
    for r in a:
        if r[-1]<sum(min(0,v) for v in r[:-1]) or r[-1]>sum(max(0,v) for v in r[:-1]):
            return 'empty',None
    if len(piv)==n:
        x=[a[i][-1] for i in range(n)]
        return ('point',x) if all(0<=v<=1 for v in x) else ('empty',None)
    return 'positive-dimensional',None

def value(p,x):
    from math import prod
    return sum((w*prod(v**k for v,k in zip(x,e)) for e,w in p.items()),Q(0))

def children(face,free,d):
    out=[]
    for i,w in zip(free,d):
        if w:
            out.extend(face[:i]+v+face[i+1:] for v in '01')
    return sorted(out)

def probe(A,b,p,n,budget=128):
    """Enumerate selected exact feasible vertices/points of the affine slice."""
    from itertools import combinations,product
    d=len(nullspace(A,n))
    # Fix enough coordinates to remove the nullspace. Not every choice is
    # independent; reduced() checks each resulting system exactly.
    count=0
    for ids in combinations(range(n),d):
        for vals in product((Q(0),Q(1),Q(1,2)),repeat=d):
            if count>=budget:
                return None
            count+=1
            rows=A+[[Q(i==j) for i in range(n)] for j in ids]
            kind,x=reduced(rows,b+list(vals),n)
            if kind=='point' and value(p,x)<0:
                return x
    return None

def replay(s,cert):
    try:
        n,A,b,p=data(s)
        if isinstance(cert,dict) and set(cert)=={'point'}:
            x=list(map(rational,cert['point']))
            if len(x)!=n or any(not 0<=v<=1 for v in x) or any(sum(u*v for u,v in zip(r,x))!=w for r,w in zip(A,b)):
                return None
            return 'refuted' if value(p,x)<0 else None
        if not isinstance(cert,dict) or set(cert)!={'faces'} or not isinstance(cert['faces'],dict) or len(cert['faces'])>256:
            return None
        nodes=cert['faces'];seen=set();pending=['*'*n]
        while pending:
            face=pending.pop()
            if face in seen:
                continue
            seen.add(face)
            node=nodes[face]
            if not isinstance(node,dict):
                return None
            free,R,t,q=face_data(A,b,p,face)
            dim=len(free);kind,x=reduced(R,t,dim)
            mode=node.get('kind')
            if mode=='empty':
                if set(node)!={'kind'} or kind!='empty':
                    return None
            elif mode=='point':
                if set(node)!={'kind'} or kind!='point' or value(q,x)<0:
                    return None
            elif mode=='box':
                if set(node)!={'kind','tree'} or not dim or not box_replay(q,dim,node['tree']):
                    return None
            elif mode=='split':
                if set(node)!={'kind','direction','curvature'} or kind!='positive-dimensional':
                    return None
                d=list(map(rational,node['direction']))
                if len(d)!=dim or not any(d) or any(sum(v*w for v,w in zip(r,d)) for r in R):
                    return None
                if not box_replay(curvature(q,d),dim,node['curvature']):
                    return None
                pending.extend(children(face,free,d))
            else:
                return None
        return 'proved' if seen==set(nodes) else None
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,OverflowError):
        return None

def solve(s,budget=128,direction_budget=8,depth=1):
    if type(budget) is not int or not 1<=budget<=256 or type(direction_budget) is not int or not 1<=direction_budget<=32:
        raise ValueError('search bounds')
    n,A,b,p=data(s);memo={};visits=0
    x=probe(A,b,p,n,budget=min(128,budget))
    if x is not None:
        cert={'point':[str(v) for v in x]}
        if replay(s,cert)=='refuted':
            return dict(status='counterexample',certificate=cert,visited=0)
    def visit(face):
        nonlocal visits
        if face in memo:
            return memo[face]
        if visits>=budget:
            return None
        visits+=1
        free,R,t,q=face_data(A,b,p,face)
        dim=len(free);kind,x=reduced(R,t,dim)
        if kind=='empty':
            memo[face]={'kind':'empty'}
        elif kind=='point':
            memo[face]={'kind':'point'} if value(q,x)>=0 else None
        else:
            r=box_search(q,dim,depth)
            if r['status']=='proved':
                memo[face]={'kind':'box','tree':r['certificate']}
            else:
                memo[face]=None
                basis=nullspace(R,dim)
                from itertools import combinations
                ds=basis+[[a+sign*b for a,b in zip(u,v)] for u,v in combinations(basis,2) for sign in (1,-1)]
                ds=sorted(ds,key=lambda d:(sum(v!=0 for v in d),d))
                for d in ds[:direction_budget]:
                    r=box_search(curvature(q,d),dim,depth)
                    if r['status']!='proved':
                        continue
                    if all(visit(f) is not None for f in children(face,free,d)):
                        memo[face]={'kind':'split','direction':[str(w) for w in d],'curvature':r['certificate']}
                        break
        return memo[face]
    root='*'*n
    if visit(root) is not None:
        # Keep only descendants of the selected successful proof.
        nodes={};pending=[root]
        while pending:
            f=pending.pop()
            if f in nodes:
                continue
            node=memo[f];nodes[f]=node
            if node['kind']=='split':
                pending.extend(children(f,[i for i,v in enumerate(f) if v=='*'],list(map(Q,node['direction']))))
        cert={'faces':nodes}
        if len(json.dumps(cert))<=15000 and replay(s,cert)=='proved':
            return dict(status='proved',certificate=cert,visited=visits)
    return dict(status='unknown',visited=visits,scope='bounded recursive face reductions')

def auto_discharge(g,limit=1):
    check(g);count=0
    for i in frontier(g):
        if count>=limit:
            break
        if i not in frontier(g):
            continue
        try:s=parse_statement(g['nodes'][i]['statement'])
        except (ValueError,TypeError):continue
        if any(o['focus']==i and oid.startswith('affine-face-') for oid,o in g['observations'].items()):
            continue
        r=solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True)
        oid='affine-face-'+fingerprint(i+'\n'+detail)[:32]
        ops=[dict(op='observe',id=oid,focus=i,kind={'proved':'proof_sketch','counterexample':'counterexample','unknown':'experiment'}[status],detail=detail)]
        if status=='proved':
            ops.append(dict(op='review_claim',id=i,decision='established',evidence='Exact recursive face certificate '+oid))
        elif status=='counterexample':
            ops.append(dict(op='review_claim',id=i,decision='refuted',evidence='Exact feasible negative point '+oid))
        g=record(g,'falsify' if status=='counterexample' else 'forward',i,ops,trusted=True);count+=1
    return g
