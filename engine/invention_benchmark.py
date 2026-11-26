"""Deterministic same-family controls; not a generalization or open-problem test."""
import itertools,json
import polynomial as p
from lemma_invention import invent,replay


def run():
    families=[('development',([1,2,4,8],[1,2,3],[1,2])),('additional_parameters',([3,5,7],[2,4],[3,4]))]
    rows=[]
    for name,params in families:
        for a,b,c in itertools.product(*params):
            s=dict(variables=['x','y'],domain='real',relation='nonnegative',terms=[[[4,0],a],[[0,4],a],[[2,2],b*b-2*a],[[1,2],2*b*c],[[0,2],c*c]])
            before=p.solve(s)['status'];r=invent(s) if before=='unknown' else None
            after=before
            if r and replay(s,r):after='proved'
            if before=='counterexample':raise ArithmeticError('known SOS family refuted')
            rows.append(dict(family=name,parameters=[a,b,c],spec=s,before=before,after=after,invention=r))
    return dict(scope='selected parameter family, no model calls; not independent held-out families',results=rows,summary={name:dict(total=sum(r['family']==name for r in rows),baseline_proved=sum(r['family']==name and r['before']=='proved' for r in rows),invention_proved=sum(r['family']==name and r['after']=='proved' for r in rows)) for name,_ in families})

if __name__=='__main__':print(json.dumps(run(),indent=2))
