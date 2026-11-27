"""Exact finite integer constraint discovery. No arbitrary executable inputs."""
import itertools,json
from runtime import strict_json

PREFIX="Finite constraint feasibility: "
MAX_VARS=16
MAX_DOMAIN=16
MAX_ROWS=64
MAX_STATES=768

def integer(x,a,b):return type(x) is int and a<=x<=b

def normalize(s):
    if not isinstance(s,dict) or set(s)!={"domains","constraints"}:raise ValueError("constraint shape")
    ds=s["domains"];cs=s["constraints"]
    if not isinstance(ds,list) or not 1<=len(ds)<=MAX_VARS or not isinstance(cs,list) or len(cs)>MAX_ROWS:raise ValueError("dimensions")
    domains=[]
    for d in ds:
        if not isinstance(d,list) or not 1<=len(d)<=MAX_DOMAIN or not all(integer(x,-1000,1000) for x in d) or len(set(d))!=len(d):raise ValueError("domain")
        domains.append(sorted(d))
    n=len(ds);constraints=[]
    for row in cs:
        if not isinstance(row,dict) or row.get("kind") not in ("linear","different","table"):raise ValueError("constraint kind")
        k=row["kind"]
        if k=="linear":
            if set(row)!={"kind","coefficients","relation","rhs"}:raise ValueError("linear shape")
            a=row["coefficients"]
            if not isinstance(a,list) or len(a)!=n or not all(integer(x,-1000,1000) for x in a) or row["relation"] not in ("eq","le","ge") or not integer(row["rhs"],-100000000,100000000):raise ValueError("linear data")
            r=dict(row)
        else:
            expected={"kind","variables"} if k=="different" else {"kind","variables","allowed"}
            if set(row)!=expected:raise ValueError("constraint shape")
            vs=row["variables"]
            if not isinstance(vs,list) or not vs or not all(integer(i,0,n-1) for i in vs) or len(set(vs))!=len(vs):raise ValueError("variable list")
            r=dict(kind=k,variables=list(vs))
            if k=="table":
                allowed=row["allowed"]
                if not isinstance(allowed,list) or len(allowed)>1024:raise ValueError("table bound")
                for t in allowed:
                    if not isinstance(t,list) or len(t)!=len(vs) or not all(type(x) is int and x in domains[i] for i,x in zip(vs,t)):raise ValueError("table row")
                r["allowed"]=[list(t) for t in sorted(set(map(tuple,allowed)))]
        constraints.append(r)
    constraints.sort(key=lambda x:json.dumps(x,sort_keys=True,separators=(",",":")))
    return dict(domains=domains,constraints=constraints)

def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(",",":"))

def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError("not a finite constraint claim")
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError("noncanonical claim")
    return s

def matching(sets):
    """Hall feasibility via a complete augmenting-path matching."""
    match={}
    def augment(i,seen):
        for x in sorted(sets[i]):
            if x in seen:continue
            seen.add(x)
            if x not in match or augment(match[x],seen):
                match[x]=i;return True
        return False
    return all(augment(i,set()) for i in range(len(sets)))

def possible(row,ds):
    k=row["kind"]
    if k=="linear":
        lo=hi=0
        for a,d in zip(row["coefficients"],ds):
            x,y=a*d[0],a*d[-1];lo+=min(x,y);hi+=max(x,y)
        b=row["rhs"];rel=row["relation"]
        return lo<=b<=hi if rel=="eq" else lo<=b if rel=="le" else hi>=b
    vs=row["variables"]
    if k=="different":return matching([ds[i] for i in vs])
    return any(all(x in ds[i] for i,x in zip(vs,t)) for t in row["allowed"])

def decode(s,a):
    return [d if x is None else [x] for d,x in zip(s["domains"],a)]

def assignment(s,a,partial=False):
    return isinstance(a,list) and len(a)==len(s["domains"]) and all((partial and x is None) or (type(x) is int and x in d) for x,d in zip(a,s["domains"]))

def dead_row(s,a):
    ds=decode(s,a)
    return next((i for i,r in enumerate(s["constraints"]) if not possible(r,ds)),None)

def pivot(s,a):
    return min((i for i,x in enumerate(a) if x is None),key=lambda i:(len(s["domains"][i]),i),default=None)

def replay(s,cert):
    """Replay exact assignment or postorder exhaustive branch DAG."""
    try:
        s=normalize(s)
        if not isinstance(cert,dict):return None
        if set(cert)=={"kind","assignment"} and cert["kind"]=="assignment":
            a=cert["assignment"]
            return "proved" if assignment(s,a) and dead_row(s,a) is None else None
        if set(cert)!={"kind","nodes"} or cert["kind"]!="no-solution":return None
        nodes=cert["nodes"]
        if not isinstance(nodes,list) or not 1<=len(nodes)<=MAX_STATES:return None
        closed=set()
        for row in nodes:
            if not isinstance(row,list) or len(row)!=3:return None
            a,rule,v=row
            if not assignment(s,a,True) or tuple(a) in closed:return None
            if rule=="conflict":
                if not integer(v,0,len(s["constraints"])-1) or possible(s["constraints"][v],decode(s,a)):return None
            elif rule=="split":
                if not integer(v,0,len(a)-1) or a[v] is not None:return None
                if any(tuple(a[:v]+[x]+a[v+1:]) not in closed for x in s["domains"][v]):return None
            else:return None
            closed.add(tuple(a))
        return "refuted" if all(x is None for x in a) else None
    except (ValueError,TypeError,KeyError,RecursionError):return None

def solve(s,budget=MAX_STATES):
    s=normalize(s)
    if not integer(budget,1,MAX_STATES):raise ValueError("budget")
    nodes=[];visited=0
    def search(a):
        nonlocal visited
        visited+=1
        if visited>budget:raise OverflowError("branch budget")
        i=dead_row(s,a)
        if i is not None:nodes.append([a,"conflict",i]);return None
        v=pivot(s,a)
        if v is None:return a
        for x in s["domains"][v]:
            r=search(a[:v]+[x]+a[v+1:])
            if r is not None:return r
        nodes.append([a,"split",v]);return None
    try:
        a=search([None]*len(s["domains"]))
        status="proved" if a is not None else "refuted"
        cert=dict(kind="assignment",assignment=a) if a is not None else dict(kind="no-solution",nodes=nodes)
        if replay(s,cert)!=status:raise ArithmeticError("constraint certificate replay")
        return dict(status=status,certificate=cert,visited=visited)
    except OverflowError:return dict(status="unknown",reason="branch budget",visited=visited)

def main():
    import argparse
    from runtime import read_json
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("spec");p.add_argument("--budget",type=int,default=MAX_STATES);a=p.parse_args()
    print(json.dumps(solve(read_json(a.spec),a.budget),indent=2))
if __name__=="__main__":main()
