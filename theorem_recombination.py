"""Exact simultaneous recombination of independently proved theorem instances.

Search produces candidate implications. Every source theorem and every
nontrivial instantiated hypothesis is a distinct proof obligation. Exact
replay checks domain preservation, positive weights and the polynomial identity.
"""
import json
from itertools import product,islice
from fractions import Fraction as Q
import polynomial as p
import conditional_theorems as ct
import representation_transfer as rt
from hypothesis import coefficients
from theorem_application import target
from rational_cone import solve as cone_solve
from discovery import check,frontier,record,fingerprint
from proof_audit import audit

def source_spec(text):
    return target(text)[0]

def context(g,q):
    # Directly discharge only exact positive multiples of context constraints
    # (both signs for equality) or manifestly nonnegative monomials.
    if rt.admissible(q,g['domain'],'nonnegative'):
        return True
    n=len(g['variables'])
    for h in g['assumptions']:
        a=p.terms(h['terms'],n)
        if a and set(a)==set(q):
            k=next(iter(a));w=q[k]/a[k]
            if (w>0 or h['relation']=='zero') and all(q[e]==w*v for e,v in a.items()):
                return True
    return False

def instance(g,source,images):
    s=source_spec(source);n=len(g['variables'])
    if not isinstance(images,list) or len(images)!=len(s['variables']):
        raise ValueError('image count')
    im=[p.terms(t,n) for t in images]
    q=rt.compose(ct.conclusion(s),im,n)
    ps=[source]
    def require(z):
        if context(g,z):return
        if g['assumptions']:
            t=ct.statement(dict(g,conclusion=p.encode(z)))
        else:
            t=p.statement(ct.poly(g['variables'],g['domain'],p.encode(z)))
        if t not in ps:ps.append(t)
    # A conditional domain transfer is sound only when each substituted
    # coordinate is explicitly nonnegative in the target context.
    if s['domain']=='nonnegative':
        for a in im:require(a)
    for h in s['assumptions']:
        hq=rt.compose(ct.poly(s['variables'],s['domain'],h['terms'],h['relation']),im,n)
        for sign in ([1,-1] if h['relation']=='zero' else [1]):
            z={e:sign*v for e,v in hq.items()}
            require(z)
    return q,ps

def obligations(goal,cert):
    g,gp,_=target(goal)
    if not isinstance(cert,dict) or set(cert)!={'instances','context_terms'}:
        raise ValueError('certificate shape')
    rows=cert['instances'];ctx=cert['context_terms']
    if not isinstance(rows,list) or not 1<=len(rows)<=16 or not isinstance(ctx,list) or len(ctx)>32:
        raise ValueError('certificate limits')
    total={};ps=[]
    n=len(g['variables'])
    for row in rows:
        if not isinstance(row,dict) or set(row)!={'source','images','weight'}:
            raise ValueError('row shape')
        w=p.rational(row['weight'])
        if w<=0:raise ValueError('positive weights required')
        q,ob=instance(g,row['source'],row['images'])
        total=rt.add(total,{e:w*v for e,v in q.items()})
        for t in ob:
            if t not in ps:ps.append(t)
    for row in ctx:
        if not isinstance(row,list) or len(row)!=2:
            raise ValueError('context term shape')
        raw,w=row
        w=p.rational(w);q=p.terms(raw,n)
        if w<=0 or not context(g,q):
            raise ValueError('unproved context term')
        total=rt.add(total,{e:w*v for e,v in q.items()})
    if total!=coefficients(gp) or goal in ps or len(ps)>32:
        raise ValueError('identity or dependency failure')
    return ps

def replay(goal,premises,cert):
    try:
        ps=obligations(goal,cert)
        return isinstance(premises,list) and len(premises)==len(ps) and set(premises)==set(ps)
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,RecursionError):
        return False

def maps(g,s,budget):
    n=len(g['variables']);m=len(s['variables'])
    opts=rt.choices(n,g['domain'])
    vs=[rt.var(n,j) for j in range(n)]
    # Invent maps from the context itself: coordinate complements,
    # inequality slacks, and affine equality elimination.
    from constraint_maps import candidates as constraint_candidates
    special=constraint_candidates(g)
    opts=special+opts
    bases=list(product(vs,repeat=m))
    seen=set();count=0
    def candidates():
        # Put natural variable correspondence first, then coordinate maps
        # and sparse changes, before a larger Cartesian search.
        if all(v in g['variables'] for v in s['variables']):
            yield tuple(rt.var(n,g['variables'].index(v)) for v in s['variables'])
        # Coordinate permutations and context-derived substitutions receive
        # a reserved early budget before the general product.
        from itertools import permutations
        if m<=n:
            yield from permutations(vs,m)
        for b in bases[:8]:
            for j in range(m):
                for v in special[:8]:
                    yield b[:j]+(v,)+b[j+1:]
        yield from bases
        for b in bases[:16]:
            for j in range(m):
                for v in opts:
                    yield b[:j]+(v,)+b[j+1:]
        yield from product(opts,repeat=m)
    for im in candidates():
        sig=tuple(tuple(sorted(a.items())) for a in im)
        if sig in seen:continue
        seen.add(sig)
        if count>=budget:return
        count+=1
        yield [p.encode(a) for a in im]

def discover(goal,sources,known=(),refuted=(),map_budget=48,column_budget=96):
    g,gp,_=target(goal);t=coefficients(gp);n=len(g['variables'])
    if not 1<=map_budget<=128 or not 8<=column_budget<=128 or len(sources)>16:
        raise ValueError('search bounds')
    known=set(known);refuted=set(refuted);pool=[];seen=set()
    for source in sources:
        if source==goal or source in refuted:continue
        try:s=source_spec(source)
        except (ValueError,TypeError):continue
        for im in maps(g,s,map_budget):
            try:q,ps=instance(g,source,im)
            except (ValueError,ArithmeticError):continue
            if not q or goal in ps or set(ps)&refuted or not set(q)&set(t):
                continue
            # Keep transformations with different unresolved hypotheses,
            # even if they yield an identical conclusion.
            sig=(tuple(sorted(q.items())),tuple(sorted(ps)))
            if sig in seen:continue
            seen.add(sig)
            pool.append((q,dict(source=source,images=im),ps))
    pool.sort(key=lambda v:(sum(x not in known for x in v[2]),
                            -len(set(v[0])&set(t)),len(set(v[0])-set(t)),
                            len(v[0]),v[1]['source']))
    pool=pool[:column_budget]
    ctx=[]
    for h in g['assumptions']:
        a=p.terms(h['terms'],n)
        if a:ctx.append(a)
        if a and h['relation']=='zero':ctx.append({e:-v for e,v in a.items()})
    for e,v in t.items():
        a={e:Q(1)}
        if v>0 and context(g,a):ctx.append(a)
    if not pool:return None
    ctx=ctx[:32]
    # First prefer sources whose hypotheses are already audited. Then
    # widen to candidates, retaining all resulting obligations.
    ready=[v for v in pool if all(x in known for x in v[2])]
    for active in (ready,pool):
        if not active:continue
        try:w,_=cone_solve([v[0] for v in active]+ctx,t,256)
        except ValueError:continue
        if w is None:continue
        rows=[dict(v[1],weight=str(z)) for v,z in zip(active,w) if z]
        if not rows:continue
        cert=dict(instances=rows,context_terms=[[p.encode(q),str(z)] for q,z in zip(ctx,w[len(active):]) if z])
        try:ps=obligations(goal,cert)
        except (ValueError,ArithmeticError):continue
        if len(json.dumps(cert))<=15000 and replay(goal,ps,cert):
            return dict(certificate=cert,premises=ps)
    return None

def insert(g,focus,hit,provenance=None):
    check(g);goal=g['nodes'][focus]['statement'];ps=hit['premises'];cert=hit['certificate']
    if focus not in frontier(g) or not replay(goal,ps,cert):
        raise ValueError('invalid bridge')
    tag='theorem-combination-'+fingerprint(focus+'\n'+json.dumps(cert,sort_keys=True))[:32]
    if tag in g['observations']:return g
    ops=[];ids=[]
    for t in ps:
        i=next((k for k,v in sorted(g['nodes'].items()) if v['statement']==t),None)
        if i is None:
            i='combination-node-'+fingerprint(t)[:24]
            ops.append(dict(op='claim',id=i,statement=t))
        elif g['nodes'][i]['status']=='refuted':return g
        ids.append(i)
    old=next((i for i,e in sorted(g['edges'].items()) if e['parent']==focus and set(e['premises'])==set(ids) and e['rule']!='rejected'),None)
    if old and g['edges'][old]['rule']=='accepted':return g
    edge=old or tag
    if old is None:
        ops.append(dict(op='derive',id=edge,parent=focus,premises=ids,
                        argument='Positive rational combination of exact theorem instances; all source theorems and substituted hypotheses remain obligations.'))
    detail=json.dumps(dict(edge=edge,certificate=cert,provenance=provenance),sort_keys=True)
    if len(detail)>20000:return g
    ops.extend([dict(op='observe',id=tag,focus=focus,kind='transfer',detail=detail),
                dict(op='review_edge',id=edge,decision='accepted',evidence='Exact theorem combination '+tag)])
    return record(g,'recombine',focus,ops,trusted=True)

def auto_discharge(g,limit=1):
    check(g)
    active=[]
    for i in frontier(g):
        try:target(g['nodes'][i]['statement'])
        except (ValueError,TypeError):continue
        active.append(i)
        if len(active)>=limit:break
    if not active:return g
    report=audit(g)
    if report['conflicts']:return g
    known=[g['nodes'][i]['statement'] for i in report['proved']]
    refuted=[v['statement'] for i,v in g['nodes'].items() if i in report['refuted'] or v['status']=='refuted']
    pool=[]
    for i,v in sorted(g['nodes'].items(),key=lambda z:(z[0] not in report['proved'],z[0])):
        if v['status']=='refuted':continue
        try:source_spec(v['statement'])
        except (ValueError,TypeError):continue
        pool.append(v['statement'])
        if len(pool)>=16:break
    for focus in active:
        if focus not in frontier(g):continue
        goal=g['nodes'][focus]['statement']
        try:hit=discover(goal,pool,known,refuted)
        except (ValueError,TypeError,ArithmeticError):continue
        if hit:
            try:g=insert(g,focus,hit)
            except ValueError:continue
    return g
