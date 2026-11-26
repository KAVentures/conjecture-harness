"""Counterexample-guided additive polynomial repair; never assumes a weakened claim true."""
import json
from fractions import Fraction as F
import polynomial as p
from discovery import check, frontier, record, fingerprint, closure
from equivalence import claim_key
from runtime import strict_json


def compatible(a,b):
    return (a['variables']==b['variables'] and a['domain']==b['domain'] and
            a['relation']==b['relation']=='nonnegative')


def coefficients(s):
    return p.terms(s['terms'],len(s['variables']))


def add(a,b,scale=F(1)):
    out=dict(a)
    for e,c in b.items():out[e]=out.get(e,F(0))+scale*c
    return {e:c for e,c in out.items() if c}


def with_terms(s,ts):
    return p.normalize(dict(s,terms=p.encode(ts)))


def sum_bridge(goal,premises):
    """Exact sufficient implication from nonnegative summands in the same domain."""
    goal=p.normalize(goal)
    if not isinstance(premises,list) or not 1<=len(premises)<=32:return False
    total={}
    for s in premises:
        s=p.normalize(s)
        if not compatible(goal,s):return False
        total=add(total,coefficients(s))
    return total==coefficients(goal)


def repair(goal,failed,certificate):
    """P(x0)<0: propose P+c and T-(P+c), c=-P(x0). Both need proof."""
    goal=p.normalize(goal);failed=p.normalize(failed)
    if not compatible(goal,failed) or not isinstance(certificate,dict) or certificate.get('kind')!='point' or not p.replay(failed,certificate):return None
    x=list(map(p.rational,certificate['point']));zero=(0,)*len(x)
    c=-p.value(coefficients(failed),x)
    if c<=0:return None
    a=with_terms(failed,add(coefficients(failed),{zero:c}))
    b=with_terms(goal,add(coefficients(goal),coefficients(a),F(-1)))
    # Avoid tautological or vacuous splits and known negative remainder at x0.
    if not any(any(e) for e in coefficients(a)) or not any(any(e) for e in coefficients(b)):return None
    if p.value(coefficients(b),x)<0:return None
    keys=[claim_key(p.statement(s)) for s in (goal,failed,a,b)]
    if len(set(keys))!=4:return None
    if not sum_bridge(goal,[a,b]):raise ArithmeticError('repair identity failed')
    return dict(shift=str(c),point=certificate['point'],premises=[a,b])


def witness_for(g,i):
    """Use only exact point evidence, replayed on the immutable failed claim."""
    if g['nodes'][i]['status']!='refuted':return None
    try:s=p.parse_statement(g['nodes'][i]['statement'])
    except (ValueError,TypeError):return None
    for k,o in sorted(g['observations'].items()):
        if not k.startswith(('poly-','shift-')) or o['focus']!=i or o['kind']!='counterexample':continue
        try:
            report=strict_json(o['detail']);cert=report['certificate']
            if report['status']=='counterexample' and cert.get('kind')=='point' and p.replay(s,cert):return s,cert,k
        except (ValueError,TypeError,KeyError,AttributeError):continue
    return None


def auto_refine(g,limit=2):
    check(g);count=0
    for edge_id,e in sorted(g['edges'].items()):
        if count>=limit:break
        if edge_id.startswith('repair-') or e['rule']=='rejected' or e['parent'] not in frontier(g):continue
        try:goal=p.parse_statement(g['nodes'][e['parent']]['statement'])
        except (ValueError,TypeError):continue
        for failed in e['premises']:
            if count>=limit:break
            found=witness_for(g,failed)
            if found is None:continue
            s,cert,obs=found
            tag=fingerprint(edge_id+'\n'+failed+'\n'+obs)[:24];oid='repair-'+tag
            if oid in g['observations']:continue
            try:r=repair(goal,s,cert)
            except (ValueError,TypeError):continue
            if r is None:continue
            ops=[];ids=[];bad=False
            for j,part in enumerate(r['premises']):
                text=p.statement(part);sig=claim_key(text)
                if any(n['status']=='refuted' and claim_key(n['statement'])==sig for n in g['nodes'].values()):bad=True;break
                existing=next((i for i,n in sorted(g['nodes'].items()) if n['statement']==text),None)
                i=existing or 'repair-'+tag+'-'+str(j)
                if i==e['parent'] or i in ids:bad=True;break
                if existing is None:
                    if i in g['nodes']:bad=True;break
                    ops.append(dict(op='claim',id=i,statement=text))
                ids.append(i)
            if bad:continue
            if any(v['parent']==e['parent'] and set(v['premises'])==set(ids) and v['rule']!='rejected' for v in g['edges'].values()):continue
            detail=json.dumps(dict(source_edge=edge_id,failed_claim=failed,witness_observation=obs,repair=r),sort_keys=True)
            if len(detail)>20000:continue
            ops.extend([dict(op='derive',id=oid,parent=e['parent'],premises=ids,argument='Proposed additive repair: exact sum equals parent. Both new nonnegativity obligations require proof.'),dict(op='observe',id=oid,focus=e['parent'],kind='refinement',detail=detail)])
            try:h=record(g,'refine',e['parent'],ops,trusted=True)
            except ValueError:continue # e.g. reused node creates a dependency cycle
            g=h;count+=1
    return g


def auto_compose(g,limit=2):
    check(g);count=0
    for i,e in sorted(g['edges'].items()):
        if count>=limit:break
        if e['rule']!='candidate' or e['parent'] not in frontier(g) or any(g['nodes'][x]['status']=='refuted' for x in e['premises']):continue
        try:
            goal=p.parse_statement(g['nodes'][e['parent']]['statement']);ps=[p.parse_statement(g['nodes'][x]['statement']) for x in e['premises']]
            if not sum_bridge(goal,ps):continue
        except (ValueError,TypeError):continue
        oid='sum-'+fingerprint(i+'\n'+g['nodes'][e['parent']]['statement']+'\n'+'\n'.join(g['nodes'][x]['statement'] for x in e['premises']))[:32]
        if oid in g['observations']:continue
        detail=json.dumps(dict(edge=i,premises=e['premises'],rule='exact coefficient sum on identical domain'),sort_keys=True)
        g=record(g,'forward',e['parent'],[dict(op='observe',id=oid,focus=e['parent'],kind='proof_sketch',detail=detail),dict(op='review_edge',id=i,decision='accepted',evidence='Exact additive polynomial identity: '+oid)],trusted=True);count+=1
    return g
