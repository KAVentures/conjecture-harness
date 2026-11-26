"""Verify this exact four-vertex counterexample by two methods."""
from pathlib import Path
import itertools,json

def verify(w):
    v=w['vertices']; pairs=w['edges']
    if not isinstance(v,list) or len(v)!=4 or any(type(x) is not int for x in v) or set(v)!=set(range(4)): raise ValueError('expected vertices 0..3')
    if any(not isinstance(e,list) or len(e)!=2 or any(type(x) is not int or x not in v for x in e) or e[0]==e[1] for e in pairs): raise ValueError('invalid edge')
    edges={frozenset(e) for e in pairs}
    if len(edges)!=len(pairs): raise ValueError('duplicate edge')
    adj={x:{y for y in v if frozenset((x,y)) in edges} for x in v}
    reached={v[0]}
    for _ in v: reached|=set().union(*(adj[x] for x in reached))
    degrees=sorted(map(len,adj.values()))
    count=sum(all(frozenset(e) in edges for e in zip(p,p[1:])) for p in itertools.permutations(v))
    result={'connected':len(reached)==4,'degrees':degrees,'hamiltonian_paths':count,'permutations_tested':24,'leaf_obstruction':degrees.count(1)>2}
    if not (result['connected'] and count==0 and result['leaf_obstruction']): raise ValueError('not the certified counterexample')
    return result
if __name__=='__main__': print(json.dumps(verify(json.loads(Path(__file__).with_name('witness.json').read_text())),sort_keys=True))
