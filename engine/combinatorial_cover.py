"""Bounded exact finite cover/edge-partition discovery with replayable certificates.

All quantities are integers. No claim about arbitrary graph order follows.
"""
import json
from runtime import strict_json

PREFIX = "Finite combinatorial cover: "
MAX_ITEMS = 32
MAX_ROWS = 4096
MAX_STATES = 512
MAX_PATH_STEPS = 30000

def integer(x, lo, hi):
    return type(x) is int and lo <= x <= hi

def vector(v, length):
    if not isinstance(v, list) or len(v) != length or not all(integer(x, 0, MAX_ITEMS) for x in v):
        raise ValueError("invalid resource vector")
    return list(v)

def normalize(s):
    if not isinstance(s, dict) or s.get("kind") not in ("cover", "paths"):
        raise ValueError("unknown cover kind")
    k = s.get("max_pieces")
    if not integer(k, 0, MAX_ITEMS):
        raise ValueError("piece bound")
    if s["kind"] == "cover":
        if set(s) != {"kind", "items", "rows", "resources", "max_pieces"}:
            raise ValueError("cover shape")
        n = s["items"]
        r = s["resources"]
        if not integer(n, 0, MAX_ITEMS) or not isinstance(r, list) or len(r) > 12:
            raise ValueError("cover dimensions")
        r = vector(r, len(r))
        if not isinstance(s["rows"], list) or len(s["rows"]) > MAX_ROWS:
            raise ValueError("row limit")
        rows = set()
        for row in s["rows"]:
            if not isinstance(row, list) or len(row) != 2:
                raise ValueError("row shape")
            items, use = row
            if not isinstance(items, list) or not items or not all(integer(i,0,n-1) for i in items) or len(set(items)) != len(items):
                raise ValueError("invalid row items")
            rows.add((tuple(sorted(items)), tuple(vector(use,len(r)))))
        return dict(kind="cover",items=n,rows=[[list(a),list(b)] for a,b in sorted(rows)],resources=r,max_pieces=k)
    if set(s) != {"kind","n","edges","endpoints","max_pieces"}:
        raise ValueError("path shape")
    n=s["n"]
    if not integer(n,1,12) or not isinstance(s["edges"],list) or len(s["edges"])>MAX_ITEMS:
        raise ValueError("graph dimensions")
    es=set()
    for e in s["edges"]:
        if not isinstance(e,list) or len(e)!=2 or not all(integer(v,0,n-1) for v in e) or e[0]==e[1]:
            raise ValueError("edge")
        edge=tuple(sorted(e))
        if edge in es:
            raise ValueError("duplicate edge")
        es.add(edge)
    b=s["endpoints"]
    if b is not None:
        b=vector(b,n)
    return dict(kind="paths",n=n,edges=[list(e) for e in sorted(es)],endpoints=b,max_pieces=k)

def statement(s):
    return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(",",":"))

def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):
        raise ValueError("not a cover statement")
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:
        raise ValueError("noncanonical cover statement")
    return s

def compile_rows(s):
    """Complete row enumeration, or raise OverflowError. No partial refutations."""
    if s["kind"]=="cover":
        return s["items"],tuple(s["resources"]),[(sum(1<<i for i in a),tuple(b)) for a,b in s["rows"]]
    n=s["n"];es=s["edges"];b=s["endpoints"]
    adj=[[] for _ in range(n)]
    for i,(u,v) in enumerate(es):
        adj[u].append((v,i));adj[v].append((u,i))
    rows=set();steps=0
    def visit(start,v,seen,mask):
        nonlocal steps
        steps+=1
        if steps>MAX_PATH_STEPS:
            raise OverflowError("path enumeration budget")
        if mask and start<v:
            use=tuple(int(i==start or i==v) for i in range(n)) if b is not None else ()
            rows.add((mask,use))
            if len(rows)>MAX_ROWS:
                raise OverflowError("path row budget")
        for w,i in adj[v]:
            if not (seen>>w)&1:
                visit(start,w,seen|(1<<w),mask|(1<<i))
    for v in range(n):
        visit(v,v,1<<v,0)
    return len(es),tuple(b or ()),sorted(rows)

def children(state, rows, incidence):
    mask,k,res=state
    if not mask or not k:
        return []
    def eligible(i):
        m,r=rows[i]
        return m&mask==m and all(a<=b for a,b in zip(r,res))
    pivot=min((i for i in range(mask.bit_length()) if (mask>>i)&1),
              key=lambda i:sum(eligible(j) for j in incidence[i]))
    return [(i,(mask^rows[i][0],k-1,tuple(b-a for a,b in zip(rows[i][1],res))))
            for i in incidence[pivot] if eligible(i)]

def setup(s):
    n,r,rows=compile_rows(s)
    incidence=[[] for _ in range(n)]
    for j,(m,_) in enumerate(rows):
        for i in range(n):
            if (m>>i)&1:incidence[i].append(j)
    return ((1<<n)-1,s["max_pieces"],r),rows,incidence

def replay(s,cert):
    """Replay constructive row cover or complete negative branching DAG."""
    try:
        s=normalize(s);root,rows,incidence=setup(s)
        if not isinstance(cert,dict):
            return None
        if set(cert)=={"kind","rows"} and cert["kind"]=="cover":
            chosen=cert["rows"];m=0;res=[0]*len(root[2])
            if not isinstance(chosen,list) or len(chosen)>root[1]:
                return None
            for i in chosen:
                if not integer(i,0,len(rows)-1):return None
                mask,use=rows[i]
                if m&mask:return None
                m|=mask
                res=[a+b for a,b in zip(res,use)]
            return "proved" if m==root[0] and tuple(res)==root[2] else None
        if set(cert)!={"kind","states"} or cert["kind"]!="no-cover-dag":
            return None
        states=cert["states"]
        if not isinstance(states,list) or not 1<=len(states)<=MAX_STATES:
            return None
        closed=set()
        for row in states:
            if not isinstance(row,list) or len(row)!=3:return None
            m,k,r=row
            if not integer(m,0,root[0]) or not integer(k,0,root[1]):return None
            r=tuple(vector(r,len(root[2])))
            if any(a>b for a,b in zip(r,root[2])):return None
            state=(m,k,r)
            if state in closed or (not m and not any(r)):return None
            if any(child not in closed for _,child in children(state,rows,incidence)):return None
            closed.add(state)
        return "refuted" if state==root else None
    except (ValueError,TypeError,KeyError,OverflowError,RecursionError):
        return None

def solve(s,budget=MAX_STATES):
    s=normalize(s)
    if not integer(budget,1,MAX_STATES):
        raise ValueError("state budget")
    visited=0;dead=set();ordered=[]
    try:
        root,rows,incidence=setup(s)
        def search(state):
            nonlocal visited
            if state in dead:return None
            visited+=1
            if visited>budget:raise OverflowError("state budget")
            m,k,r=state
            if not m and not any(r):return []
            for i,child in children(state,rows,incidence):
                result=search(child)
                if result is not None:return [i]+result
            dead.add(state);ordered.append([m,k,list(r)])
            return None
        result=search(root)
        cert=dict(kind="cover",rows=result) if result is not None else dict(kind="no-cover-dag",states=ordered)
        status="proved" if result is not None else "refuted"
        if replay(s,cert)!=status:raise ArithmeticError("cover replay failed")
        return dict(status=status,certificate=cert,visited=visited,rows=len(rows))
    except OverflowError as e:
        return dict(status="unknown",reason=str(e),visited=visited)

def main():
    import argparse
    from runtime import read_json
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("spec");p.add_argument("--budget",type=int,default=MAX_STATES)
    a=p.parse_args()
    print(json.dumps(solve(read_json(a.spec),a.budget),indent=2))
if __name__=="__main__":main()
