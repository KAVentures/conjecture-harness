"""Read-only mathematical replay independent of local review flags.
Unsupported evidence is unverified, never promoted by a recorded review.
"""
import argparse,json
from discovery import check,closure
from runtime import read_json,strict_json
import affine,polynomial,capacity,finite_power,graph_lemma
import graph_reduction,lemma_invention,recursive_invention,affine_bridge,theorem_transfer
from hypothesis import sum_bridge
import symbolic_discovery,proof_synthesis,representation_transfer,dynamics_discovery
import indexed_algebra,simplex_discovery,extremal_reduction,conditional_theorems,theorem_application
from equivalence import equivalent
from certificate_registry import TYPED,AUDIT_DIRECT,typed_replay


def direct(text,oid,o):
    r=strict_json(o['detail']);status=r.get('status');c=r.get('certificate')
    if oid.startswith(tuple(TYPED)):
        return typed_replay(text,oid,status,c)
    if oid.startswith('bundle-') and status=='proved':
        from proof_bundle import replay as replay_bundle
        if replay_bundle(c,text):return 'proved'
    if oid.startswith('aff-') and status=='proved' and affine.replay(affine.parse_statement(text),c):return 'proved'
    if oid.startswith(('poly-','shift-')):
        s=polynomial.parse_statement(text)
        if status=='proved' and c.get('kind') in ('sos','identity') and polynomial.replay(s,c):return 'proved'
        if status=='counterexample' and c.get('kind')=='point' and polynomial.replay(s,c):return 'refuted'
    if oid.startswith(('capacity-','graph-reduction-')):
        s=capacity.parse_statement(text)
        if status=='proved' and (graph_reduction.replay(s,c) if oid.startswith('graph-reduction-') else capacity.replay(s,c)):return 'proved'
        if status=='counterexample' and c.get('kind')=='packing' and capacity.replay_counterexample(s,c['words']):return 'refuted'
    if oid.startswith('finite-power-'):
        s=finite_power.parse_statement(text)
        if status=='proved' and finite_power.replay(s,c):return 'proved'
        if status=='counterexample' and len(r['witness'])>s['upper'] and finite_power.packing(s,r['witness']):return 'refuted'
    if oid.startswith('lab-') and status=='counterexample' and graph_lemma.statement(r['spec'])==text and graph_lemma.replay(r['spec'],r['witness'])['counterexample']:return 'refuted'
    if oid.startswith('invent-') and lemma_invention.replay(polynomial.parse_statement(text),r):return 'proved'
    if oid.startswith('recursive-') and status=='proved' and recursive_invention.replay(polynomial.parse_statement(text),r['tree']):return 'proved'
    return None


def bridge(g,i,e,observations):
    text=lambda j:g['nodes'][j]['statement']
    a=text(e['parent']);ps=e['premises']
    from matrix_permanent import prefix_bridge
    if len(ps)==1 and prefix_bridge(a,text(ps[0])):return 'typed Abel summation'
    # An additive identity is itself a certificate, without trusting its label.
    try:
        if sum_bridge(polynomial.parse_statement(a),[polynomial.parse_statement(text(j)) for j in ps]):return 'exact polynomial sum'
    except (ValueError,TypeError,KeyError):pass
    for oid,o in observations:
        try:
            if oid.startswith('modular-transfer-'):
                from modular_discovery import bridge as modular_bridge
                d=strict_json(o['detail'])
                if d['edge']==i and modular_bridge(a,[text(j) for j in ps],d['certificate']):return oid
            if oid.startswith('cover-transfer-'):
                from cover_transfer import replay as cover_replay
                d=strict_json(o['detail'])
                if d['edge']==i and cover_replay(a,[text(j) for j in ps],d['certificate']):return oid
            if oid.startswith('theorem-combination-'):
                from theorem_recombination import replay as combination_replay
                d=strict_json(o['detail'])
                if d['edge']==i and combination_replay(a,[text(j) for j in ps],d['certificate']):return oid
            if oid.startswith('application-'):
                d=strict_json(o['detail'])
                if d['edge']==i and theorem_application.replay(a,[text(j) for j in ps],d['certificate']):return oid
            if oid.startswith('transport-moment-'):
                from transport_moment_bridge import replay as transport_moment_replay
                d=strict_json(o['detail'])
                if d['edge']==i and transport_moment_replay(a,[text(j) for j in ps],d['certificate']):return oid
            if oid.startswith('tensor-combine-'):
                from tensor_recombination import replay as tensor_replay
                d=strict_json(o['detail'])
                if d['edge']==i and tensor_replay(a,[text(j) for j in ps],d['certificate']):return oid
            if oid.startswith('extremal-'):
                d=strict_json(o['detail'])
                if d['edge']==i and extremal_reduction.replay(simplex_discovery.parse_statement(a),[simplex_discovery.parse_statement(text(j)) for j in ps],d['certificate']):return oid
            if oid.startswith('representation-') and len(ps)==1:
                d=strict_json(o['detail'])
                if d['edge']==i and d['premise']==ps[0] and representation_transfer.replay(polynomial.parse_statement(a),polynomial.parse_statement(text(ps[0])),d['certificate']):return oid
            if oid.startswith('synthesis-'):
                d=strict_json(o['detail'])
                if d['edge']==i and d['premises']==ps and proof_synthesis.replay(polynomial.parse_statement(a),[polynomial.parse_statement(text(j)) for j in ps],d['certificate']):return oid
            if oid.startswith('bridge-'):
                d=strict_json(o['detail'])
                if d['edge']==i and affine_bridge.replay_bridge(affine.parse_statement(a),{j:affine.parse_statement(text(j)) for j in ps},d['report']['certificate']):return oid
            if oid.startswith('theorem-') and len(ps)==1:
                d=strict_json(o['detail'])
                if d['parent']==e['parent'] and d['premise']==ps[0] and theorem_transfer.replay(capacity.parse_statement(a),capacity.parse_statement(text(ps[0])),d['report']['certificate']):return oid
        except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,RecursionError):continue
    return None


def audit(g):
    check(g);proved={};refuted={};invalid=[];by_focus={}
    for oid,o in sorted(g['observations'].items()):
        by_focus.setdefault(o['focus'],[]).append((oid,o))
        if not oid.startswith(AUDIT_DIRECT) or o['kind'] not in ('proof_sketch','counterexample'):continue
        i=o['focus']
        try:r=direct(g['nodes'][i]['statement'],oid,o)
        except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError,RecursionError):r=None
        if r=='proved' and o['kind']=='proof_sketch':proved[i]=oid
        elif r=='refuted' and o['kind']=='counterexample':refuted[i]=oid
        else:invalid.append(oid)
    # Propagate only from independently replayed premises. Accepted status alone is insufficient.
    checked={}
    for i,e in sorted(g['edges'].items()):
        if e['rule']=='accepted':
            r=bridge(g,i,e,by_focus.get(e['parent'],[]))
            if r:checked[i]=r
    changed=True
    while changed:
        changed=False
        for i,e in sorted(g['edges'].items()):
            if i in checked and e['parent'] not in proved and all(j in proved for j in e['premises']):
                proved[e['parent']]=i;changed=True
        for i,n in sorted(g['nodes'].items()):
            if i not in proved:
                for j in list(proved):
                    if equivalent(n['statement'],g['nodes'][j]['statement']):proved[i]='equivalent:'+j;changed=True;break
            if i not in refuted:
                for j in list(refuted):
                    if equivalent(n['statement'],g['nodes'][j]['statement']):refuted[i]='equivalent:'+j;changed=True;break
    recorded=closure(g);recorded_refuted={i for i,n in g['nodes'].items() if n['status']=='refuted'}
    conflicts=sorted((set(proved)&set(refuted))|(set(proved)&recorded_refuted)|(set(refuted)&recorded))
    status='conflict' if conflicts else 'proved' if 'goal' in proved else 'refuted' if 'goal' in refuted else 'unverified'
    return dict(target_sha256=g['target_sha256'],status=status,proved=proved,refuted=refuted,checked_edges=checked,invalid_observations=invalid,conflicts=conflicts,unverified_recorded_claims=sorted(recorded-set(proved)),unverified_recorded_refutations=sorted(recorded_refuted-set(refuted)),scope='Supported exact Python certificates only; not a proof assistant, authenticity or novelty audit.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('state');p.add_argument('--require-verified',action='store_true');a=p.parse_args()
    r=audit(read_json(a.state,limit=32*1024*1024));print(json.dumps(r,indent=2,sort_keys=True))
    if a.require_verified and (r['status'] not in ('proved','refuted') or r['invalid_observations']):p.exit(1)
if __name__=='__main__':main()
