"""Universal modular polynomial implications, with exact finite residue coverage."""
import itertools,json,math
from runtime import strict_json

PREFIX="Universal modular implication: "
MAX_RESIDUES=65536

def integer(x,a,b):return type(x) is int and a<=x<=b

def poly(terms,n,m):
    if not isinstance(terms,list) or len(terms)>64:raise ValueError("polynomial terms")
    d={}
    for t in terms:
        if not isinstance(t,list) or len(t)!=2:raise ValueError("term")
        e,c=t
        if not isinstance(e,list) or len(e)!=n or not all(integer(x,0,16) for x in e) or not integer(c,-10**12,10**12):raise ValueError("term data")
        k=tuple(e);d[k]=(d.get(k,0)+c)%m
    return [[list(e),c] for e,c in sorted(d.items()) if c]

def normalize(s):
    if not isinstance(s,dict) or set(s)!={"variables","modulus","assumptions","conclusion"}:raise ValueError("modular shape")
    n=s["variables"];m=s["modulus"]
    if not integer(n,1,5) or not integer(m,2,256):raise ValueError("modular dimensions")
    hs=s["assumptions"]
    if not isinstance(hs,list) or len(hs)>16:raise ValueError("assumptions")
    def rel(r):
        if not isinstance(r,dict) or set(r)!={"terms","allowed"}:raise ValueError("relation")
        a=r["allowed"]
        if not isinstance(a,list) or len(a)>m or not all(integer(x,0,m-1) for x in a):raise ValueError("allowed residues")
        return dict(terms=poly(r["terms"],n,m),allowed=sorted(set(a)))
    return dict(variables=n,modulus=m,assumptions=[rel(h) for h in hs],conclusion=rel(s["conclusion"]))

def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(",",":"))

def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError("not modular")
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError("noncanonical modular claim")
    return s

def evaluate(r,x,m):
    return sum(c*math.prod(pow(v,e,m) for v,e in zip(x,es)) for es,c in r["terms"])%m

def bad(s,x):
    m=s["modulus"]
    return all(evaluate(h,x,m) in h["allowed"] for h in s["assumptions"]) and evaluate(s["conclusion"],x,m) not in s["conclusion"]["allowed"]

def factors(m):
    """Pairwise coprime prime-power factors, product exactly m."""
    r=[];p=2
    while p*p<=m:
        if m%p==0:
            q=1
            while m%p==0:m//=p;q*=p
            r.append(q)
        p+=1
    if m>1:r.append(m)
    return r

def crt_children(s):
    # Safe factorization only for divisibility conclusion and no assumptions.
    if s["assumptions"] or s["conclusion"]["allowed"]!=[0]:return []
    fs=factors(s["modulus"])
    if len(fs)<2:return []
    return [normalize(dict(s,modulus=q)) for q in fs]

def replay(s,cert):
    try:
        s=normalize(s);n=s["variables"];m=s["modulus"]
        if not isinstance(cert,dict):return None
        if set(cert)=={"kind","residue"} and cert["kind"]=="counterexample":
            x=cert["residue"]
            return "refuted" if isinstance(x,list) and len(x)==n and all(integer(v,0,m-1) for v in x) and bad(s,x) else None
        if set(cert)!={"kind","count"} or cert["kind"]!="complete-residues" or not integer(cert["count"],1,MAX_RESIDUES) or cert["count"]!=m**n:return None
        return "proved" if not any(bad(s,x) for x in itertools.product(range(m),repeat=n)) else None
    except (ValueError,TypeError,KeyError):return None

def solve(s,budget=MAX_RESIDUES):
    s=normalize(s)
    if not integer(budget,1,MAX_RESIDUES):raise ValueError("budget")
    m=s["modulus"];n=s["variables"];visited=0
    for x in itertools.product(range(m),repeat=n):
        if visited>=budget:return dict(status="unknown",visited=visited,reason="residue budget")
        visited+=1
        if bad(s,x):
            cert=dict(kind="counterexample",residue=list(x))
            if replay(s,cert)!="refuted":raise ArithmeticError("modular witness")
            return dict(status="refuted",certificate=cert,visited=visited)
    cert=dict(kind="complete-residues",count=visited)
    if replay(s,cert)!="proved":raise ArithmeticError("modular coverage")
    return dict(status="proved",certificate=cert,visited=visited)

def bridge(goal,premises,cert):
    try:
        s=parse_statement(goal)
        if cert!={"kind":"coprime-divisibility"} or not isinstance(premises,list):return False
        children=crt_children(s)
        return bool(children) and sorted(premises)==sorted(statement(c) for c in children)
    except (ValueError,TypeError,KeyError):return False

def main():
    import argparse
    from runtime import read_json
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("spec");p.add_argument("--budget",type=int,default=MAX_RESIDUES);a=p.parse_args()
    print(json.dumps(solve(read_json(a.spec),a.budget),indent=2))
if __name__=="__main__":main()
