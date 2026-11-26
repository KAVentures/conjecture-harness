"""Universal linear graph consequences with a small explicit theorem basis.

A certificate combines applicable graph inequalities by exact nonnegative
linear multipliers. Every row has a documented elementary justification.
"""
import itertools,re,json
from fractions import Fraction as Q
import affine,graph_lemma as gl

FIELDS=gl.FIELDS
SUFFIX='. Here n is order, m is size, alpha is independence number, omega is clique number, delta is minimum degree and Delta is maximum degree.'
PATTERN=r'For every finite simple undirected graph with n >= (\d+) and required properties \[([^\]]*)\], (.+) >= (-?\d+)'+re.escape(SUFFIX)

def parse_statement(text):
    if not isinstance(text,str) or len(text)>20000:raise ValueError('graph statement')
    m=re.fullmatch(PATTERN,text)
    if not m:raise ValueError('not universal linear graph claim')
    n,props,terms,k=m.groups();coefficients={}
    for term in terms.split(' + '):
        q=re.fullmatch(r'\((-?\d+)\)\*(n|m|alpha|omega|delta|Delta)',term)
        if not q or q[2] in coefficients:raise ValueError('graph coefficient')
        coefficients[q[2]]=int(q[1])
    s=gl.validate(dict(min_n=int(n),properties=[] if props=='none' else props.split(', '),coefficients=coefficients,constant=int(k)))
    if gl.statement(s)!=text:raise ValueError('noncanonical graph statement')
    return s

def row(c=0,**terms):return [c]+[terms.get(k,0) for k in FIELDS]

def basis(s):
    s=gl.validate(s);n=s['min_n'];props=s['properties']
    b={
        'order':row(-n,n=1),
        'edge-nonnegative':row(m=1),
        'independent-singleton':row(-1,alpha=1),
        'clique-singleton':row(-1,omega=1),
        'degree-nonnegative':row(delta=1),
        'degree-order':row(Delta=1,delta=-1),
        'degree-simple':row(-1,n=1,Delta=-1),
        'independence-order':row(n=1,alpha=-1),
        'clique-order':row(n=1,omega=-1),
        'clique-independent-intersection':row(1,n=1,alpha=-1,omega=-1),
        'independent-min-degree':row(n=1,alpha=-1,delta=-1),
        'clique-max-degree':row(1,Delta=1,omega=-1),
        'max-degree-edges':row(m=1,Delta=-1),
        'degree-extremes':row(m=2,delta=-1,Delta=-1),
        'edge-deletion-independent':row(alpha=1,m=1,n=-1),
        'clique-edges':row(1,m=1,omega=-1),
        'handshake-min':row(m=2,delta=-n),
    }
    if 'connected' in props:
        b['connected-spanning-tree']=row(1,m=1,n=-1)
        if n>=2:
            b['connected-min-degree']=row(-1,delta=1)
            b['connected-edge-clique']=row(-2,omega=1)
    if 'triangle_free' in props:b['triangle-free-clique']=row(2,omega=-1)
    return b

def affine_spec(s,ids):
    s=gl.validate(s);b=basis(s)
    if not isinstance(ids,list) or len(ids)>12 or len(set(ids))!=len(ids) or any(not isinstance(i,str) or i not in b for i in ids):raise ValueError('theorem row IDs')
    return dict(variables=list(FIELDS),assumptions=[b[i] for i in ids],conclusion=row(-s['constant'],**s['coefficients']))

def replay(s,cert):
    try:
        if not isinstance(cert,dict) or set(cert)!={'kind','rows','linear_certificate'} or cert['kind']!='linear-graph-consequence':return None
        return 'proved' if affine.replay(affine_spec(s,cert['rows']),cert['linear_certificate']) else None
    except (ValueError,TypeError,KeyError,ArithmeticError,AttributeError):return None

def solve(s,budget=128):
    s=gl.validate(s)
    if type(budget) is not int or not 1<=budget<=512:raise ValueError('search budget')
    b=basis(s);goal=set(s['coefficients']);tested=0
    # Prefer rows supported on the goal variables, then expanding
    # neighborhoods. Exact elimination verifies every chosen combination.
    def score(i):
        support={k for k,v in zip(FIELDS,b[i][1:]) if v}
        return (len(support-goal),-len(support&goal),i)
    ids=sorted(b,key=score);candidates=[]
    candidates.extend([ids[:12],ids[:8],ids[:4]])
    candidates.extend([[i] for i in ids])
    candidates.extend([list(q) for q in itertools.combinations(ids[:10],2)])
    candidates.extend([list(q) for q in itertools.combinations(ids[:8],3)])
    seen=set()
    for chosen in candidates:
        key=tuple(sorted(chosen))
        if key in seen:continue
        if tested>=budget:break
        seen.add(key);tested+=1
        r=affine.prove(affine_spec(s,chosen),max_pairs=2000)
        if r['status']!='proved':continue
        cert=dict(kind='linear-graph-consequence',rows=chosen,linear_certificate=r['certificate'])
        if replay(s,cert)!='proved':raise ArithmeticError('graph consequence replay failed')
        return dict(status='proved',certificate=cert,tested=tested)
    return dict(status='unknown',tested=tested,scope='elementary graph theorem basis and bounded rational consequence search; no refutation from failure')

def main():
    import argparse
    from runtime import read_json
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('spec');p.add_argument('--budget',type=int,default=128);a=p.parse_args()
    print(json.dumps(solve(read_json(a.spec),a.budget),indent=2))
if __name__=='__main__':main()
