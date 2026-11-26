"""Replay exact polynomial evidence and update only its bound claim."""
import json
from discovery import check,frontier,record,fingerprint
from polynomial import statement,parse_statement,solve,replay

def discharge(g,focus,s,budget=256):
    check(g)
    if g['nodes'][focus]['statement']!=statement(s) or focus not in frontier(g):raise ValueError('claim mismatch or not reachable')
    report=solve(s,budget);detail=json.dumps(report,sort_keys=True);i='poly-'+fingerprint(focus+'\n'+detail)[:32]
    if i in g['observations']:return g,report
    status=report['status'];ops=[dict(op='observe',id=i,focus=focus,kind={'proved':'proof_sketch','counterexample':'counterexample','unknown':'experiment'}[status],detail=detail)]
    if status!='unknown':
        if not replay(s,report['certificate']):raise ArithmeticError('certificate replay failed')
        ops.append(dict(op='review_claim',id=focus,decision='established' if status=='proved' else 'refuted',evidence='Exact polynomial certificate in observation '+i))
    return record(g,'falsify' if status=='counterexample' else 'forward',focus,ops,trusted=True),report

def auto_discharge(g,limit=2):
    count=0
    for focus in frontier(g):
        if count>=limit:break
        if focus not in frontier(g):continue
        try:s=parse_statement(g['nodes'][focus]['statement'])
        except (ValueError,TypeError):continue
        if any(o['focus']==focus and i.startswith('poly-') for i,o in g['observations'].items()):continue
        g,_=discharge(g,focus,s);count+=1
    return g
