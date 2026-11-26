"""Exact fixed-graph independence/clique upper bounds with structural proof DAGs."""
import itertools,json
from runtime import strict_json

PREFIX='Fixed graph invariant upper bound: '
MAX_N=48
MAX_NODES=512

def bits(m):
    while m:
        b=m&-m;yield b.bit_length()-1;m^=b

def normalize(s):
    if not isinstance(s,dict) or set(s)!={'n','edges','invariant','upper'}:raise ValueError('graph claim shape')
    n=s['n'];k=s['upper'];es=s['edges']
    if type(n) is not int or not 1<=n<=MAX_N or type(k) is not int or not 0<=k<=n or s['invariant'] not in ('alpha','omega'):raise ValueError('graph limits')
    if not isinstance(es,list) or len(es)>n*(n-1)//2:raise ValueError('edge list')
    seen=set()
    for e in es:
        if not isinstance(e,list) or len(e)!=2 or any(type(v) is not int for v in e) or not 0<=e[0]<e[1]<n or tuple(e) in seen:raise ValueError('edge')
        seen.add(tuple(e))
    return dict(n=n,edges=[list(e) for e in sorted(seen)],invariant=s['invariant'],upper=k)

def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))
def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('not structural graph claim')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical graph claim')
    return s

def adjacency(s):
    n=s['n'];full=(1<<n)-1;a=[0]*n
    for u,v in s['edges']:a[u]|=1<<v;a[v]|=1<<u
    if s['invariant']=='omega':a=[full^(1<<i)^m for i,m in enumerate(a)]
    return a

def independent(a,m):
    return all(not(a[v]&m) for v in bits(m))

def clique(a,m):
    return all((a[v]&m)==(m^(1<<v)) for v in bits(m))

def components(a,m):
    out=[]
    while m:
        c=m&-m;todo=c
        while todo:
            v=(todo&-todo).bit_length()-1;todo^=1<<v
            more=a[v]&m&~c;c|=more;todo|=more
        out.append(c);m^=c
    return out

def cover(a,m):
    groups=[]
    for v in sorted(bits(m),key=lambda v:(-(a[v]&m).bit_count(),v)):
        bit=1<<v
        for i,c in enumerate(groups):
            if a[v]&c==c:groups[i]|=bit;break
        else:groups.append(bit)
    return groups

def greedy(a,m):
    w=0
    while m:
        v=min(bits(m),key=lambda v:((a[v]&m).bit_count(),v));b=1<<v
        w|=b;m&=~(a[v]|b)
    return w

def dominated(a,m):
    for v in bits(m):
        nv=(a[v]|(1<<v))&m
        for u in bits(a[v]&m):
            if ((a[u]|(1<<u))&m)&~nv==0:return u,v
    return None

def replay(s,cert):
    """Check only explicit local graph identities, never rerun the search."""
    try:
        s=normalize(s);a=adjacency(s);full=(1<<s['n'])-1
        if not isinstance(cert,dict):return None
        if set(cert)=={'kind','vertices'} and cert['kind']=='packing':
            vs=cert['vertices']
            if not isinstance(vs,list) or len(vs)<=s['upper'] or any(type(v) is not int or not 0<=v<s['n'] for v in vs) or len(set(vs))!=len(vs):return None
            return 'refuted' if independent(a,sum(1<<v for v in vs)) else None
        if set(cert)!={'kind','rows'} or cert['kind']!='structure-dag':return None
        rows=cert['rows']
        if not isinstance(rows,list) or not 1<=len(rows)<=MAX_NODES:return None
        bounds={}
        def partition(m,parts):
            if not isinstance(parts,list) or len(parts)>s['n']:return False
            union=0
            for c in parts:
                if type(c) is not int or c<=0 or c&~m or c&union:return False
                union|=c
            return union==m
        for row in rows:
            if not isinstance(row,list) or len(row)!=3:return None
            m,rule,data=row
            if type(m) is not int or m<0 or m&~full or m in bounds:return None
            if rule=='cover':
                if not partition(m,data) or any(not clique(a,c) for c in data):return None
                bound=len(data)
            elif rule=='components':
                if not partition(m,data) or len(data)<2 or any(c not in bounds for c in data):return None
                if any(a[v]&(m^c) for c in data for v in bits(c)):return None
                bound=sum(bounds[c] for c in data)
            elif rule=='fold':
                if not isinstance(data,list) or len(data)!=2 or any(type(v) is not int or not 0<=v<s['n'] or not(m>>v&1) for v in data):return None
                u,v=data
                if u==v or ((a[u]|(1<<u))&m)&~((a[v]|(1<<v))&m):return None
                child=m^(1<<v)
                if child not in bounds:return None
                bound=bounds[child]
            elif rule=='branch':
                if type(data) is not int or not 0<=data<s['n'] or not(m>>data&1):return None
                left=m^(1<<data);right=m&~(a[data]|(1<<data))
                if left not in bounds or right not in bounds:return None
                bound=max(bounds[left],1+bounds[right])
            else:return None
            bounds[m]=bound
        return 'proved' if rows[-1][0]==full and bounds[full]<=s['upper'] else None
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError):return None

def solve(s,budget=256):
    s=normalize(s)
    if type(budget) is not int or not 1<=budget<=MAX_NODES:raise ValueError('node budget')
    a=adjacency(s);full=(1<<s['n'])-1;rows=[];memo={};visited=0
    def packing(w):
        cert=dict(kind='packing',vertices=list(bits(w)))
        if replay(s,cert)!='refuted':raise ArithmeticError('packing replay failed')
        return dict(status='refuted',certificate=cert,visited=visited)
    w=greedy(a,full)
    if w.bit_count()>s['upper']:return packing(w)
    class Exhausted(Exception):pass
    def visit(m):
        nonlocal visited
        if m in memo:return memo[m]
        if visited>=budget:raise Exhausted
        visited+=1;w=greedy(a,m);groups=cover(a,m)
        if w.bit_count()==len(groups):
            row=[m,'cover',groups]
        else:
            cs=components(a,m)
            if len(cs)>1:
                w=0
                for c in cs:w|=visit(c)
                row=[m,'components',cs]
            else:
                pair=dominated(a,m)
                if pair:
                    u,v=pair;w=visit(m^(1<<v));row=[m,'fold',[u,v]]
                else:
                    v=max(bits(m),key=lambda v:((a[v]&m).bit_count(),-v))
                    left=visit(m^(1<<v));right=visit(m&~(a[v]|(1<<v)))|(1<<v)
                    w=max((left,right),key=int.bit_count);row=[m,'branch',v]
        rows.append(row);memo[m]=w;return w
    try:w=visit(full)
    except Exhausted:return dict(status='unknown',visited=visited,scope='bounded structural search')
    if w.bit_count()>s['upper']:return packing(w)
    cert=dict(kind='structure-dag',rows=rows)
    if replay(s,cert)!='proved':raise ArithmeticError('graph bound replay failed')
    return dict(status='proved',certificate=cert,visited=visited,exact_value=w.bit_count())

def main():
    import argparse
    from runtime import read_json
    q=argparse.ArgumentParser(description=__doc__);q.add_argument('spec');q.add_argument('--budget',type=int,default=256);a=q.parse_args()
    print(json.dumps(solve(read_json(a.spec),a.budget),indent=2))
if __name__=='__main__':main()
