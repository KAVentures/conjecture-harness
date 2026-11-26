"""Bounded proof-route composition over exact, already instantiated statements.

No semantic matching is claimed. Every theorem rule carries an explicit
proof obligation (including literature rules). Plans are not proof certificates.
"""
from itertools import product

def pareto(routes,cap):
    # A subset dominates a superset: shared obligations are counted only once.
    ordered=sorted(set(routes),key=lambda s:(len(s),sorted(s)))
    out=[]
    for r in ordered:
        if not any(a<=r for a in out):
            out.append(r)
        if len(out)==cap:
            break
    return out

def plan(goal,rules,verified=(),cap=32,rounds=12,weights=None):
    """Rules are (conclusion, premises, rule-proof-id). Return open obligations.

    Each rule-proof-id must be separately verified or discharged. The caller
    supplies audit-verified IDs only, not untrusted status flags.
    """
    if not 1<=cap<=64 or not 1<=rounds<=32 or len(rules)>256:
        raise ValueError("search bounds")
    known=set(verified)
    nodes={goal}|known
    for conclusion,premises,proof in rules:
        if not all(isinstance(s,str) and s for s in [conclusion,*premises,proof]) or len(premises)>8 or conclusion in premises or conclusion==proof:
            raise ValueError("invalid rule")
        nodes.update([conclusion,*premises,proof])
    routes={n:[frozenset() if n in known else frozenset([n])] for n in nodes}
    truncated=False
    for _ in range(rounds):
        nxt={n:r[:] for n,r in routes.items()}
        for conclusion,premises,proof in rules:
            if conclusion in known:
                continue
            pools=[routes[p] for p in [*premises,proof]]
            combinations=[frozenset()]
            for pool in pools:
                combinations=pareto([a|b for a,b in product(combinations,pool)],cap)
                if len(combinations)==cap:
                    truncated=True
            # A circular path depending on the conclusion is not progress.
            nxt[conclusion]=pareto(nxt[conclusion]+[r for r in combinations if conclusion not in r],cap)
        if nxt==routes:
            break
        routes=nxt
    weights=weights or {}
    return dict(routes=[sorted(r) for r in sorted(routes[goal],key=lambda r:(sum(weights.get(x,1) for x in r),len(r),sorted(r)))], truncated=truncated, scope="bounded obligation plans; not proof replay")

def evaluate(arms):
    """Matched-budget, externally reviewed outcomes; reject unequal budgets."""
    if len(arms)<2:
        raise ValueError("at least two arms")
    baseline=None;out={}
    for name,rows in arms.items():
        by_id={}
        for r in rows:
            task=r["task"]
            if task in by_id or type(r["calls"]) is not int or r["calls"]<0 or type(r["budget"]) is not int or r["budget"]<1 or r["calls"]>r["budget"] or r["verdict"] not in ("proved","refuted","partial","incorrect","abstained"):
                raise ValueError("invalid evaluation row")
            by_id[task]=r
        budget={k:v["budget"] for k,v in by_id.items()}
        if baseline is None:baseline=budget
        elif budget!=baseline:raise ValueError("unmatched tasks/budgets")
        out[name]=dict(tasks=len(rows),solved=sum(r["verdict"] in ("proved","refuted") for r in rows),calls=sum(r["calls"] for r in rows))
    return out
