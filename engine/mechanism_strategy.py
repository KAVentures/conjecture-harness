"""Evidence-weighted strategy mechanisms for stalled proof search.

Mechanisms are bounded prompt templates, not proof rules or executable code.
Credit is attributed to the first proposal of an independently replayed
claim or implication. A refuted auxiliary hypothesis is useful negative
evidence, not a proof of the parent. Scores are heuristic, not calibrated.
"""
from collections import Counter
import math

MECHANISMS={
    'coordinate-reduction':('reformulate','Eliminate constrained coordinates or use a normalized projective chart.','Derive an explicit domain map and the residual inequality; check complete coverage or state the missing direction.'),
    'extremal-structure':('reformulate','Replace an arbitrary object by a simpler extremal configuration.','Derive a feasible perturbation and a sign certificate or show a counterexample to the reduction.'),
    'symbolic-induction':('backward','Invent an invariant under a size-changing recurrence.','Derive the exact recurrence, base case and inductive residual; identify auxiliary invariants without assuming them.'),
    'cancellation-identity':('recombine','Group terms by symmetry or construct a signed cancellation identity.','Find an exact identity reducing the target to a positive combination, and prove or falsify each necessary sign.'),
    'dual-certificate':('backward','Seek a dual, sum-of-squares, entropy, or variational representation.','Show the precise bridge from a certificate to the target, with quantified assumptions and any duality gap.'),
    'equality-analysis':('falsify','Analyze equality and near-equality configurations rather than generic random examples.','Derive the first nonzero perturbation term in a feasible direction, then seek an exact violating witness.'),
    'theorem-combination':('recombine','Combine theorems under different substitutions, retaining hypotheses.','Find a concrete cancellation between theorem conclusions; explicitly discharge or retain all domain and source obligations.'),
    'hypothesis-relaxation':('refine','Weaken a false sufficient lemma without losing the target implication.','Use the exact witness to alter the hypothesis; rederive the bridge before testing the replacement.'),
    'alternative-encoding':('reformulate','Change the underlying mathematical objects, not just notation.','Specify an encoding into a distinct algebraic, combinatorial, or probabilistic structure; identify a theorem available only there.')
}

def statistics(g,report):
    stats={m:dict(attempts=0,positive=0,negative=0,seconds=0.0) for m in MECHANISMS}
    owners={};events={}
    for idx,h in enumerate(g['history']):
        if h['trusted_review']:continue
        m=h.get('research_mechanism')
        if m not in stats:continue
        r=stats[m];r['attempts']+=1
        sec=h.get('elapsed_seconds',1)
        if type(sec) not in (int,float) or not math.isfinite(sec) or sec<0:sec=1
        r['seconds']+=max(1,min(300,sec));events[idx]=m
        for op in h['operations']:
            if op['op'] in ('claim','derive'):
                owners.setdefault((op['op'],op['id']),idx)
    # Only current exact audit results are eligible. Recorded manual review
    # statuses and self-reported reward cannot supply credit.
    positive=set();negative=set()
    for i in report['proved']:
        if ('claim',i) in owners:positive.add(owners['claim',i])
    for i in report['checked_edges']:
        if ('derive',i) in owners:positive.add(owners['derive',i])
    for i in report['refuted']:
        if ('claim',i) in owners:negative.add(owners['claim',i])
    for i in positive:stats[events[i]]['positive']+=1
    for i in negative:stats[events[i]]['negative']+=1
    return stats

def rank(g,report,focus,mode=None):
    if report['conflicts']:return []
    stats=statistics(g,report);total=sum(v['attempts'] for v in stats.values())
    recent=Counter(h.get('research_mechanism') for h in g['history'][-12:] if not h['trusted_review'] and h['focus']==focus)
    out=[]
    for m,(kind,mechanism,test) in MECHANISMS.items():
        r=stats[m];n=r['attempts'];cost=r['seconds']/max(n,1)
        score=(r['positive']+0.2*r['negative'])/(n+1)/(1+math.log1p(cost)/4)
        score+=math.sqrt(math.log(total+2)/(n+1))-0.4*recent[m]
        if mode==kind:score+=0.12
        out.append(dict(id=m,mode=kind,mechanism=mechanism,test=test,score=round(score,6),evidence=r))
    return sorted(out,key=lambda v:(-v['score'],v['id']))

def witnesses(g,report,focus,limit=4):
    """Retrieve actual audited negative evidence on live failed routes."""
    relevant={focus}
    for e in g['edges'].values():
        if e['parent']==focus and e['rule']!='rejected':
            relevant.update(e['premises'])
    out=[]
    for i,oid in sorted(report['refuted'].items()):
        if i not in relevant or oid not in g['observations']:continue
        o=g['observations'][oid]
        if len(o['detail'])>8000:continue
        out.append(dict(claim=i,statement=g['nodes'][i]['statement'],observation=oid,detail=o['detail']))
        if len(out)>=limit:break
    return out
