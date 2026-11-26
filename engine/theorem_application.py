"""Discover explicit applications of conditional theorems.

The source theorem is always a proof premise. A source from literature is not
established just because it has a citation. Substituted assumptions are
separate obligations in the target context; equality needs both signs.
"""
import json
from fractions import Fraction as Q
import polynomial as p
import conditional_theorems as ct
import representation_transfer as rt
from hypothesis import coefficients
from discovery import check,frontier,closure,record,fingerprint

def target(text):
    try:
        s=ct.parse_statement(text);return s,ct.conclusion(s),True
    except ValueError:
        s=p.parse_statement(text)
        if s['relation']!='nonnegative':raise ValueError('target relation')
        return dict(variables=s['variables'],domain=s['domain'],assumptions=[],conclusion=s['terms']),s,False

def obligations(goal_text,source_text,certificate):
    g,gp,conditional=target(goal_text);s=ct.parse_statement(source_text);sp=ct.conclusion(s)
    if not rt.replay(gp,sp,certificate):raise ValueError('conclusion map or source domain mismatch')
    n=len(g['variables']);images=[p.terms(a,n) for a in certificate['images']]
    out=[source_text]
    for h in s['assumptions']:
        hp=ct.poly(s['variables'],s['domain'],h['terms'],h['relation'])
        q=rt.compose(hp,images,n)
        for sign in ([1,-1] if h['relation']=='zero' else [1]):
            raw=p.encode({e:sign*v for e,v in q.items()})
            if conditional:
                t=ct.statement(dict(g,conclusion=raw))
            else:
                t=p.statement(ct.poly(g['variables'],g['domain'],raw))
            if t not in out:out.append(t)
    return out

def replay(goal_text,premise_texts,cert):
    try:
        if not isinstance(cert,dict) or set(cert)!={'source','map'}:return False
        expected=obligations(goal_text,cert['source'],cert['map'])
        return isinstance(premise_texts,list) and len(premise_texts)==len(expected) and set(premise_texts)==set(expected) and goal_text not in expected
    except (ValueError,TypeError,KeyError,ArithmeticError,AttributeError):return False

def obligation_status(text):
    """Bounded exact screening; these results never establish graph nodes."""
    try:
        if text.startswith(ct.PREFIX):
            s=ct.parse_statement(text);r=ct.solve(s,budget=8)
            status=r['status']
            if status in ('proved','counterexample'):
                expected='proved' if status=='proved' else 'refuted'
                if ct.replay(s,r['certificate'])==expected:return expected
        else:
            s=p.parse_statement(text);r=p.solve(s,budget=24)
            if r['status'] in ('proved','counterexample') and p.replay(s,r['certificate']):
                return 'proved' if r['status']=='proved' else 'refuted'
    except (ValueError,TypeError,KeyError,ArithmeticError):pass
    return 'unknown'

def propose(goal_text,source_text,budget=128,known_refuted=()):
    g,gp,_=target(goal_text);s=ct.parse_statement(source_text)
    best=None;best_score=None;screened={}
    known_refuted=set(known_refuted)
    for hit in rt.mappings(gp,ct.conclusion(s),budget,limit=12):
        cert=dict(source=source_text,map=hit['certificate'])
        try:ps=obligations(goal_text,source_text,cert['map'])
        except ValueError:continue
        if not replay(goal_text,ps,cert) or any(t in known_refuted for t in ps):continue
        states=[]
        for t in ps[1:]:
            if t not in screened:screened[t]=obligation_status(t)
            states.append(screened[t])
            if states[-1]=='refuted':break
        if 'refuted' in states:continue
        # Fewer unresolved hypotheses, then fewer obligations. Stop when every
        # instantiated assumption has a replayable certificate. Source theorem
        # remains an independent obligation even if all its assumptions pass.
        score=(states.count('unknown'),len(ps))
        if best_score is None or score<best_score:
            best=dict(premises=ps,certificate=cert,tested=hit['tested'])
            best_score=score
        if score[0]==0:return best
    return best

def insert(g,focus,source_text,application,provenance=None):
    check(g);goal=g['nodes'][focus]['statement'];ps=application['premises'];cert=application['certificate']
    if focus not in frontier(g) or not replay(goal,ps,cert) or cert['source']!=source_text:raise ValueError('application mismatch')
    if provenance is not None:
        if not isinstance(provenance,dict) or set(provenance)!={'source','locator'} or any(not isinstance(v,str) or not v.strip() or len(v)>1000 for v in provenance.values()):raise ValueError('source metadata')
    tag='application-'+fingerprint(focus+'\n'+json.dumps(cert,sort_keys=True))[:32]
    if tag in g['observations']:return g
    ops=[];ids=[]
    for text in ps:
        i=next((k for k,v in sorted(g['nodes'].items()) if v['statement']==text),None)
        if i is None:
            i='application-node-'+fingerprint(text)[:24]
            ops.append(dict(op='claim',id=i,statement=text))
        elif g['nodes'][i]['status']=='refuted':return g
        ids.append(i)
    old=next((i for i,e in sorted(g['edges'].items()) if e['parent']==focus and set(e['premises'])==set(ids) and e['rule']!='rejected'),None)
    if old and g['edges'][old]['rule']=='accepted':return g
    edge=old or tag
    if old is None:ops.append(dict(op='derive',id=edge,parent=focus,premises=ids,argument='Apply conditional theorem by exact substitution; prove source and every substituted hypothesis in target context.'))
    detail=json.dumps(dict(edge=edge,certificate=cert,provenance=provenance),sort_keys=True)
    if len(detail)>20000:return g
    ops.extend([dict(op='observe',id=tag,focus=focus,kind='transfer',detail=detail),dict(op='review_edge',id=edge,decision='accepted',evidence='Exact conclusion and hypothesis substitution '+tag)])
    return record(g,'reformulate',focus,ops,trusted=True)

def auto_discharge(g,limit=2):
    check(g);count=0;attempts=0
    pool=[]
    known=closure(g)
    for i in sorted(g['nodes'],key=lambda i:(i not in known,i)):
        node=g['nodes'][i]
        if node['status']=='refuted':continue
        try:ct.parse_statement(node['statement'])
        except (ValueError,TypeError):continue
        pool.append((i,node['statement']))
        if len(pool)>=8:break
    for focus in frontier(g):
        if count>=limit or attempts>=3:break
        if focus not in frontier(g):continue
        goal=g['nodes'][focus]['statement']
        try:target(goal)
        except (ValueError,TypeError):continue
        attempts+=1
        for i,source in pool:
            if i==focus:continue
            try:
                hit=propose(goal,source,64,known_refuted=[n['statement'] for n in g['nodes'].values() if n['status']=='refuted'])
                if hit is None:continue
                h=insert(g,focus,source,hit)
            except ValueError:continue # cycle, size limit or unsupported map
            if h!=g:g=h;count+=1;break
    return g

def main():
    import argparse
    from pathlib import Path
    from discovery import save
    from runtime import read_json
    from harness import coordinator_lock
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('state');p.add_argument('source');p.add_argument('--focus',default='goal');p.add_argument('--budget',type=int,default=128);a=p.parse_args()
    path=Path(a.state).resolve();log=path.with_name(path.name+'.runs');log.mkdir(exist_ok=True)
    raw=read_json(a.source)
    if not isinstance(raw,dict) or set(raw)!={'theorem','source','locator'}:raise ValueError('source record shape')
    source=ct.statement(raw['theorem'])
    with coordinator_lock(log):
        g=check(read_json(path,limit=32*1024*1024));hit=propose(g['nodes'][a.focus]['statement'],source,a.budget,known_refuted=[n['statement'] for n in g['nodes'].values() if n['status']=='refuted'])
        if hit is None:print(json.dumps(dict(status='unknown')));return
        h=insert(g,a.focus,source,hit,dict(source=raw['source'],locator=raw['locator']))
        if h!=g:save(path,h)
        print(json.dumps(dict(status='application-proposed' if h!=g else 'unchanged',premises=hit['premises']),indent=2))
if __name__=='__main__':main()
