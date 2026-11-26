"""Conservative delayed credit for research proposals, not a proof verifier."""
import math


def statistics(history,modes):
    """Credit a proposal only when its own relevant claim/edge is later reviewed.

    First proposer owns an ID. Credit is capped per attempt; it is a heuristic
    provenance proxy, not causal attribution or an estimate of theorem probability.
    Old histories without verified_items have no attributed credit.
    """
    owners={};credits={};attempts={m:0 for m in modes};costs={m:0.0 for m in modes}
    for index,h in enumerate(history):
        if not h['trusted_review']:
            m=h['mode'];attempts[m]+=1
            elapsed=h.get('elapsed_seconds',1)
            if type(elapsed) not in (int,float) or not math.isfinite(elapsed) or elapsed<0:elapsed=1
            costs[m]+=max(1,min(300,elapsed))
            for op in h['operations']:
                if op['op'] in ('claim','derive'):owners.setdefault((op['op'],op['id']),index)
        else:
            for item in h.get('verified_items',[]):
                owner=owners.get(tuple(item))
                if owner is not None:credits[owner]=1
    return {m:dict(attempts=attempts[m],credits=sum(v for i,v in credits.items() if history[i]['mode']==m),seconds=costs[m]) for m in modes}


def ranking(history,modes):
    stats=statistics(history,modes);total=sum(x['attempts'] for x in stats.values())
    def score(m):
        r=stats[m];n=r['attempts'];mean=r['seconds']/max(1,n)
        # Normalize exploitation by a bounded cost penalty, but not exploration.
        return (r['credits']/(1+n))/(1+math.log1p(mean)/4)+math.sqrt(math.log(2+total)/(1+n))
    return sorted(modes,key=lambda m:-score(m))
