"""Certified support-face extremizer reductions on transportation polytopes."""
from fractions import Fraction as Q
from collections import deque
import json
from affine import rational
import polynomial as p
from runtime import strict_json
from affine_face_lab import face_data,reduced,value
from affine_extremal_invention import curvature,transportation_equalities
import box_bernstein as box
PREFIX='Transportation polynomial inequality: '
MAX_FACES=192

def normalize(s):
    if not isinstance(s,dict) or set(s)!={'rows','columns','terms'}:raise ValueError('claim')
    r=s['rows'];c=s['columns']
    if not isinstance(r,list) or not isinstance(c,list) or not 1<=len(r)<=6 or not 1<=len(c)<=6 or len(r)*len(c)>25:raise ValueError('shape')
    r=list(map(rational,r));c=list(map(rational,c))
    if any(not 0<=v<=1 for v in r+c) or sum(r)!=sum(c):raise ValueError('margins')
    return dict(rows=list(map(str,r)),columns=list(map(str,c)),terms=p.encode(p.terms(s['terms'],len(r)*len(c),8)))
def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))
def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('not transport')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical transport')
    return s
def data(s):
    s=normalize(s);r,c=len(s['rows']),len(s['columns'])
    return r,c,[[Q(v) for v in row] for row in transportation_equalities(r,c)],list(map(Q,s['rows']+s['columns'])),p.terms(s['terms'],r*c,8)
def directions(r,c,free):
    # For every support edge, find a shortest alternate path. Together
    # these expose simple cycles, including chordless cycles longer than 4.
    adj=[[] for _ in range(r+c)]
    for e in free:
        u,v=e//c,r+e%c;adj[u].append((v,e));adj[v].append((u,e))
    seen=set()
    for e in free:
        u,v=e//c,r+e%c;prev={u:None};todo=deque([u])
        while todo and v not in prev:
            a=todo.popleft()
            for b,k in adj[a]:
                if k!=e and b not in prev:prev[b]=(a,k);todo.append(b)
        if v not in prev:continue
        path=[];x=v
        while x!=u:x,k=prev[x];path.append(k)
        cyc=[e]+path;d={k:(1 if i%2==0 else -1) for i,k in enumerate(cyc)}
        sig=tuple(sorted(d))
        if sig in seen:continue
        seen.add(sig);yield [Q(d.get(k,0)) for k in free]
def children(face,free,d):return [face[:i]+'0'+face[i+1:] for i,v in zip(free,d) if v]
def lift(face,x):
    it=iter(x);return [next(it) if v=='*' else Q(0) for v in face]
def replay(s,cert):
    try:
        r,c,A,b,p0=data(s);n=r*c
        if not isinstance(cert,dict) or len(json.dumps(cert))>18000:return None
        if set(cert)=={'point'}:
            if not isinstance(cert['point'],list) or len(cert['point'])!=n:return None
            x=list(map(rational,cert['point']))
            return 'refuted' if all(0<=v<=1 for v in x) and all(sum(v*w for v,w in zip(row,x))==t for row,t in zip(A,b)) and value(p0,x)<0 else None
        if set(cert)!={'faces'} or not isinstance(cert['faces'],dict) or len(cert['faces'])>MAX_FACES:return None
        nodes=cert['faces'];todo=['*'*n];seen=set()
        while todo:
            face=todo.pop()
            if face in seen:continue
            seen.add(face);node=nodes[face];free,R,t,q=face_data(A,b,p0,face);dim=len(free);kind,x=reduced(R,t,dim)
            if not isinstance(node,dict):return None
            mode=node.get('kind')
            if mode=='empty':
                if set(node)!={'kind'} or kind!='empty':return None
            elif mode=='point':
                if set(node)!={'kind'} or kind!='point' or value(q,x)<0:return None
            elif mode=='box':
                if set(node)!={'kind','tree'} or not dim or not box.replay(q,dim,node['tree']):return None
            elif mode=='cycle':
                if set(node)!={'kind','direction','tree'} or not isinstance(node['direction'],list) or len(node['direction'])!=dim:return None
                d=list(map(rational,node['direction']))
                if not any(d) or any(v not in (-1,0,1) for v in d) or any(sum(v*w for v,w in zip(row,d)) for row in R):return None
                if not box.replay(curvature(q,d),dim,node['tree']):return None
                todo.extend(children(face,free,d))
            else:return None
        return 'proved' if seen==set(nodes) else None
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,OverflowError,RecursionError):return None
def solve(s):
    r,c,A,b,p0=data(s);n=r*c;nodes={};witness=None;budget=384
    def visit(face):
        nonlocal witness,budget
        if face in nodes:return True
        if len(nodes)>=MAX_FACES or budget<=0:return False
        budget-=1;free,R,t,q=face_data(A,b,p0,face);dim=len(free);kind,x=reduced(R,t,dim)
        if kind=='empty':nodes[face]=dict(kind='empty');return True
        if kind=='point':
            if value(q,x)<0:witness=dict(point=list(map(str,lift(face,x))));return False
            nodes[face]=dict(kind='point');return True
        res=box.search(q,dim,depth=0)
        if res['status']=='proved':nodes[face]=dict(kind='box',tree=res['certificate']);return True
        for d in directions(r,c,free):
            if budget<=0:return False
            budget-=1;cur=box.search(curvature(q,d),dim,depth=1)
            if cur['status']!='proved':continue
            before=set(nodes)
            nodes[face]=dict(kind='cycle',direction=list(map(str,d)),tree=cur['certificate'])
            if all(visit(f) for f in children(face,free,d)):return True
            if witness is not None:return False
            for f in set(nodes)-before:del nodes[f]
        return False
    try:
        if visit('*'*n):
            cert=dict(faces=nodes)
            if replay(s,cert)=='proved':return dict(status='proved',certificate=cert)
        if witness is not None and replay(s,witness)=='refuted':return dict(status='counterexample',certificate=witness)
    except (ValueError,OverflowError):pass
    return dict(status='unknown',scope='bounded support-face search')
def auto_discharge(g,limit=1):
    from deep_invention_dispatch import discharge
    return discharge(g,parse_statement,solve,replay,'transport-face-',limit)
