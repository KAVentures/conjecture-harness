"""Compose typed affine implications through independently replayable certificates.
A bridge certifies conditional sufficiency, not truth of its premise claims.
"""
import json
from affine import normalize, parse_statement, prove, replay
from discovery import check, frontier, record, fingerprint


def inputs(goal, premises):
    g=normalize(goal)
    if not isinstance(premises,dict) or not 1<=len(premises)<=12:
        raise ValueError('expected 1..12 typed premises')
    ps={k:normalize(v) for k,v in premises.items()}
    if any(p['variables']!=g['variables'] for p in ps.values()):
        raise ValueError('variable lists must match exactly')
    return g,ps


def query(g,rows,conclusion):
    return dict(variables=g['variables'],assumptions=rows,conclusion=conclusion)


def replay_bridge(goal,premises,certificate):
    try:return _replay_bridge(goal,premises,certificate)
    except (ValueError,TypeError,KeyError,ZeroDivisionError):return False

def _replay_bridge(goal,premises,certificate):
    g,ps=inputs(goal,premises)
    if not isinstance(certificate,dict) or set(certificate)!={'steps','final'} or not isinstance(certificate['steps'],list) or len(certificate['steps'])>len(ps):return False
    rows=list(g['assumptions']);used=set()
    for step in certificate['steps']:
        if not isinstance(step,dict) or set(step)!={'premise','assumptions'}:return False
        i=step['premise']
        if not isinstance(i,str) or i not in ps or i in used:return False
        p=ps[i];cs=step['assumptions']
        if not isinstance(cs,list) or len(cs)!=len(p['assumptions']):return False
        if not all(replay(query(g,rows,a),c) for a,c in zip(p['assumptions'],cs)):return False
        if len(rows)>=12:return False
        rows.append(p['conclusion']);used.add(i)
    return replay(query(g,rows,g['conclusion']),certificate['final'])


def synthesize(goal,premises,pair_budget=1000,max_calls=48):
    g,ps=inputs(goal,premises)
    if type(max_calls) is not int or not 1<=max_calls<=100 or type(pair_budget) is not int or not 1<=pair_budget<=2000:raise ValueError('invalid bridge budget')
    rows=list(g['assumptions']);steps=[];remaining=dict(sorted(ps.items()));calls=0
    def attempt(conclusion):
        nonlocal calls
        if calls>=max_calls:return None
        calls+=1;r=prove(query(g,rows,conclusion),pair_budget)
        return r['certificate'] if r['status']=='proved' else None
    while calls<max_calls:
        final=attempt(g['conclusion'])
        if final is not None:
            cert=dict(steps=steps,final=final)
            if not replay_bridge(g,ps,cert):raise ArithmeticError('bridge certificate failed replay')
            return dict(status='proved',calls=calls,certificate=cert)
        if len(rows)>=12:break
        changed=False
        for i,p in list(remaining.items()):
            proofs=[]
            for a in p['assumptions']:
                c=attempt(a)
                if c is None:break
                proofs.append(c)
            if len(proofs)!=len(p['assumptions']):continue
            steps.append(dict(premise=i,assumptions=proofs));rows.append(p['conclusion']);del remaining[i];changed=True
            break # check the goal again before expanding further
        if not changed:break
    return dict(status='unknown',calls=calls,certificate=None)


def discharge(g,edge_id):
    check(g);e=g['edges'][edge_id]
    if e['rule']!='candidate' or e['parent'] not in frontier(g) or any(g['nodes'][i]['status']=='refuted' for i in e['premises']):raise ValueError('not a live candidate bridge')
    goal=parse_statement(g['nodes'][e['parent']]['statement']);ps={i:parse_statement(g['nodes'][i]['statement']) for i in e['premises']}
    report=synthesize(goal,ps);detail=json.dumps(dict(edge=edge_id,report=report),sort_keys=True)
    ident='bridge-'+fingerprint(detail)[:32]
    if ident in g['observations']:return g,report
    # The graph's observation size bound is smaller than the full certificate language.
    if len(detail)>20000:return g,dict(status='unknown',calls=report['calls'],certificate=None)
    ops=[dict(op='observe',id=ident,focus=e['parent'],kind='proof_sketch' if report['status']=='proved' else 'experiment',detail=detail)]
    if report['status']=='proved':
        if not replay_bridge(goal,ps,report['certificate']):raise ArithmeticError('bridge replay failed')
        ops.append(dict(op='review_edge',id=edge_id,decision='accepted',evidence='Exact affine bridge certificate in observation '+ident))
    return record(g,'forward',e['parent'],ops,trusted=True),report


def auto_discharge(g,limit=2):
    count=0
    tried=set()
    for i,o in g['observations'].items():
        if i.startswith('bridge-'):
            tried.add(json.loads(o['detail'])['edge'])
    for i,e in sorted(g['edges'].items()):
        if count>=limit:break
        if i in tried or e['rule']!='candidate' or e['parent'] not in frontier(g):continue
        try:
            goal=parse_statement(g['nodes'][e['parent']]['statement']);ps={p:parse_statement(g['nodes'][p]['statement']) for p in e['premises']};inputs(goal,ps)
        except (ValueError,TypeError):continue
        if any(g['nodes'][p]['status']=='refuted' for p in e['premises']):continue
        g,_=discharge(g,i);count+=1
    return g
