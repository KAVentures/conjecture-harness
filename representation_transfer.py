"""Checked polynomial substitution as a domain-preserving theorem transfer.

Search is heuristic; the replayed implication is exact. No arbitrary source
theorem or unproved domain condition is silently accepted.
"""
import itertools,json
from fractions import Fraction as F
import polynomial as p
from hypothesis import coefficients
from discovery import check,closure,frontier,record,fingerprint

def constant(n,c):return {(0,)*n:F(c)} if c else {}
def var(n,j):return {tuple(int(i==j) for i in range(n)):F(1)}
def add(a,b):
    r=dict(a)
    for e,c in b.items():r[e]=r.get(e,F(0))+c
    return {e:c for e,c in r.items() if c}
def mul(a,b):
    r={}
    for e,c in a.items():
        for f,d in b.items():
            k=tuple(x+y for x,y in zip(e,f))
            if sum(k)>8:raise ValueError('expanded degree limit')
            r[k]=r.get(k,F(0))+c*d
    if len(r)>512 or any(x.numerator.bit_length()>256 or x.denominator.bit_length()>256 for x in r.values()):raise ValueError('expansion limit')
    return {e:c for e,c in r.items() if c}
def power(a,k,n):
    r=constant(n,1)
    for _ in range(k):r=mul(r,a)
    return r
def compose(source,images,n):
    out={}
    for e,c in coefficients(source).items():
        term=constant(n,c)
        for k,img in zip(e,images):
            if k:term=mul(term,power(img,k,n))
        out=add(out,term)
        if len(out)>512 or any(x.numerator.bit_length()>256 or x.denominator.bit_length()>256 for x in out.values()):raise ValueError('expansion limit')
    return out
def admissible(image,target_domain,source_domain):
    if source_domain=='real':return True
    # Sufficient exact proof that a polynomial image is nonnegative.
    return all(c>=0 and (target_domain=='nonnegative' or all(k%2==0 for k in e)) for e,c in image.items())
def replay(goal,source,certificate):
    try:
        g=p.normalize(goal);s=p.normalize(source);n=len(g['variables'])
        if g['relation']!=s['relation'] or not isinstance(certificate,dict) or set(certificate)!={'images','scale'}:return False
        raw=certificate['images'];scale=p.rational(certificate['scale'])
        if scale<=0 or not isinstance(raw,list) or len(raw)!=len(s['variables']):return False
        images=[p.terms(t,n) for t in raw]
        if not all(admissible(img,g['domain'],s['domain']) for img in images):return False
        return {e:scale*c for e,c in compose(s,images,n).items()}==coefficients(g)
    except (ValueError,TypeError,KeyError,ArithmeticError,AttributeError):return False

def choices(n,domain):
    # Projections, coordinate identifications, sign/scale, shifts, sums,
    # differences and squares. These work for arbitrary input polynomials.
    vs=[var(n,j) for j in range(n)]
    out=vs+[constant(n,0),constant(n,1)]
    for v in vs:
        out.extend([{e:-c for e,c in v.items()},{e:2*c for e,c in v.items()},add(v,constant(n,1)),mul(v,v)])
    for i,j in itertools.combinations(range(n),2):
        out.extend([add(vs[i],vs[j]),add(vs[i],{e:-c for e,c in vs[j].items()})])
    return out

def mappings(goal,source,budget=128,limit=8):
    """Yield distinct checked conclusion maps under one shared search cap."""
    g=p.normalize(goal);s=p.normalize(source);n=len(g['variables']);m=len(s['variables'])
    if type(budget) is not int or not 1<=budget<=2048 or type(limit) is not int or not 1<=limit<=32:raise ValueError('map budget')
    if g['relation']!=s['relation'] or not coefficients(g):return
    opts=[a for a in choices(n,g['domain']) if admissible(a,g['domain'],s['domain'])]
    # First try all coordinate maps, then one nontrivial image at a time,
    # then the full product under a shared cap.
    projections=[var(n,i) for i in range(n) if admissible(var(n,i),g['domain'],s['domain'])]
    if not projections:
        projections=[mul(var(n,i),var(n,i)) for i in range(n)]
    bases=list(itertools.product(projections,repeat=m)) if projections else []
    def candidates():
        yield from bases
        for b in bases[:32]:
            for j in range(m):
                for v in opts:
                    yield b[:j]+(v,)+b[j+1:]
        yield from itertools.product(opts,repeat=m)
    target=coefficients(g);seen=set();tested=0;found=0
    for images in candidates():
        sig=tuple(tuple(sorted(a.items())) for a in images)
        if sig in seen:continue
        seen.add(sig)
        if tested>=budget:break
        tested+=1
        try:q=compose(s,images,n)
        except ValueError:continue
        if set(q)!=set(target) or not q:continue
        k=next(iter(q));scale=target[k]/q[k]
        if scale<=0:continue
        try:cert=dict(images=[p.encode(a) for a in images],scale=str(scale))
        except ValueError:continue
        if replay(g,s,cert):
            yield dict(certificate=cert,tested=tested)
            found+=1
            if found>=limit:return

def synthesize(goal,source,budget=128):
    return next(mappings(goal,source,budget,limit=1),None)

def auto_discharge(g,limit=2,focus_budget=3):
    check(g);count=0;attempted=0
    if type(limit) is not int or not 1<=limit<=16 or type(focus_budget) is not int or not 1<=focus_budget<=16:raise ValueError('transfer pass limits')
    visits={}
    for h in g['history']:visits[h['focus']]=visits.get(h['focus'],0)+1
    for focus in sorted(frontier(g),key=lambda i:(visits.get(i,0),i)):
        if count>=limit or attempted>=focus_budget:break
        if focus not in frontier(g):continue
        try:goal=p.parse_statement(g['nodes'][focus]['statement'])
        except (ValueError,TypeError):continue
        attempted+=1;known=closure(g);pool=[]
        for i in sorted(known):
            try:s=p.parse_statement(g['nodes'][i]['statement'])
            except (ValueError,TypeError):continue
            if s['relation']==goal['relation']:pool.append((i,s))
            if len(pool)>=12:break
        for i,s in pool:
            if i==focus:continue
            r=synthesize(goal,s,budget=64)
            if r is None:continue
            tag='representation-'+fingerprint(focus+'\n'+i)[:32]
            old=next((k for k,e in sorted(g['edges'].items()) if e['parent']==focus and e['premises']==[i] and e['rule']!='rejected'),None)
            if old is not None and g['edges'][old]['rule']=='accepted':continue
            eid=old or tag
            if tag in g['observations']:continue
            ops=[] if old else [dict(op='derive',id=eid,parent=focus,premises=[i],argument='Exact polynomial substitution, domain preservation and positive scale.')]
            detail=json.dumps(dict(edge=eid,premise=i,**r),sort_keys=True)
            ops.extend([dict(op='observe',id=tag,focus=focus,kind='transfer',detail=detail),dict(op='review_edge',id=eid,decision='accepted',evidence='Exact substitution identity '+tag)])
            try:g=record(g,'reformulate',focus,ops,trusted=True)
            except ValueError:continue
            count+=1;break
    return g
