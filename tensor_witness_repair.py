"""Exact witness-guided repair of failed constrained tensor inequalities.

Propose a corrected lemma and compensating residual, preserving the target
identity. A repaired lemma is not a theorem until separately discharged.
"""
import json
from fractions import Fraction as Q
import constrained_tensor_lab as ct
import tensor_recombination as tc
from runtime import strict_json

def spec_from(s,nf):
    raw=[]
    for (power,fs),v in sorted(nf.items()):
        if v:raw.append(dict(coefficient=str(v),n_power=power,factors=[[name,list(ix)] for name,ix in fs]))
    return ct.normalize(dict(ct.context(s),terms=raw))

def repair(goal,failed,witness):
    s=ct.parse_statement(goal);f=ct.parse_statement(failed)
    if ct.context(s)!=ct.context(f) or ct.replay(f,witness)!='refuted':return []
    bad=ct.point_value(f,witness);target=ct.normal(s);F=ct.normal(f);out=[]
    if ct.point_value(s,witness)<0:return []
    # Invent a positive correction from the target's weighted square pool.
    # Require the correction to be nonzero at the actual failed witness.
    atoms,cols=ct.pool(s)
    for atom,col in zip(atoms,cols):
        try:
            slack=spec_from(s,col);v=ct.point_value(slack,witness)
            if v<=0:continue
            shift=-bad/v;A=dict(F);ct.add(A,col,shift);A=ct.clean(A)
            B=dict(target);ct.add(B,A,-1);B=ct.clean(B)
            if not A or not B:continue
            a,b=spec_from(s,A),spec_from(s,B);texts=[ct.statement(a),ct.statement(b)]
            if len(set(texts+[goal,failed]))!=4 or ct.point_value(a,witness)<0 or ct.point_value(b,witness)<0:continue
            cert=dict(weights=['1','1'],atoms=[])
            if not tc.replay(goal,texts,cert):continue
            # Reject candidates with a second exact counterexample. Survival
            # is merely a search filter, not evidence of universal truth.
            if ct.probe(a) is not None or ct.probe(b) is not None:continue
            if texts not in [r['premises'] for r in out]:out.append(dict(premises=texts,certificate=cert,shift=str(shift),correction=atom))
            if len(out)>=3:break
        except (ValueError,TypeError,ArithmeticError,OverflowError):continue
    return out

def auto_discharge(g,limit=1):
    from discovery import check,frontier,record,fingerprint
    from proof_audit import audit
    check(g);targets=[]
    for i in frontier(g):
        try:ct.parse_statement(g['nodes'][i]['statement']);targets.append(i)
        except (ValueError,TypeError):continue
    if not targets:return g
    report=audit(g)
    if report['conflicts']:return g
    count=0
    for focus in targets:
        if count>=limit:break
        if focus not in frontier(g):continue
        goal=g['nodes'][focus]['statement']
        for e in list(g['edges'].values()):
            if e['parent']!=focus or e['rule']=='rejected':continue
            for i in e['premises']:
                oid=report['refuted'].get(i)
                if oid not in g['observations'] or not oid.startswith('constrained-tensor-'):continue
                try:w=strict_json(g['observations'][oid]['detail'])['certificate'];hits=repair(goal,g['nodes'][i]['statement'],w)
                except (ValueError,TypeError,KeyError,ArithmeticError):continue
                for hit in hits:
                    tag='tensor-combine-repair-'+fingerprint(focus+'\n'+oid+'\n'+'\n'.join(hit['premises']))[:24]
                    if tag in g['observations']:continue
                    ops=[];ids=[];bad=False
                    for text in hit['premises']:
                        pid=next((k for k,n in sorted(g['nodes'].items()) if n['statement']==text),None)
                        if pid==focus or pid in report['refuted'] or (pid and g['nodes'][pid]['status']=='refuted'):bad=True;break
                        if pid is None:
                            pid='tensor-repair-node-'+fingerprint(text)[:24];ops.append(dict(op='claim',id=pid,statement=text))
                        ids.append(pid)
                    if bad or any(x['parent']==focus and set(x['premises'])==set(ids) and x['rule']!='rejected' for x in g['edges'].values()):continue
                    ops.extend([dict(op='derive',id=tag,parent=focus,premises=ids,argument='Witness-guided correction plus compensating residual; exact tensor sum, both premises still require proof.'),dict(op='observe',id=tag,focus=focus,kind='transfer',detail=json.dumps(dict(edge=tag,certificate=hit['certificate'],failed=i,witness=oid,shift=hit['shift']),sort_keys=True)),dict(op='review_edge',id=tag,decision='accepted',evidence='Exact cancellation identity '+tag)])
                    try:g=record(g,'refine',focus,ops,trusted=True)
                    except ValueError:continue
                    count+=1;break
                if count>=limit:break
            if count>=limit:break
    return g
