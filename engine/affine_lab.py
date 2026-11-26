"""Apply replayed affine proofs to exactly bound reachable claims."""
import json
from discovery import check,frontier,record,fingerprint
from affine import statement,parse_statement,prove,replay


def discharge(g,focus,spec,max_pairs=20000):
    check(g)
    if g['nodes'][focus]['statement']!=statement(spec):raise ValueError('claim/spec mismatch')
    if focus not in frontier(g):raise ValueError('claim is not an open reachable obligation')
    report=prove(spec,max_pairs)
    detail=json.dumps(report,sort_keys=True);ident='aff-'+fingerprint(focus+'\n'+detail)[:32]
    if ident in g['observations']:return g,report
    ops=[dict(op='observe',id=ident,focus=focus,kind='proof_sketch' if report['status']=='proved' else 'experiment',detail=detail)]
    if report['status']=='proved':
        if not replay(spec,report['certificate']):raise ArithmeticError('certificate replay failed')
        ops.append(dict(op='review_claim',id=focus,decision='established',evidence='Exact rational affine certificate in observation '+ident))
    return record(g,'forward',focus,ops,trusted=True),report


def auto_discharge(g,limit=2):
    """Only canonical, target-reachable obligations; at most two bounded searches per cycle."""
    attempted=0
    for focus in frontier(g):
        if attempted>=limit:break
        if focus not in frontier(g):continue
        try:spec=parse_statement(g['nodes'][focus]['statement'])
        except (ValueError,TypeError):continue
        if any(o['focus']==focus and i.startswith('aff-') for i,o in g['observations'].items()):continue
        g,_=discharge(g,focus,spec,max_pairs=2000);attempted+=1
    return g
