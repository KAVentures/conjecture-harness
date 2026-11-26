"""Canonical integer-tail implications, with discrete and eventual sign certificates."""
import json
from fractions import Fraction as Q
import polynomial as p
import integer_sign as ins
from runtime import strict_json
from discovery import check,frontier,record,fingerprint

PREFIX='Integer polynomial implication: '

def normalize(s):
    if not isinstance(s,dict) or set(s)!={'start','quantifier','assumptions','conclusion'} or type(s['start']) is not int or not 0<=s['start']<=10**12 or s['quantifier'] not in ('all','eventual'):raise ValueError('integer claim shape')
    if not isinstance(s['assumptions'],list) or len(s['assumptions'])>8:raise ValueError('hypothesis limit')
    a=[]
    for h in s['assumptions']:
        if not isinstance(h,dict) or set(h)!={'relation','terms'} or h['relation'] not in ('zero','nonnegative'):raise ValueError('hypothesis shape')
        a.append(dict(relation=h['relation'],terms=p.encode(p.terms(h['terms'],1))))
    return dict(start=s['start'],quantifier=s['quantifier'],assumptions=a,conclusion=p.encode(p.terms(s['conclusion'],1)))

def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))
def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('not integer claim')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical integer claim')
    return s

def inputs(s):
    s=normalize(s)
    def dense(ts):
        q=p.terms(ts,1)
        return [q.get((k,),Q(0)) for k in range(1+max((e[0] for e in q),default=0))]
    return [dense(h['terms']) for h in s['assumptions']]+[dense(s['conclusion'])],[h['relation'] for h in s['assumptions']],s['start']

def eventual(raw,relations,start):
    # Each nonzero polynomial has the sign of its leading coefficient
    # beyond its own strict Cauchy root bound. Zero polynomials stay zero.
    signs=[];bound=start
    for p0 in raw:
        q=ins.trim(p0)
        if not q:signs.append(0);continue
        signs.append(ins.sign(q[-1]))
        bound=max(bound,(Q(2)+max((abs(c/q[-1]) for c in q[:-1]),default=Q(0))).__ceil__())
    fails=signs[-1]<0 and all(s==0 if r=='zero' else s>=0 for r,s in zip(relations,signs))
    return dict(outcome='refuted' if fails else 'proved',threshold=str(bound),signs=signs)

def replay(s,cert):
    try:
        s=normalize(s);raw,relations,start=inputs(s)
        if s['quantifier']=='all':return ins.replay(raw,relations,start,cert)
        if not isinstance(cert,dict) or set(cert)!={'kind','classification'} or cert['kind']!='eventual-sign':return None
        r=eventual(raw,relations,start)
        return r['outcome'] if r==cert['classification'] else None
    except (ValueError,TypeError,KeyError,ArithmeticError):return None

def solve(s):
    s=normalize(s)
    try:
        raw,relations,start=inputs(s)
        if s['quantifier']=='all':r=ins.classify(raw,relations,start);kind='integer-sign'
        else:r=eventual(raw,relations,start);kind='eventual-sign'
    except ValueError:return dict(status='unknown')
    cert=dict(kind=kind,classification=r)
    if replay(s,cert)!=r['outcome']:raise ArithmeticError('integer replay failed')
    return dict(status=r['outcome'],certificate=cert)

def auto_discharge(g,limit=2):
    check(g);count=0
    for i in frontier(g):
        if count>=limit:break
        if i not in frontier(g):continue
        try:s=parse_statement(g['nodes'][i]['statement'])
        except (ValueError,TypeError):continue
        if any(o['focus']==i and oid.startswith('integer-sign-') for oid,o in g['observations'].items()):continue
        r=solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True)
        oid='integer-sign-'+fingerprint(i+'\n'+detail)[:32]
        kind={'proved':'proof_sketch','refuted':'counterexample','unknown':'experiment'}[status]
        ops=[dict(op='observe',id=oid,focus=i,kind=kind,detail=detail)]
        if status!='unknown':ops.append(dict(op='review_claim',id=i,decision='established' if status=='proved' else 'refuted',evidence='Exact discrete or eventual sign certificate '+oid))
        g=record(g,'falsify' if status=='refuted' else 'forward',i,ops,trusted=True);count+=1
    return g

def main():
    import argparse
    from runtime import read_json
    q=argparse.ArgumentParser(description=__doc__);q.add_argument('spec');a=q.parse_args()
    print(json.dumps(solve(read_json(a.spec)),indent=2))
if __name__=='__main__':main()
