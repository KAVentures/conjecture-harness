"""Bounded recursive SOS lemma search with explicit tree certificates."""
import json
import polynomial as p
from hypothesis import sum_bridge
from lemma_invention import candidates
from discovery import check, closure, frontier, fingerprint, record


def replay(s,tree,depth=0):
    """Validate every leaf and every additive bridge on its exact parent."""
    if depth>4 or not isinstance(tree,dict):return False
    try:
        s=p.normalize(s)
        if s['relation']!='nonnegative':return False
        if set(tree)=={'certificate'}:
            c=tree['certificate'];return isinstance(c,dict) and c.get('kind')=='sos' and p.replay(s,c)
        if set(tree)!={'parts','children'} or len(tree['parts'])!=2 or len(tree['children'])!=2:return False
        return sum_bridge(s,tree['parts']) and all(replay(a,t,depth+1) for a,t in zip(tree['parts'],tree['children']))
    except (ValueError,TypeError,KeyError,AttributeError,RecursionError):return False


def search(s,budget=384,max_depth=3,width=16):
    """Iterative deepening, shared candidate budget, bounded branch width.

    A residual counterexample prunes only that decomposition. Unknown is
    never a certificate. Each extracted square is already certified; recurse
    on the residual, with exact-state memoization and ancestor exclusion.
    """
    if any(type(v) is not int or not 1<=v<=m for v,m in ((budget,2048),(max_depth,4),(width,64))):raise ValueError('invalid search limits')
    s=p.normalize(s);tested=0;direct={};expanded=0
    def finish(status,tree=None):return dict(status=status,tested=tested,expanded=expanded,tree=tree)
    if s['relation']!='nonnegative' or len(s['variables'])<2:return finish('unknown')
    def visit(q,left,ancestors):
        nonlocal tested,expanded
        key=p.statement(q)
        if key in ancestors:return None
        if key not in direct:
            if len(direct)>=budget+1:return None
            direct[key]=p.solve(q,budget=1)
        r=direct[key]
        if r['status']=='proved':return {'certificate':r['certificate']}
        if r['status']=='counterexample' or not left or tested>=budget:return None
        expanded+=1;seen=set();local=0
        for a,b,c in candidates(q):
            if local>=width or tested>=budget:break
            tested+=1;local+=1
            ka,kb=p.statement(a),p.statement(b)
            if kb in ancestors or kb==key or ka==key or ka==kb or (ka,kb) in seen:continue
            seen.add((ka,kb))
            if not sum_bridge(q,[a,b]) or not p.replay(a,c):raise ArithmeticError('invalid extracted square')
            child=visit(b,left-1,ancestors|{key})
            if child is not None:return dict(parts=[a,b],children=[{'certificate':c},child])
        return None
    for depth in range(1,max_depth+1):
        tree=visit(s,depth,set())
        if tree is not None:
            if not replay(s,tree):raise ArithmeticError('recursive certificate failed replay')
            return finish('proved',tree)
        if tested>=budget:break
    return finish('unknown')


def auto_recursive(g,limit=1):
    """Install a recursively replayed tree atomically after shallow abstention."""
    check(g);count=0
    for i in frontier(g):
        if count>=limit:break
        if i not in frontier(g) or any(e['parent']==i for e in g['edges'].values()):continue
        try:s=p.parse_statement(g['nodes'][i]['statement'])
        except (ValueError,TypeError):continue
        if not any(k.startswith('invent-') and o['focus']==i for k,o in g['observations'].items()):continue
        if any(k.startswith('recursive-') and o['focus']==i for k,o in g['observations'].items()):continue
        count+=1;r=search(s);oid='recursive-'+fingerprint(i+'\n'+p.statement(s))[:24];detail=json.dumps(r,sort_keys=True)
        if len(detail)>20000:continue
        ops=[dict(op='observe',id=oid,focus=i,kind='proof_sketch' if r['status']=='proved' else 'experiment',detail=detail)]
        if r['status']=='proved':
            from equivalence import claim_key
            if not replay(s,r['tree']):raise ArithmeticError('recursive certificate failed replay')
            known=closure(g);by_text={n['statement']:j for j,n in g['nodes'].items()};built=set()
            def install(q,t,node,path):
                if node in known or node in built:return
                sig=claim_key(p.statement(q))
                if any(n['status']=='refuted' and claim_key(n['statement'])==sig for n in g['nodes'].values()):raise ValueError('conflicting reviewed refutation')
                if 'certificate' in t:
                    ops.append(dict(op='review_claim',id=node,decision='established',evidence='Replayed SOS leaf '+path+' in '+oid));built.add(node);return
                ids=[]
                for j,(a,child) in enumerate(zip(t['parts'],t['children'])):
                    text=p.statement(a);sub=path+str(j);k=by_text.get(text)
                    if k is None:
                        k=oid+'-'+sub;by_text[text]=k
                        ops.append(dict(op='claim',id=k,statement=text))
                    if k==node or k in ids:raise ValueError('duplicate or cyclic tree node')
                    install(a,child,k,sub);ids.append(k)
                edge=oid+'-e'+path
                ops.extend([dict(op='derive',id=edge,parent=node,premises=ids,argument='Exact recursive additive decomposition'),dict(op='review_edge',id=edge,decision='accepted',evidence='Replayed coefficient sum at '+path+' in '+oid)])
                built.add(node)
            try:install(s,r['tree'],i,'r')
            except ValueError:continue
        try:g=record(g,'backward',i,ops,trusted=True)
        except ValueError:continue
    return g
