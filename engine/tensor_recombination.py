"""Combine audited tensor lemmas and newly synthesized weighted squares."""
import json
import constrained_tensor_lab as ct
from affine import rational
from rational_cone import solve as cone

def source_in_context(s,text):
    if text.startswith(ct.PREFIX):
        q=ct.parse_statement(text)
    else:
        import tensor_sos_lab as sos
        raw=sos.parse_statement(text)
        q=dict(raw,nonnegative=[],centered={})
    if q['tensors']!=s['tensors'] or not set(q['nonnegative'])<=set(s['nonnegative']) or any(not set(v)<=set(s['centered'].get(k,[])) for k,v in q['centered'].items()):raise ValueError('source context not implied')
    return ct.normal(s,q['terms'])

def replay(goal,premises,cert):
    try:
        s=ct.parse_statement(goal)
        if not isinstance(cert,dict) or set(cert)!={'weights','atoms'} or not isinstance(cert['weights'],list) or len(cert['weights'])!=len(premises) or not 1<=len(premises)<=12 or len(set(premises))!=len(premises) or goal in premises or not isinstance(cert['atoms'],list) or len(cert['atoms'])>64 or len(json.dumps(cert))>15000:return False
        total={}
        for text,w in zip(premises,cert['weights']):
            w=rational(w)
            if w<=0:return False
            ct.add(total,source_in_context(s,text),w)
        for row in cert['atoms']:
            if not isinstance(row,list) or len(row)!=2:return False
            w=rational(row[0])
            if w<=0:return False
            ct.add(total,ct.expand(s,row[1]),w)
        return ct.clean(total)==ct.normal(s)
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,OverflowError,RecursionError):return False

def discover(goal,sources):
    s=ct.parse_statement(goal);texts=[];cols=[]
    for t in sources:
        if t==goal or t in texts:continue
        try:v=source_in_context(s,t)
        except (ValueError,TypeError):continue
        if v:texts.append(t);cols.append(v)
        if len(texts)>=12:break
    if not texts:return None
    a,extra=ct.pool(s)
    try:w,_=cone(cols+extra,ct.normal(s),pivot_budget=160)
    except ValueError:return None
    if w is None:return None
    ps=[t for t,v in zip(texts,w) if v]
    if not ps:return None
    c=dict(weights=[str(v) for v in w[:len(texts)] if v],atoms=[[str(v),x] for x,v in zip(a,w[len(texts):]) if v])
    return dict(premises=ps,certificate=c) if replay(goal,ps,c) else None

def auto_discharge(g,limit=1):
    from discovery import check,frontier,record,fingerprint
    from proof_audit import audit
    check(g);count=0
    candidates=[]
    for i in frontier(g):
        try:ct.parse_statement(g['nodes'][i]['statement']);candidates.append(i)
        except (ValueError,TypeError):continue
    if not candidates:return g
    report=audit(g)
    if report['conflicts']:return g
    source={}
    for i in sorted(report['proved']):
        text=g['nodes'][i]['statement']
        source.setdefault(text,i)
    for focus in candidates:
        if count>=limit:break
        if focus not in frontier(g):continue
        goal=g['nodes'][focus]['statement'];hit=discover(goal,list(source))
        if hit is None:continue
        ps=[source[t] for t in hit['premises']]
        tag='tensor-combine-'+fingerprint(focus+'\n'+'\n'.join(ps))[:32]
        if tag in g['observations'] or any(e['parent']==focus and set(e['premises'])==set(ps) and e['rule']!='rejected' for e in g['edges'].values()):continue
        detail=json.dumps(dict(edge=tag,certificate=hit['certificate']),sort_keys=True)
        ops=[dict(op='derive',id=tag,parent=focus,premises=ps,argument='Exact positive combination of audited tensor lemmas and nonnegative weighted tensor squares under a verified structural context inclusion.'),dict(op='observe',id=tag,focus=focus,kind='transfer',detail=detail),dict(op='review_edge',id=tag,decision='accepted',evidence='Exact tensor identity '+tag)]
        try:g=record(g,'recombine',focus,ops,trusted=True)
        except ValueError:continue
        count+=1
    return g
