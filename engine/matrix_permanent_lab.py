"""Connect exact matrix discovery and a sound sufficient-condition bridge to the AND/OR graph."""
import json
from discovery import check,frontier,record,fingerprint
from matrix_permanent import parse_statement,statement,solve,replay,prefix_bridge

ARGUMENT='Abel summation: normalized chord gap/t = sum c_k(1-t^(k-1)). Divide each weight by 2-2^(2-k); ratios are positive and nonincreasing in k for 0<t<=1/2. Nonnegative weighted prefixes imply the gap is nonnegative. At t=0 equality. See MATRIX_DISCOVERY.md.'

def auto_discharge(g,limit=2):
    check(g);count=0
    for focus in frontier(g):
        if count>=limit:break
        if focus not in frontier(g):continue
        try:s=parse_statement(g['nodes'][focus]['statement'])
        except (ValueError,TypeError):continue
        if any(o['focus']==focus and i.startswith('matrix-') for i,o in g['observations'].items()):continue
        report=solve(s);detail=json.dumps(report,sort_keys=True);oid='matrix-'+fingerprint(focus+'\n'+detail)[:32]
        status=report['status'];ops=[dict(op='observe',id=oid,focus=focus,kind={'proved':'proof_sketch','counterexample':'counterexample','unknown':'experiment'}[status],detail=detail)]
        if status!='unknown':
            expected='proved' if status=='proved' else 'refuted'
            if replay(s,report['certificate'])!=expected:raise ArithmeticError('matrix certificate replay failed')
            ops.append(dict(op='review_claim',id=focus,decision='established' if expected=='proved' else 'refuted',evidence='Exact matrix evidence '+oid))
        elif s['kind']=='lih-wang':
            premise=statement(dict(s,kind='signed-prefix'))
            pid=next((i for i,n in g['nodes'].items() if n['statement']==premise),None)
            if pid is None:
                pid='matrix-prefix-'+fingerprint(premise)[:24]
                ops.append(dict(op='claim',id=pid,statement=premise))
            if pid!=focus and prefix_bridge(statement(s),premise) and not any(e['parent']==focus and e['premises']==[pid] for e in g['edges'].values()):
                # Avoid cycles with a pre-existing claim; review the new bridge only if graph accepts it.
                eid='matrix-bridge-'+fingerprint(focus+'\n'+pid)[:24]
                extra=[dict(op='derive',id=eid,parent=focus,premises=[pid],argument=ARGUMENT),dict(op='review_edge',id=eid,decision='accepted',evidence='Typed Abel summation rule; MATRIX_DISCOVERY.md')]
                try:
                    g=record(g,'backward',focus,ops+extra,trusted=True);count+=1;continue
                except ValueError:
                    ops=[o for o in ops if o['op']!='claim']
        g=record(g,'falsify' if status=='counterexample' else 'forward',focus,ops,trusted=True);count+=1
    return g
