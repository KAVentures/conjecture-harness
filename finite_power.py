"""Exact finite strong-power packing decisions with checkable coloring trees."""
import itertools,json
from capacity import normalize as graph_normalize
from runtime import strict_json

PREFIX='Finite strong-power independence upper bound: '


def normalize(s):
    if not isinstance(s,dict) or set(s)!={'n','edges','power','upper'}:raise ValueError('invalid finite power spec')
    g=graph_normalize(dict(n=s['n'],edges=s['edges'],upper=1));k=s['power'];b=s['upper']
    if type(k) is not int or not 1<=k<=8 or g['n']**k>1024 or type(b) is not int or not 0<=b<=1024:raise ValueError('finite power limits exceeded')
    return dict(n=g['n'],edges=g['edges'],power=k,upper=b)


def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))


def parse_statement(t):
    if not t.startswith(PREFIX):raise ValueError('not a finite-power claim')
    s=strict_json(t[len(PREFIX):])
    if statement(s)!=t:raise ValueError('noncanonical claim')
    return s


def bits(m):
    while m:
        b=m&-m;yield b.bit_length()-1;m^=b


def graph(s):
    s=normalize(s);n=s['n'];k=s['power'];es={tuple(e) for e in s['edges']}
    words=list(itertools.product(range(n),repeat=k));adj=[0]*len(words)
    for i,a in enumerate(words):
        for j in range(i):
            if any(x!=y and tuple(sorted((x,y))) not in es for x,y in zip(a,words[j])):
                adj[i]|=1<<j;adj[j]|=1<<i
    return words,adj


def transitive(s,perms):
    """Check explicit automorphisms mapping vertex zero to every vertex."""
    n=s['n'];es={tuple(e) for e in s['edges']}
    if not isinstance(perms,list) or len(perms)!=n:return False
    for a in perms:
        if not isinstance(a,list) or len(a)!=n or any(type(x) is not int for x in a) or set(a)!=set(range(n)):return False
        if {tuple(sorted((a[u],a[v]))) for u,v in es}!=es:return False
    return {a[0] for a in perms}==set(range(n))


def find_symmetry(s,budget=2000):
    """Find explicit transitivity witnesses by bounded adjacency-preserving search."""
    s=normalize(s);n=s['n'];es={tuple(e) for e in s['edges']}
    if type(budget) is not int or not 1<=budget<=20000:raise ValueError('invalid symmetry budget')
    neighbors=[{j for j in range(n) if tuple(sorted((i,j))) in es} for i in range(n)]
    degrees=list(map(len,neighbors));tested=0;perms=[]
    if len(set(degrees))!=1:return None
    for target in range(n):
        m={0:target};used={target}
        def visit():
            nonlocal tested
            if len(m)==n:return [m[i] for i in range(n)]
            if tested>=budget:return None
            tested+=1
            def options(i):return [j for j in range(n) if j not in used and degrees[i]==degrees[j] and all((a in neighbors[i])==(b in neighbors[j]) for a,b in m.items())]
            i,opts=min(((i,options(i)) for i in range(n) if i not in m),key=lambda item:(len(item[1]),item[0]))
            for j in opts:
                m[i]=j;used.add(j);r=visit();used.remove(j);del m[i]
                if r is not None:return r
                if tested>=budget:break
            return None
        r=visit()
        if r is None:return None
        perms.append(r)
    if not transitive(s,perms):raise ArithmeticError('automorphism replay failed')
    return perms


def coloring(mask,adj):
    groups=[]
    while mask:
        group=[];available=mask
        while available:
            v=(available&-available).bit_length()-1;group.append(v);mask^=1<<v;available&=~((1<<v)|adj[v])
        groups.append(group)
    return groups


def search(s,budget=2000,perms=None):
    s=normalize(s)
    if type(budget) is not int or not 1<=budget<=10000:raise ValueError('invalid node budget')
    if perms is not None and not transitive(s,perms):raise ValueError('invalid symmetry certificate')
    words,adj=graph(s);tested=0;best=[];b=s['upper']
    root=(1<<len(words))-1;chosen=[]
    if perms is not None:root=adj[0];chosen=[0]
    def visit(mask,path):
        nonlocal tested,best
        if len(path)>len(best):best=path[:]
        if len(path)>b:return 'counterexample',path
        if tested>=budget or len(path)>128:return 'unknown',None
        tested+=1;colors=coloring(mask,adj)
        if len(path)+len(colors)<=b:return 'proved',{'colors':colors}
        # Partition all cliques by their last vertex in the coloring order.
        remaining=mask;branches=[]
        for v in reversed([x for c in colors for x in c]):
            status,t=visit(remaining&adj[v],path+[v]);remaining^=1<<v
            if status!='proved':return status,t
            branches.append([v,t])
        return 'proved',{'branches':branches}
    status,t=visit(root,chosen)
    cert={'permutations':perms,'tree':t} if status=='proved' else None
    if status=='proved' and not replay(s,cert):raise ArithmeticError('coloring proof failed replay')
    witness=[list(words[i]) for i in best]
    return dict(status=status,nodes=tested,certificate=cert,witness=witness)


def packing(s,w):
    s=normalize(s);es={tuple(e) for e in s['edges']}
    if not isinstance(w,list) or not 1<=len(w)<=1024:return False
    if any(not isinstance(a,list) or len(a)!=s['power'] or any(type(x) is not int or not 0<=x<s['n'] for x in a) for a in w):return False
    return all(any(x!=y and tuple(sorted((x,y))) not in es for x,y in zip(a,b)) for a,b in itertools.combinations(w,2))


def replay(s,cert):
    """Check the proof tree, not the heuristic search order."""
    try:
        s=normalize(s);_,adj=graph(s);b=s['upper'];count=0
        if not isinstance(cert,dict) or set(cert)!={'permutations','tree'}:return False
        perms=cert['permutations'];root=(1<<len(adj))-1;size=0
        if perms is not None:
            if not transitive(s,perms):return False
            root=adj[0];size=1
        def visit(mask,k,t):
            nonlocal count
            count+=1
            if count>10000 or k>b or k>128 or not isinstance(t,dict):return False
            if set(t)=={'colors'}:
                colors=t['colors'];seen=0
                if not isinstance(colors,list) or k+len(colors)>b:return False
                for c in colors:
                    if not isinstance(c,list) or not c:return False
                    group=0
                    for v in c:
                        if type(v) is not int or not 0<=v<len(adj) or not (mask>>v&1) or seen>>v&1 or group&adj[v]:return False
                        group|=1<<v;seen|=1<<v
                return seen==mask
            if set(t)!={'branches'} or not isinstance(t['branches'],list) or not mask:return False
            for item in t['branches']:
                if not isinstance(item,list) or len(item)!=2:return False
                v,child=item
                if type(v) is not int or not 0<=v<len(adj) or not mask>>v&1:return False
                if not visit(mask&adj[v],k+1,child):return False
                mask^=1<<v
            return mask==0
        return visit(root,size,cert['tree'])
    except (ValueError,TypeError,KeyError,RecursionError):return False
