"""Exact conditional polynomial inequalities with explicit hypotheses.

The certificate is a polynomial identity: target = SOS residual + sums of
nonnegative multipliers times products of inequality assumptions + arbitrary
multipliers times equality assumptions. Search is bounded and incomplete.
"""
import itertools,json
from fractions import Fraction as Q
import polynomial as p
from hypothesis import coefficients
from representation_transfer import add,mul,constant,admissible
from runtime import strict_json

PREFIX='Conditional polynomial theorem: '

def poly(vs,domain,t,relation='nonnegative'):
    return p.normalize(dict(variables=vs,domain=domain,terms=t,relation=relation))

def normalize(s):
    if not isinstance(s,dict) or set(s)!={'variables','domain','assumptions','conclusion'}:raise ValueError('conditional theorem shape')
    vs=s['variables'];domain=s['domain'];c=poly(vs,domain,s['conclusion'])
    raw=s['assumptions']
    if not isinstance(raw,list) or len(raw)>8:raise ValueError('assumption limit')
    a=[]
    for h in raw:
        if not isinstance(h,dict) or set(h)!={'relation','terms'}:raise ValueError('assumption shape')
        q=poly(vs,domain,h['terms'],h['relation'])
        a.append(dict(relation=q['relation'],terms=q['terms']))
    return dict(variables=c['variables'],domain=domain,assumptions=a,conclusion=c['terms'])

def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))
def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('not conditional theorem')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical theorem')
    return s

def conclusion(s):
    s=normalize(s);return poly(s['variables'],s['domain'],s['conclusion'])

def assumptions(s):
    n=len(s['variables'])
    return [p.terms(a['terms'],n) for a in s['assumptions']]

def scale(a,c):return {e:c*v for e,v in a.items() if c*v}
def sub(a,b):return add(a,scale(b,Q(-1)))

def feasible(s,x):
    if s['domain']=='nonnegative' and any(v<0 for v in x):return False
    return all((p.value(q,x)==0 if h['relation']=='zero' else p.value(q,x)>=0) for h,q in zip(s['assumptions'],assumptions(s)))

def residual(s,rows):
    n=len(s['variables']);a=assumptions(s);out=coefficients(conclusion(s))
    if not isinstance(rows,list) or len(rows)>16:raise ValueError('multiplier count')
    for row in rows:
        if not isinstance(row,dict) or set(row)!={'indices','multiplier'}:raise ValueError('multiplier shape')
        ix=row['indices']
        if not isinstance(ix,list) or not 1<=len(ix)<=3 or any(type(i) is not int or not 0<=i<len(a) for i in ix) or len(set(ix))!=len(ix):raise ValueError('indices')
        m=p.terms(row['multiplier'],n)
        if not any(s['assumptions'][i]['relation']=='zero' for i in ix) and not admissible(m,s['domain'],'nonnegative'):raise ValueError('multiplier sign')
        q=m
        for i in ix:q=mul(q,a[i])
        out=sub(out,q)
    return out

def replay(s,cert):
    try:
        s=normalize(s);n=len(s['variables'])
        if not isinstance(cert,dict):return None
        if cert.get('kind')=='point' and set(cert)=={'kind','point'}:
            if not isinstance(cert['point'],list) or len(cert['point'])!=n:return None
            x=list(map(p.rational,cert['point']))
            return 'refuted' if feasible(s,x) and p.value(coefficients(conclusion(s)),x)<0 else None
        if cert.get('kind')!='conditional-identity' or set(cert)!={'kind','multipliers','residual'}:return None
        rem=residual(s,cert['multipliers'])
        q=poly(s['variables'],s['domain'],p.encode(rem))
        c=cert['residual']
        if not isinstance(c,dict) or c.get('kind')!='sos':return None
        return 'proved' if p.replay(q,c) else None
    except (ValueError,TypeError,KeyError,ArithmeticError,AttributeError):return None

def candidates(s):
    n=len(s['variables']);a=assumptions(s);zero=(0,)*n
    exps=[zero]+[e for e in itertools.product(range(3),repeat=n) if 0<sum(e)<=2]
    for size in (1,2):
        for ix in itertools.combinations(range(len(a)),size):
            eq=any(s['assumptions'][i]['relation']=='zero' for i in ix)
            for e in exps:
                if not eq and s['domain']=='real' and any(k%2 for k in e):continue
                try:
                    q={e:Q(1)}
                    for i in ix:q=mul(q,a[i])
                except ValueError:continue
                if q:yield ix,e,q,eq

def solve(s,budget=128):
    s=normalize(s)
    if type(budget) is not int or not 1<=budget<=512:raise ValueError('search budget')
    target=coefficients(conclusion(s));pool=list(candidates(s))
    # Prefer eliminating a negative term, then try exact residual certificates.
    seen=set();tested=0
    def try_rows(rows,rem):
        nonlocal tested
        if tested>=budget:return None
        key=tuple(sorted(rem.items()))
        if key in seen:return None
        seen.add(key);tested+=1
        try:r=p.solve(poly(s['variables'],s['domain'],p.encode(rem)),budget=1)
        except ValueError:return None
        if r['status']=='proved':
            c=dict(kind='conditional-identity',multipliers=rows,residual=r['certificate'])
            if replay(s,c)!='proved':raise ArithmeticError('conditional replay failed')
            return c
        return None
    def moves(rem):
        options=[]
        # Include every coefficient cancellation, prioritizing removal of
        # negative terms; equality multipliers may have either sign.
        for ix,e,q,eq in pool:
            for k in sorted(set(rem)&set(q)):
                w=rem[k]/q[k]
                if not w or (w<0 and not eq):continue
                r=sub(rem,scale(q,w))
                if r==rem:continue
                try:raw=p.encode({e:w})
                except ValueError:continue
                score=(sum(c<0 for c in r.values()),len(r),sum(abs(c) for c in r.values()))
                options.append((score,dict(indices=list(ix),multiplier=raw),r))
        return sorted(options,key=lambda a:a[0])[:16]
    cert=try_rows([],target)
    if cert:return dict(status='proved',certificate=cert,tested=tested)
    first=moves(target)
    for _,row,rem in first:
        cert=try_rows([row],rem)
        if cert:return dict(status='proved',certificate=cert,tested=tested)
    for _,row,rem in first:
        for _,r2,rem2 in moves(rem):
            cert=try_rows([row,r2],rem2)
            if cert:return dict(status='proved',certificate=cert,tested=tested)
            if tested>=budget:break
        if tested>=budget:break
    grid=('0','1','2','1/2') if s['domain']=='nonnegative' else ('0','1','-1','2','-2','1/2')
    for i,x in enumerate(itertools.product(grid,repeat=len(s['variables']))):
        if i>=budget:break
        c=dict(kind='point',point=list(x))
        if replay(s,c)=='refuted':return dict(status='counterexample',certificate=c,tested=tested,points=i+1)
    if budget>=32 and s['assumptions']:
        from polynomial_cone import search
        cert,pivots=search(assumptions(s),[h['relation'] for h in s['assumptions']],target,len(s['variables']),s['domain'],min(256,budget*2))
        if cert is not None and replay(s,cert)=='proved':return dict(status='proved',certificate=cert,tested=tested,cone_pivots=pivots)
    return dict(status='unknown',tested=tested,scope='bounded multiplier, feasible-point and simultaneous cone search; no completeness claim')

def main():
    import argparse
    from runtime import read_json
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('spec');p.add_argument('--budget',type=int,default=128);a=p.parse_args()
    print(json.dumps(solve(read_json(a.spec),a.budget),indent=2))
if __name__=='__main__':main()
