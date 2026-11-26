"""Bounded target-only invention of additive SOS lemmas via sparse square extraction.
Every proposed decomposition is checked on the original domain and statement.
"""
import json
from fractions import Fraction as F
import polynomial as p
from hypothesis import add, coefficients, with_terms, sum_bridge
from equivalence import claim_key
from discovery import check, closure, frontier, fingerprint, record


def candidates(s):
    """Enumerate squares whose cross term cancels a term of the target.

    A positive even monomial supplies a diagonal anchor. The second monomial
    may be absent from the original positive diagonal support: its cost is
    transferred to the residual, rather than rejected prematurely.
    """
    t=coefficients(s)
    anchors=sorted((tuple(k//2 for k in e),c) for e,c in t.items()
                   if c>0 and all(k%2==0 for k in e))
    crosses=sorted(t.items(),key=lambda item:(not any(k%2 for k in item[0]),item[1]>=0,item[0]))
    for e,c in crosses:
        for u,d in anchors:
            v=tuple(a-b for a,b in zip(e,u))
            if v==u or min(v)<0 or sum(v)>4:continue
            for ratio in (F(1),F(1,2),F(1,3),F(1,4),F(2,3)):
                w=d*ratio;b=c/(2*w)
                q={u:F(1),v:b}
                a={tuple(2*k for k in u):w,e:c,tuple(2*k for k in v):w*b*b}
                try:
                    cert=dict(kind='sos',squares=[[str(w),p.encode(q)]],monomials=[])
                    A=with_terms(s,a);B=with_terms(s,add(t,a,F(-1)))
                    if len(str(w))>80 or not any(any(k) for k in coefficients(B)):continue
                    yield A,B,cert
                except (ValueError,TypeError):continue


def invent(s,budget=96):
    """Discover two nonnegative summands; exhaustion stays unknown."""
    if type(budget) is not int or not 1<=budget<=512:raise ValueError('invalid candidate budget')
    s=p.normalize(s);tested=0;seen=set()
    def unknown():return dict(status='unknown',tested=tested,parts=None,certificates=None)
    if s['relation']!='nonnegative' or len(s['variables'])<2:return unknown()
    target=claim_key(p.statement(s))
    # Bound candidate enumeration as well as the number of residual proof attempts.
    for A,B,cert in candidates(s):
        if tested>=budget:break
        tested+=1
        pair=(claim_key(p.statement(A)),claim_key(p.statement(B)))
        if target in pair or pair[0]==pair[1] or pair in seen:continue
        seen.add(pair)
        if not sum_bridge(s,[A,B]) or not p.replay(A,cert):raise ArithmeticError('invalid invented summand')
        r=p.solve(B,budget=1)
        if r['status']!='proved':continue
        if not p.replay(B,r['certificate']):raise ArithmeticError('residual certificate failed')
        return dict(status='proved',tested=tested,parts=[A,B],certificates=[cert,r['certificate']])
    return unknown()


def replay(s,r):
    """Check actual decomposition and both universal certificates; never points."""
    try:
        if r['status']!='proved' or len(r['parts'])!=2 or len(r['certificates'])!=2:return False
        return sum_bridge(s,r['parts']) and all(c.get('kind')=='sos' and p.replay(a,c) for a,c in zip(r['parts'],r['certificates']))
    except (ValueError,TypeError,KeyError,AttributeError):return False


def auto_invent(g,limit=1):
    """Only after a direct solver abstained on a bare reachable claim.

    The successful split is represented as two established obligations and an
    accepted additive edge. Original input and certificate are preserved.
    """
    check(g);count=0
    for i in frontier(g):
        if count>=limit:break
        if i not in frontier(g) or any(e['parent']==i for e in g['edges'].values()):continue
        try:s=p.parse_statement(g['nodes'][i]['statement'])
        except (ValueError,TypeError):continue
        if len(s['variables'])<2 or s['relation']!='nonnegative':continue
        if not any(k.startswith('poly-') and o['focus']==i for k,o in g['observations'].items()):continue
        if any(k.startswith('invent-') and o['focus']==i for k,o in g['observations'].items()):continue
        count+=1;r=invent(s);tag=fingerprint(i+'\n'+p.statement(s))[:24];oid='invent-'+tag
        detail=json.dumps(r,sort_keys=True)
        if len(detail)>20000:continue
        ops=[dict(op='observe',id=oid,focus=i,kind='proof_sketch' if r['status']=='proved' else 'experiment',detail=detail)]
        if r['status']=='proved':
            if not replay(s,r):raise ArithmeticError('invented proof failed replay')
            ids=[];newops=[];known=closure(g);skip=False
            for j,part in enumerate(r['parts']):
                text=p.statement(part);sig=claim_key(text)
                if any(n['status']=='refuted' and claim_key(n['statement'])==sig for n in g['nodes'].values()):
                    raise ValueError('invented certificate conflicts with reviewed equivalent refutation')
                existing=next((k for k,n in sorted(g['nodes'].items()) if n['statement']==text),None)
                node=existing or oid+'-'+str(j)
                if node==i or node in ids or (existing is None and node in g['nodes']):skip=True;break
                if existing is None:newops.append(dict(op='claim',id=node,statement=text))
                if node not in known:newops.append(dict(op='review_claim',id=node,decision='established',evidence='Exact SOS certificate '+str(j)+' in observation '+oid))
                ids.append(node)
            if skip:continue
            ops=newops+ops+[dict(op='derive',id=oid,parent=i,premises=ids,argument='Exact sum of two independently certified nonnegative polynomials'),dict(op='review_edge',id=oid,decision='accepted',evidence='Original coefficient identity and SOS replay: '+oid)]
        # Atomic: no half-installed proof when existing graph constraints reject it.
        try:g=record(g,'backward',i,ops,trusted=True)
        except ValueError:continue
    return g
