"""Stationary-face polynomial certificates for transportation polytopes.

At a minimum with exactly this positive support, tangent gradients vanish
and directional Hessians are nonnegative. Cover every support recursively.
"""
from fractions import Fraction as Q
import json
import transport_face_lab as tr
import box_bernstein as box
import polynomial as p
from affine import rational
from affine_face_lab import face_data,reduced,value
from affine_extremal_invention import nullspace
from inequality_invention import derivative,add,mul
from rational_cone import solve as cone
MAX_FACES=192
parse_statement=tr.parse_statement
def data(s):return tr.data(s)
def generators(R,t,q,n):
    zero=(0,)*n;one={zero:Q(1)};basis=nullspace(R,n)
    eq=[]
    for r,b in zip(R,t):
        h={zero:-b}
        for j,v in enumerate(r):
            if v:h[tuple(int(i==j) for i in range(n))]=v
        h={e:v for e,v in h.items() if v}
        if h and h not in eq:eq.append(h)
    for d in basis:
        h=derivative(q,d)
        if h and h not in eq:eq.append(h)
    hs=[]
    for d in basis:
        h=derivative(derivative(q,d),d)
        if h and h not in hs:hs.append(h)
    return eq,hs
def polynomial(q,n):
    return p.terms(q,n,8)
def reconstruct(q,R,t,n,cert):
    if not isinstance(cert,dict) or set(cert)!={'eq','hessian','tree'}:raise ValueError('stationary certificate')
    eq,hs=generators(R,t,q,n);rem=q
    for name,pool in [('eq',eq),('hessian',hs)]:
        rows=cert[name]
        if not isinstance(rows,list) or len(rows)>64:raise ValueError('multipliers')
        for row in rows:
            if not isinstance(row,list) or len(row)!=2:raise ValueError('multiplier')
            i,raw=row
            if type(i) is not int or not 0<=i<len(pool):raise ValueError('index')
            w=polynomial(raw,n)
            if name=='hessian' and any(v<0 for v in w.values()):raise ValueError('negative multiplier on box')
            rem=add(rem,mul(w,pool[i]),-1)
            if len(rem)>128 or any(sum(e)>12 for e in rem):raise ValueError('residual size')
    return box.replay(rem,n,cert['tree'])
def find(q,R,t,n):
    eq,hs=generators(R,t,q,n);zero=(0,)*n
    exps=[zero]+[tuple(int(i==j) for i in range(n)) for j in range(n)]
    # Include equality multipliers of degree one and nonnegative Hessian
    # multipliers. Residual candidates are box-positive monomials,
    # x_i(1-x_i), and 1-x_i.
    cols=[];meta=[]
    def push(v,m):
        if v and len(cols)<256:cols.append(v);meta.append(m)
    for name,pool in [('eq',eq),('hessian',hs)]:
        for i,h in enumerate(pool):
            for e in exps:
                for sign in ((1,-1) if name=='eq' else (1,)):
                    w={e:Q(sign)};v=mul(w,h)
                    if len(v)<=128 and all(sum(k)<=8 for k in v):push(v,(name,i,w))
    for e in sorted(set(q)|set(exps)):
        push({e:Q(1)},None)
    for e in exps[1:]:
        push({zero:Q(1),e:Q(-1)},None)
        push({e:Q(1),tuple(2*v for v in e):Q(-1)},None)
    try:w,_=cone(cols,q,pivot_budget=160)
    except ValueError:return None
    if w is None:return None
    c=dict(eq=[],hessian=[],tree=None)
    rem=q
    for v,m in zip(w,meta):
        if not v or m is None:continue
        name,i,f=m;f={e:v*a for e,a in f.items()}
        c[name].append([i,p.encode(f)])
        rem=add(rem,mul(f,(eq if name=='eq' else hs)[i]),-1)
    try:
        r=box.search(rem,n,depth=1)
        if r['status']!='proved':return None
        c['tree']=r['certificate']
        return c if reconstruct(q,R,t,n,c) else None
    except (ValueError,OverflowError):return None
def faces(face):return [face[:i]+'0'+face[i+1:] for i,v in enumerate(face) if v=='*']
def replay(s,cert):
    try:
        r,c,A,b,q0=data(s);n=r*c
        if not isinstance(cert,dict) or len(json.dumps(cert))>18000:return None
        if set(cert)=={'point'}:return tr.replay(s,cert)
        if set(cert)!={'stationary-faces'} or not isinstance(cert['stationary-faces'],dict) or len(cert['stationary-faces'])>MAX_FACES:return None
        nodes=cert['stationary-faces'];todo=['*'*n];seen=set()
        while todo:
            face=todo.pop()
            if face in seen:continue
            seen.add(face);node=nodes[face];free,R,t,q=face_data(A,b,q0,face);dim=len(free);kind,x=reduced(R,t,dim)
            if node=={'kind':'empty'}:
                if kind!='empty':return None
            elif node=={'kind':'point'}:
                if kind!='point' or value(q,x)<0:return None
            elif isinstance(node,dict) and set(node)=={'kind','tree'} and node['kind']=='box':
                if not dim or not box.replay(q,dim,node['tree']):return None
            elif isinstance(node,dict) and set(node)=={'kind','certificate'} and node['kind']=='stationary':
                if not dim or not reconstruct(q,R,t,dim,node['certificate']):return None
                # If only margin equations were used, the identity holds
                # on the whole face, including its boundary.
                eq,_=generators(R,t,q,dim)
                # Conservative: cover every proper support regardless.
                todo.extend(faces(face))
            else:return None
        return 'proved' if seen==set(nodes) else None
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,OverflowError,RecursionError):return None
def solve(s):
    r,c,A,b,q0=data(s);n=r*c;nodes={};todo=['*'*n]
    try:
        while todo:
            face=todo.pop()
            if face in nodes:continue
            if len(nodes)>=MAX_FACES:break
            free,R,t,q=face_data(A,b,q0,face);dim=len(free);kind,x=reduced(R,t,dim)
            if kind=='empty':nodes[face]=dict(kind='empty');continue
            if kind=='point':
                if value(q,x)<0:
                    cert=dict(point=list(map(str,tr.lift(face,x))))
                    if tr.replay(s,cert)=='refuted':return dict(status='counterexample',certificate=cert)
                    raise ArithmeticError('point replay')
                nodes[face]=dict(kind='point');continue
            ans=box.search(q,dim,depth=0)
            if ans['status']=='proved':nodes[face]=dict(kind='box',tree=ans['certificate']);continue
            cert=find(q,R,t,dim)
            if cert is None:break
            nodes[face]=dict(kind='stationary',certificate=cert);todo.extend(faces(face))
        else:
            c=dict(**{'stationary-faces':nodes})
            if replay(s,c)=='proved':return dict(status='proved',certificate=c)
    except (ValueError,OverflowError):pass
    return dict(status='unknown',scope='bounded stationary support search')
def auto_discharge(g,limit=1):
    from deep_invention_dispatch import discharge
    return discharge(g,parse_statement,solve,replay,'stationary-transport-',limit)
