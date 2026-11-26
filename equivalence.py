"""Conservative exact equivalence for supported universal typed statements.
Never guesses equivalence from prose, embeddings or sampled values.
"""
from functools import lru_cache
from fractions import Fraction as F
from itertools import permutations
import affine
import polynomial


def orders(n):
    # Full permutation search for small languages only. Larger affine claims
    # still support positional alpha-renaming and row normalization.
    return permutations(range(n)) if n<=4 else [tuple(range(n))]


def scaled(row, signed=False):
    first=next((v for v in row if v),F(1))
    factor=first if signed else abs(first)
    return tuple(v/factor for v in row)


@lru_cache(maxsize=1024)
def signature(text):
    """Exact equivalence implies matching signatures within these transformations.
    Matching signatures imply equivalence; unequal signatures are inconclusive.
    """
    try:
        if text.startswith(affine.PREFIX):
            s=affine.parse_statement(text);n=len(s['variables'])
            def form(order):
                def row(r):return scaled(tuple(F(r[i]) for i in (0,*(j+1 for j in order))))
                assumptions={row(r) for r in s['assumptions']}
                # All constant nonnegative rows become zero or positive one.
                assumptions={r for r in assumptions if any(r[1:]) or r[0]<0}
                return tuple(sorted(assumptions)),row(s['conclusion'])
            return ('affine',n,min(form(o) for o in orders(n)))
        if text.startswith(polynomial.PREFIX):
            s=polynomial.parse_statement(text);n=len(s['variables']);p=polynomial.terms(s['terms'],n)
            def form(order):
                pairs=sorted((tuple(e[i] for i in order),v) for e,v in p.items())
                co=scaled(tuple(v for _,v in pairs),signed=s['relation']=='zero')
                return tuple((e,v) for (e,_),v in zip(pairs,co))
            return ('polynomial',n,s['domain'],s['relation'],min(form(o) for o in orders(n)))
    except (ValueError,TypeError,KeyError,RecursionError):
        pass
    return None


def claim_key(text):
    s=signature(text)
    return ('typed',s) if s is not None else ('text',' '.join(text.split()))


def equivalent(a,b):
    s=signature(a)
    return s is not None and s==signature(b)


def auto_reuse(g,limit=2):
    """Transfer reviewed status to an equivalent legacy reachable node.
    Preserves original text, cites source node, inherits its trust level.
    No new truth is inferred from a candidate or an observation.
    """
    from discovery import check,closure,frontier,record,fingerprint
    check(g);count=0
    for target in frontier(g):
        if count>=limit:break
        if target not in frontier(g):continue
        sig=signature(g['nodes'][target]['statement'])
        if sig is None:continue
        known=closure(g);matches=[]
        for i,n in sorted(g['nodes'].items()):
            if i==target or signature(n['statement'])!=sig:continue
            if i in known:matches.append((i,'established'))
            elif n['status']=='refuted':matches.append((i,'refuted'))
        if not matches:continue
        if len({status for _,status in matches})!=1:raise ValueError('conflicting equivalent reviewed claims')
        source,status=matches[0]
        detail=f'Exact typed equivalence of {source} and {target}; positive scaling, alpha-renaming, permitted variable permutation, row normalization. Inherits source review status; inspect source evidence.'
        ident='equiv-'+fingerprint(source+'\n'+target+'\n'+status)[:32]
        ops=[dict(op='observe',id=ident,focus=target,kind='transfer',detail=detail),dict(op='review_claim',id=target,decision=status,evidence='Equivalent reviewed claim '+source+'; '+ident)]
        g=record(g,'forward' if status=='established' else 'falsify',target,ops,trusted=True);count+=1
    return g
