"""Install checked constraint and modular results; invent exact CRT obligations."""
import json
import finite_csp as fc
import modular_discovery as md
from discovery import check,frontier,record,fingerprint

def modular_split(g,focus,s):
    children=md.crt_children(s)
    if not children:return g
    target=g["nodes"][focus]["statement"];ps=[md.statement(t) for t in children]
    cert=dict(kind="coprime-divisibility")
    if not md.bridge(target,ps,cert):return g
    tag="modular-transfer-"+fingerprint(focus+"\n"+target)[:32]
    if tag in g["observations"]:return g
    ops=[];ids=[]
    for p in ps:
        i=next((k for k,n in sorted(g["nodes"].items()) if n["statement"]==p),None)
        if i is None:
            i="modular-node-"+fingerprint(p)[:24]
            ops.append(dict(op="claim",id=i,statement=p))
        elif g["nodes"][i]["status"]=="refuted":return g
        ids.append(i)
    old=next((k for k,e in g["edges"].items() if e["parent"]==focus and set(e["premises"])==set(ids) and e["rule"]!="rejected"),None)
    if old and g["edges"][old]["rule"]=="accepted":return g
    edge=old or tag
    if old is None:ops.append(dict(op="derive",id=edge,parent=focus,premises=ids,argument="Pairwise coprime prime-power divisors multiply to the original modulus."))
    ops.extend([dict(op="observe",id=tag,focus=focus,kind="transfer",detail=json.dumps(dict(edge=edge,certificate=cert),sort_keys=True)),dict(op="review_edge",id=edge,decision="accepted",evidence="Replayed coprime divisor bridge "+tag)])
    try:return record(g,"reformulate",focus,ops,trusted=True)
    except ValueError:return g

def auto_discharge(g,limit=3):
    check(g);count=0
    for focus in frontier(g):
        if count>=limit:break
        if focus not in frontier(g):continue
        text=g["nodes"][focus]["statement"]
        module=fc if text.startswith(fc.PREFIX) else md if text.startswith(md.PREFIX) else None
        if module is None:continue
        try:s=module.parse_statement(text)
        except (ValueError,TypeError):continue
        if module is md:
            h=modular_split(g,focus,s)
            if h!=g:g=h;count+=1;continue
        prefix="finite-csp-" if module is fc else "modular-residue-"
        if any(o["focus"]==focus and oid.startswith(prefix) for oid,o in g["observations"].items()):continue
        r=module.solve(s,budget=512 if module is fc else 8192);status=r["status"]
        detail=json.dumps(r,sort_keys=True,separators=(",",":"))
        if len(detail)>20000:continue
        oid=prefix+fingerprint(focus+"\n"+detail)[:32]
        kind={"proved":"proof_sketch","refuted":"counterexample","unknown":"experiment"}[status]
        ops=[dict(op="observe",id=oid,focus=focus,kind=kind,detail=detail)]
        if status!="unknown":
            if module.replay(s,r["certificate"])!=status:raise ArithmeticError("certificate replay")
            ops.append(dict(op="review_claim",id=focus,decision="established" if status=="proved" else "refuted",evidence="Exact certificate "+oid))
        g=record(g,"falsify" if status=="refuted" else "forward",focus,ops,trusted=True);count+=1
    return g
