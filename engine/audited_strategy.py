"""Conservative retrospective credit from independently checked proof evidence.

This is attribution of outcomes, not a causal model or a success probability.
Only proposal attempts that contributed to a replayed proof route receive
positive credit; an exactly refuted proposed claim receives adverse credit.
"""
from discovery import MODES,check
from proof_audit import audit

def statistics(g):
    check(g);r=audit(g)
    if r['conflicts']:raise ValueError('conflicting evidence')
    attempts={m:0 for m in MODES};owners={};positive=set();adverse=set()
    history=g['history']
    for i,h in enumerate(history):
        if h['trusted_review']:continue
        mode=h['mode']
        if mode not in MODES:raise ValueError('invalid history mode')
        attempts[mode]+=1
        for op in h['operations']:
            k=op.get('op');oid=op.get('id')
            if k in ('claim','derive'):owners.setdefault((k,oid),i)
    # Exact negative results are useful but disprove the proposed lemma.
    for i in r['refuted']:
        owner=owners.get(('claim',i))
        if owner is not None:adverse.add(owner)
    # Restrict positive credit to the actual verified goal proof route.
    todo=['goal'] if 'goal' in r['proved'] else [];seen=set()
    while todo:
        i=todo.pop()
        if i in seen:continue
        seen.add(i);w=r['proved'][i]
        owner=owners.get(('claim',i))
        if owner is not None:positive.add(owner)
        if w.startswith('equivalent:'):todo.append(w.split(':',1)[1])
        elif w in r['checked_edges']:
            e=g['edges'][w]
            if e['parent']!=i:raise ValueError('audit edge mismatch')
            todo.extend(e['premises'])
            owner=owners.get(('derive',w))
            if owner is not None:positive.add(owner)
    return {m:dict(attempts=attempts[m],credits=sum(history[i]['mode']==m for i in positive),adverse=sum(history[i]['mode']==m for i in adverse)) for m in MODES}
