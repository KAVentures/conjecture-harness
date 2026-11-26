"""Conservative delayed credit for research proposals, not a proof verifier."""
import math


def statistics(history,modes):
    """Attribute reviewed items to their first proposer, with distinct outcomes.

    A false proposed lemma or rejected implication is an adverse result for
    its proposer, not a successful discovery. Negative evidence remains useful
    to the coordinator. Positive and adverse credits are each capped at one
    per attempt. Neither measures causality or mathematical success probability.
    """
    owners={};positive=set();adverse=set();attempts={m:0 for m in modes};costs={m:0.0 for m in modes}
    for index,h in enumerate(history):
        if not h['trusted_review']:
            m=h['mode'];attempts[m]+=1
            elapsed=h.get('elapsed_seconds',1)
            if type(elapsed) not in (int,float) or not math.isfinite(elapsed) or elapsed<0:elapsed=1
            costs[m]+=max(1,min(300,elapsed))
            for op in h['operations']:
                if op['op'] in ('claim','derive'):owners.setdefault((op['op'],op['id']),index)
        else:
            decisions={(('claim' if op['op']=='review_claim' else 'derive'),op['id']):op['decision'] for op in h['operations'] if op['op'] in ('review_claim','review_edge')}
            for item in h.get('verified_items',[]):
                key=tuple(item);owner=owners.get(key)
                if owner is None:continue
                # A claim can be established via closure without a direct review.
                # Edge decisions must be explicit; absence is not positive evidence.
                decision=decisions.get(key,'established' if key[0]=='claim' else None)
                if decision in ('refuted','rejected'):adverse.add(owner)
                elif decision in ('established','accepted'):positive.add(owner)
    return {m:dict(attempts=attempts[m],credits=sum(history[i]['mode']==m for i in positive),adverse=sum(history[i]['mode']==m for i in adverse),seconds=costs[m]) for m in modes}


def ranking(history,modes,prior=None):
    prior={} if prior is None else prior
    if not isinstance(prior,dict) or any(m not in modes or type(v) not in (int,float) or not math.isfinite(v) or abs(v)>0.15 for m,v in prior.items()):raise ValueError('invalid bounded strategy prior')
    stats=statistics(history,modes);total=sum(x['attempts'] for x in stats.values())
    def score(m):
        r=stats[m];n=r['attempts'];mean=r['seconds']/max(1,n)
        # Penalize failed proposals separately from cost so slow failures do not
        # become artificially attractive. Retain exploration of all modes.
        return (r['credits']/(1+n))/(1+math.log1p(mean)/4)-0.5*r['adverse']/(1+n)+math.sqrt(math.log(2+total)/(1+n))+prior.get(m,0)
    return sorted(modes,key=lambda m:-score(m))


def stagnation(history):
    """Count proposal attempts since verified progress, not checker bookkeeping."""
    count=0
    for h in reversed(history):
        if h['trusted_review'] and h['reward']>0:break
        if not h['trusted_review']:count+=1
    return count
