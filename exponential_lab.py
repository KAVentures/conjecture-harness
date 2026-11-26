"""Graph adapter for exact exponential-polynomial sequence signs."""
import json
from fractions import Fraction as Q
import exponential_sign as es
from affine import rational
from runtime import strict_json
from discovery import check,frontier,record,fingerprint

PREFIX='Exponential polynomial sequence inequality: '

def normalize(s):
    if not isinstance(s,dict) or set(s)!={'start','quantifier','terms'} or type(s['start']) is not int or not 1<=s['start']<=es.MAX_N or s['quantifier'] not in ('all','eventual'):raise ValueError('sequence scope')
    rows=s['terms']
    if not isinstance(rows,list) or len(rows)>16 or any(not isinstance(row,list) or len(row)!=3 for row in rows):raise ValueError('sequence term shape')
    ts=es.canonical([(rational(b),k,rational(c)) for b,k,c in rows])
    out=[[str(b),k,str(c)] for (b,k),c in sorted(ts.items())]
    if any(len(x)>80 for b,k,c in out for x in (b,c)):raise ValueError('coefficient limit')
    return dict(start=s['start'],quantifier=s['quantifier'],terms=out)

def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))
def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('not exponential sequence')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical sequence')
    return s

def inputs(s):
    s=normalize(s);return [(Q(b),k,Q(c)) for b,k,c in s['terms']],s['start'],s['quantifier']

def replay(s,cert):
    try:return es.replay(*inputs(s),cert)
    except (ValueError,TypeError,KeyError,ArithmeticError):return None

def solve(s):
    cert=es.classify(*inputs(s));status=cert['outcome']
    if status!='unknown' and replay(s,cert)!=status:raise ArithmeticError('sequence replay failed')
    return dict(status=status,certificate=cert)

def auto_discharge(g,limit=2):
    check(g);count=0
    for i in frontier(g):
        if count>=limit:break
        if i not in frontier(g):continue
        try:s=parse_statement(g['nodes'][i]['statement'])
        except (ValueError,TypeError):continue
        if any(o['focus']==i and oid.startswith('exponential-sign-') for oid,o in g['observations'].items()):continue
        r=solve(s);status=r['status'];detail=json.dumps(r,sort_keys=True)
        oid='exponential-sign-'+fingerprint(i+'\n'+detail)[:32]
        kind={'proved':'proof_sketch','refuted':'counterexample','unknown':'experiment'}[status]
        ops=[dict(op='observe',id=oid,focus=i,kind=kind,detail=detail)]
        if status!='unknown':ops.append(dict(op='review_claim',id=i,decision='established' if status=='proved' else 'refuted',evidence='Exact exponential dominance certificate '+oid))
        g=record(g,'falsify' if status=='refuted' else 'forward',i,ops,trusted=True);count+=1
    return g

def main():
    import argparse
    from runtime import read_json
    q=argparse.ArgumentParser(description=__doc__);q.add_argument('spec');a=q.parse_args()
    print(json.dumps(solve(read_json(a.spec)),indent=2))
if __name__=='__main__':main()
