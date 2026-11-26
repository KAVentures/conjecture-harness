"""Exact extremal face reduction for simplex inequalities.

Along a line exchanging mass between coordinates i,j, concavity implies the
minimum is attained at one of its endpoints. This converts the original
inequality to two smaller-dimensional face claims and one curvature claim.
"""
import itertools,json
from fractions import Fraction as Q
import simplex_discovery as s
from symbolic_discovery import terms,encode,add
from discovery import check,frontier,record,fingerprint

def derivative(p,i):
    out={}
    for e,c in p.items():
        if e[i]:
            a=list(e);a[i]-=1;out[tuple(a)]=c*e[i]
    return out

def obligations(goal,i,j):
    g=s.normalize(goal);n=len(g['variables'])
    if n<3 or type(i) is not int or type(j) is not int or not 0<=i<j<n:raise ValueError('face reduction indices')
    p=terms(g['terms'],n,6)
    def face(k):
        q={e[:k]+e[k+1:]:c for e,c in p.items() if not e[k]}
        return s.normalize(dict(variables=g['variables'][:k]+g['variables'][k+1:],terms=encode(q)))
    d=add(derivative(p,i),derivative(p,j),Q(-1))
    dd=add(derivative(d,j),derivative(d,i),Q(-1)) # negative exchange curvature
    return [s.normalize(dict(variables=g['variables'],terms=encode(dd))),face(i),face(j)]

def replay(goal,premises,cert):
    try:
        if not isinstance(cert,dict) or set(cert)!={'pair'} or not isinstance(cert['pair'],list) or len(cert['pair'])!=2:return False
        expected={s.statement(p) for p in obligations(goal,*cert['pair'])}
        return isinstance(premises,list) and len(premises)==len(expected) and {s.statement(p) for p in premises}==expected
    except (ValueError,TypeError,KeyError,ArithmeticError):return False

def auto_discharge(g,limit=2):
    check(g);count=0;attempts=0
    for focus in frontier(g):
        if count>=limit or attempts>=4:break
        if focus not in frontier(g):continue
        try:goal=s.parse_statement(g['nodes'][focus]['statement'])
        except (ValueError,TypeError):continue
        n=len(goal['variables'])
        if n<3:continue
        attempts+=1
        for i,j in itertools.combinations(range(n),2):
            tag='extremal-'+fingerprint(focus+'\n'+str(i)+','+str(j))[:32]
            if tag in g['observations']:continue
            try:parts=obligations(goal,i,j)
            except ValueError:continue
            # A verified curvature premise is necessary before investing in faces.
            curvature=s.solve(parts[0],depth=1)
            if curvature['status']!='proved':continue
            ids=[];ops=[];bad=False;specs={}
            for part in parts:
                text=s.statement(part)
                pid=next((k for k,v in sorted(g['nodes'].items()) if v['statement']==text),None)
                if pid==focus or (pid and g['nodes'][pid]['status']=='refuted'):bad=True;break
                if pid is None:
                    pid='extremal-node-'+fingerprint(text)[:24]
                    if not any(o['id']==pid for o in ops):ops.append(dict(op='claim',id=pid,statement=text))
                if pid not in ids:ids.append(pid)
                specs[pid]=part
            if bad or any(e['parent']==focus and set(e['premises'])==set(ids) and e['rule']!='rejected' for e in g['edges'].values()):continue
            cert=dict(pair=[i,j])
            if not replay(goal,[specs[pid] for pid in ids],cert):raise ArithmeticError('face bridge replay failed')
            ops.extend([dict(op='derive',id=tag,parent=focus,premises=ids,argument='For fixed other coordinates and fixed sum of the pair, nonpositive second derivative gives concavity. Every value is at least the minimum at the two endpoint faces.'),dict(op='observe',id=tag,focus=focus,kind='transfer',detail=json.dumps(dict(edge=tag,certificate=cert),sort_keys=True)),dict(op='review_edge',id=tag,decision='accepted',evidence='Exact exchange-curvature and face-restriction identities '+tag)])
            try:g=record(g,'backward',focus,ops,trusted=True)
            except ValueError:continue
            count+=1;break
    return g
