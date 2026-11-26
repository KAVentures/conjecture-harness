"""Exact capacity-preserving induced reductions via distinguishability maps."""
import itertools
from capacity import normalize,solve as capacity_solve,replay as capacity_replay,replay_counterexample


def reduced(s,subset):
    s=normalize(s);es={tuple(e) for e in s['edges']}
    if not isinstance(subset,list) or not subset or len(subset)>=s['n'] or any(type(v) is not int or not 0<=v<s['n'] for v in subset) or subset!=sorted(set(subset)):
        raise ValueError('invalid proper induced subset')
    return dict(n=len(subset),edges=[[i,j] for i,j in itertools.combinations(range(len(subset)),2) if (subset[i],subset[j]) in es],upper=s['upper'])


def verify_map(s,subset,mapping):
    """Map distinct nonadjacent vertices to distinct nonadjacent vertices."""
    try:
        h=reduced(s,subset);s=normalize(s);es={tuple(e) for e in s['edges']};hs={tuple(e) for e in h['edges']}
        if not isinstance(mapping,list) or len(mapping)!=s['n'] or any(type(x) is not int or not 0<=x<h['n'] for x in mapping):return False
        if any(mapping[v]!=i for i,v in enumerate(subset)):return False
        return all(mapping[u]!=mapping[v] and tuple(sorted((mapping[u],mapping[v]))) not in hs for u,v in itertools.combinations(range(s['n']),2) if (u,v) not in es)
    except (ValueError,TypeError,KeyError):return False


def fold(s):
    """Delete v when N[u] is contained in N[v], and map v to u."""
    s=normalize(s);es={tuple(e) for e in s['edges']};alive=set(range(s['n']));rep=list(range(s['n']))
    while True:
        neighborhoods={v:{v}|{u for u in alive if tuple(sorted((u,v))) in es} for v in alive}
        pair=next(((v,u) for v in sorted(alive,reverse=True) for u in sorted(alive) if u!=v and neighborhoods[u]<=neighborhoods[v]),None)
        if pair is None:break
        v,u=pair;alive.remove(v);rep=[u if x==v else x for x in rep]
    subset=sorted(alive)
    if len(subset)==s['n']:return None
    mapping=[subset.index(v) for v in rep]
    if not verify_map(s,subset,mapping):raise ArithmeticError('fold map failed replay')
    return dict(subset=subset,mapping=mapping)


def replay(s,cert):
    try:
        if not isinstance(cert,dict) or set(cert)!={'subset','mapping','upper_certificate'}:return False
        return verify_map(s,cert['subset'],cert['mapping']) and capacity_replay(reduced(s,cert['subset']),cert['upper_certificate'])
    except (ValueError,TypeError,KeyError):return False


def solve(s):
    s=normalize(s);m=fold(s)
    if m is None:return dict(status='unknown',reduction=None,certificate=None)
    h=reduced(s,m['subset']);r=capacity_solve(h)
    if r['status']=='proved':
        c=dict(m,upper_certificate=r['certificate'])
        if not replay(s,c):raise ArithmeticError('reduced upper certificate failed replay')
        return dict(status='proved',reduction=m,certificate=c)
    if r['status']=='counterexample':
        words=[[m['subset'][v] for v in w] for w in r['certificate']['words']]
        if not replay_counterexample(s,words):raise ArithmeticError('lifted packing failed replay')
        return dict(status='counterexample',reduction=m,certificate=dict(kind='packing',words=words))
    return dict(status='unknown',reduction=m,certificate=None)
