"""Universal polynomial graph bounds with explicit theorem-basis certificates."""
import json
from fractions import Fraction as Q
import polynomial as p
import conditional_theorems as ct
import graph_consequences as gc
import graph_lemma as gl
import graph_nonlinear_basis as gb
from rational_cone import solve as conic_solve
from polynomial_cone import search
from runtime import strict_json

PREFIX='Universal polynomial graph invariant inequality: '

def normalize(s):
    if not isinstance(s,dict) or set(s)!={'min_n','properties','variables','terms'}:raise ValueError('graph polynomial shape')
    base=gl.validate(dict(min_n=s['min_n'],properties=s['properties'],coefficients={'n':1},constant=0))
    vs=s['variables']
    if not isinstance(vs,list) or any(v not in gl.FIELDS for v in vs):raise ValueError('graph invariant variables')
    q=p.normalize(dict(variables=vs,domain='nonnegative',relation='nonnegative',terms=s['terms']))
    return dict(min_n=base['min_n'],properties=base['properties'],variables=q['variables'],terms=q['terms'])

def statement(s):return PREFIX+json.dumps(normalize(s),sort_keys=True,separators=(',',':'))
def parse_statement(text):
    if not isinstance(text,str) or not text.startswith(PREFIX):raise ValueError('not nonlinear graph claim')
    s=normalize(strict_json(text[len(PREFIX):]))
    if statement(s)!=text:raise ValueError('noncanonical graph claim')
    return s

def rows(s):
    s=normalize(s);vs=s['variables'];b={}
    def insert(k,q):
        if any(v not in vs for e in q for v in e):return
        terms={}
        for e,c in q.items():
            f=tuple(e.count(v) for v in vs);terms[f]=terms.get(f,Q(0))+Q(c)
        b[k]={e:c for e,c in terms.items() if c}
    g=dict(min_n=s['min_n'],properties=s['properties'],coefficients={'n':1},constant=0)
    for k,row in gc.basis(g).items():
        q={():row[0]} if row[0] else {}
        q.update({(v,):c for v,c in zip(gl.FIELDS,row[1:]) if c})
        insert(k,q)
    for k,q in gb.basis(s['properties']).items():insert(k,q)
    return b

def conditional(s,ids):
    s=normalize(s);b=rows(s)
    if not isinstance(ids,list) or len(ids)>8 or any(not isinstance(i,str) or i not in b for i in ids) or len(set(ids))!=len(ids):raise ValueError('theorem row IDs')
    return ct.normalize(dict(variables=s['variables'],domain='nonnegative',assumptions=[dict(relation='nonnegative',terms=p.encode(b[i])) for i in ids],conclusion=s['terms']))

def replay(s,cert):
    try:
        if not isinstance(cert,dict) or set(cert)!={'kind','rows','conditional_certificate'} or cert['kind']!='nonlinear-graph-consequence':return None
        c=cert['conditional_certificate']
        if not isinstance(c,dict) or c.get('kind')!='conditional-identity':return None
        return 'proved' if ct.replay(conditional(s,cert['rows']),c)=='proved' else None
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError):return None

def solve(s,pivot_budget=256):
    s=normalize(s)
    if type(pivot_budget) is not int or not 1<=pivot_budget<=1024:raise ValueError('pivot limit')
    b=rows(s);n=len(s['variables']);target=p.terms(s['terms'],n)
    def report(ids,c):
        cert=dict(kind='nonlinear-graph-consequence',rows=ids,conditional_certificate=c)
        if replay(s,cert)!='proved':return None
        return dict(status='proved',certificate=cert)
    q=p.solve(dict(variables=s['variables'],domain='nonnegative',relation='nonnegative',terms=s['terms']),budget=1)
    if q['status']=='proved':
        return report([],dict(kind='conditional-identity',multipliers=[],residual=q['certificate']))
    ids=sorted(b,key=lambda i:(-len(set(b[i])&set(target)),len(set(b[i])-set(target)),i))
    # First try direct nonnegative combinations of all theorem rows.
    x,used=conic_solve([b[i] for i in ids],target,min(96,pivot_budget))
    if x is not None:
        chosen=[i for i,w in zip(ids,x) if w]
        if len(chosen)<=8:
            c=dict(kind='conditional-identity',multipliers=[dict(indices=[j],multiplier=[[[0]*n,str(x[ids.index(i)])]]) for j,i in enumerate(chosen)],residual=dict(kind='sos',squares=[],monomials=[]))
            r=report(chosen,c)
            if r:return dict(r,pivots=used)
    # Then try bounded polynomial products and multiples of applicable rows.
    # No counterexample to this relaxation is a counterexample graph.
    subsets=[ids[:8],ids[:4],ids[8:16]]
    for selected in subsets:
        if not selected or used>=pivot_budget:continue
        c,steps=search([b[i] for i in selected],['nonnegative']*len(selected),target,n,'nonnegative',min(96,pivot_budget-used))
        used+=steps
        if c:
            r=report(selected,c)
            if r:return dict(r,pivots=used)
    return dict(status='unknown',pivots=used,scope='bounded consequences of elementary graph inequalities; not a complete graph invariant characterization')

def main():
    import argparse
    from runtime import read_json
    q=argparse.ArgumentParser(description=__doc__);q.add_argument('spec');q.add_argument('--pivots',type=int,default=256);a=q.parse_args()
    print(json.dumps(solve(read_json(a.spec),a.pivots),indent=2))
if __name__=='__main__':main()
