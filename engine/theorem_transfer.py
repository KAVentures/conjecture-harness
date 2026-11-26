"""Checked theorem transfer for graph capacity, with exact conditional bridges."""
import itertools,json
from fractions import Fraction as F
import capacity as c
from discovery import check,closure,frontier,record,fingerprint

RULE='capacity-complement-map-power-v1'
SOURCE='J. Zuiddam, The asymptotic spectrum of graphs and the Shannon capacity, arXiv:1807.00169, graph preorder and Shannon capacity; https://arxiv.org/abs/1807.00169'


def power_graph(s,k):
    s=c.normalize(s)
    if type(k) is not int or not 1<=k<=5 or s['n']**k>32:raise ValueError('power graph limit')
    words=list(itertools.product(range(s['n']),repeat=k));es={tuple(e) for e in s['edges']}
    return len(words),[(i,j) for i,j in itertools.combinations(range(len(words)),2) if all(x==y or tuple(sorted((x,y))) in es for x,y in zip(words[i],words[j]))]


def nonedges(n,es):
    es={tuple(e) for e in es}
    return [(i,j) for i,j in itertools.combinations(range(n),2) if (i,j) not in es]


def replay(goal,premise,cert):
    try:
        g=c.normalize(goal);h=c.normalize(premise)
        if not isinstance(cert,dict) or set(cert)!={'rule','power','mapping'} or cert['rule']!=RULE:return False
        k=cert['power'];n,es=power_graph(g,k);m=cert['mapping']
        if not isinstance(m,list) or len(m)!=n or any(type(v) is not int or not 0<=v<h['n'] for v in m):return False
        if F(h['upper'])>F(g['upper'])**k:return False
        ne=set(nonedges(h['n'],h['edges']))
        return all(tuple(sorted((m[i],m[j]))) in ne for i,j in nonedges(n,es))
    except (ValueError,TypeError,KeyError,OverflowError):return False


def search(goal,premise,budget=2000):
    g=c.normalize(goal);h=c.normalize(premise)
    if type(budget) is not int or not 1<=budget<=10000:raise ValueError('invalid search budget')
    tested=0
    for k in range(1,6):
        if g['n']**k>32 or tested>=budget:break
        if F(h['upper'])>F(g['upper'])**k:continue
        n,es=power_graph(g,k);ns=[set() for _ in range(n)];hs=[set() for _ in range(h['n'])]
        for i,j in nonedges(n,es):ns[i].add(j);ns[j].add(i)
        for i,j in nonedges(h['n'],h['edges']):hs[i].add(j);hs[j].add(i)
        mapping={}
        def visit():
            nonlocal tested
            if len(mapping)==n:return [mapping[i] for i in range(n)]
            if tested>=budget:return None
            tested+=1
            def opts(i):
                available=set(range(h['n']))
                for j in ns[i]&mapping.keys():available&=hs[mapping[j]]
                return sorted(available)
            i,choices=min(((i,opts(i)) for i in range(n) if i not in mapping),key=lambda x:(len(x[1]),-len(ns[x[0]]),x[0]))
            for v in choices:
                mapping[i]=v;r=visit();del mapping[i]
                if r is not None:return r
                if tested>=budget:break
            return None
        m=visit()
        if m is not None:
            cert=dict(rule=RULE,power=k,mapping=m)
            if not replay(g,h,cert):raise ArithmeticError('theorem transfer replay failed')
            return dict(status='proved_bridge',tested=tested,certificate=cert)
    return dict(status='unknown',tested=tested,certificate=None)


def auto_transfer(g,limit=2):
    """Check existing candidate bridges, then seek links to established claims.

    Each application is conditional on the premise; no external text can
    certify a theorem or a reviewed premise. Bounded searches per pass.
    """
    check(g);attempts=0
    tried=set()
    for i,o in g['observations'].items():
        if i.startswith('theorem-'):
            d=json.loads(o['detail']);tried.add((d['parent'],d['premise']))
    def typed(i):
        try:return c.parse_statement(g['nodes'][i]['statement'])
        except (ValueError,TypeError):return None
    jobs=[]
    f=set(frontier(g))
    for i,e in sorted(g['edges'].items()):
        if e['parent'] in f and e['rule']=='candidate' and len(e['premises'])==1:jobs.append((e['parent'],e['premises'][0],i))
    for a in sorted(f):
        if typed(a) is None:continue
        for b in sorted(closure(g)):
            if a!=b and not any(e['parent']==a and e['premises']==[b] for e in g['edges'].values()):jobs.append((a,b,None))
    for a,b,edge in jobs:
        if attempts>=limit:break
        if a not in frontier(g) or (a,b) in tried or g['nodes'][b]['status']=='refuted':continue
        x,y=typed(a),typed(b)
        if x is None or y is None:continue
        attempts+=1;tried.add((a,b));r=search(x,y,budget=1000)
        oid='theorem-'+fingerprint(a+'\n'+b)[:24];detail=json.dumps(dict(parent=a,premise=b,source=SOURCE,report=r),sort_keys=True)
        ops=[dict(op='observe',id=oid,focus=a,kind='transfer' if r['status']=='proved_bridge' else 'experiment',detail=detail)]
        if r['status']=='proved_bridge':
            if not replay(x,y,r['certificate']):raise ArithmeticError('transfer failed replay')
            if edge is None:
                edge=oid;ops.append(dict(op='derive',id=edge,parent=a,premises=[b],argument='Verified complement homomorphism from strong power; capacity power identity'))
            ops.append(dict(op='review_edge',id=edge,decision='accepted',evidence='Exact theorem hypotheses in '+oid))
        try:g=record(g,'forward',a,ops,trusted=True)
        except ValueError:continue # conservatively reject dependency cycles
    return g
