"""Small transparent known controls for matched graph-evaluation budgets, not an AI benchmark."""
import json
from graph_lemma import search


def run():
    controls=[
        ('dense-clique',5,['connected'],{'omega':-1},-3,True),
        ('sparse-degree',5,['connected'],{'Delta':-1},-3,True),
        ('independence-lower',5,['connected'],{'alpha':1},3,True),
        ('triangle-free-degree',5,['connected','triangle_free'],{'delta':-1},-1,True),
        ('edge-bound',5,[],{'m':-1},-9,True),
        ('order-dominates-alpha',5,[],{'n':1,'alpha':-1},0,False),
        ('connected-size',5,['connected'],{'m':1,'n':-1},-1,False),
        ('sparse-edge',5,[],{'m':-1},0,True),
    ]
    results=[]
    for name,n,props,c,b,has_counterexample in controls:
        spec=dict(min_n=n,properties=props,coefficients=c,constant=b)
        row={'id':name,'spec':spec,'known_counterexample_exists':has_counterexample,'results':{}}
        for strategy in ('exhaustive','families_first'):
            r=search(spec,n,16,strategy)
            found=r['status']=='counterexample'
            if found and not has_counterexample:raise AssertionError('false positive on true control')
            row['results'][strategy]={'found':found,'tested':r['tested'],'witness':r['witness'],'replay':r['replay']}
        results.append(row)
    return {'scope':'hand-selected known graph inequality controls, 16 graph evaluations per strategy and target; no model calls, open problems or statistical generalization','results':results,'found':{s:sum(r['results'][s]['found'] for r in results) for s in ('exhaustive','families_first')}}

if __name__=='__main__':print(json.dumps(run(),indent=2))
