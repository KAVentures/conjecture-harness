"""Checked graph surgery and finite-cover theorem transfer.

Each implication preserves the frozen target. A source must independently be
proved. No rule asserts a universal graph theorem from finite evidence.
"""
import json
import combinatorial_cover as cc
from discovery import check, frontier, record, fingerprint

def suppress(s,v):
    s=cc.normalize(s)
    if s["kind"]!="paths" or not cc.integer(v,0,s["n"]-1) or s["n"]<2:
        raise ValueError("not a suppressible vertex")
    incident=[e for e in s["edges"] if v in e]
    if len(incident)!=2 or (s["endpoints"] is not None and s["endpoints"][v]!=0):
        raise ValueError("degree or endpoint condition")
    a,b=sorted(next(x for x in e if x!=v) for e in incident)
    if [a,b] in s["edges"]:raise ValueError("replacement edge already exists")
    remap=lambda x:x-int(x>v)
    es=[[remap(x) for x in e] for e in s["edges"] if v not in e]
    es.append([remap(a),remap(b)])
    endpoints=None if s["endpoints"] is None else s["endpoints"][:v]+s["endpoints"][v+1:]
    return cc.normalize(dict(s,n=s["n"]-1,edges=es,endpoints=endpoints))

def replay(goal,premises,cert):
    try:
        g=cc.parse_statement(goal)
        if not isinstance(premises,list) or len(premises)!=1 or premises[0]==goal:return False
        p=cc.parse_statement(premises[0])
        if not isinstance(cert,dict):return False
        if set(cert)=={"kind","vertex"} and cert["kind"]=="suppress":
            return suppress(g,cert["vertex"])==p
        if set(cert)=={"kind"} and cert["kind"]=="monotone":
            if g["kind"]!=p["kind"] or p["max_pieces"]>g["max_pieces"]:return False
            if g["kind"]=="paths":
                return (g["n"]==p["n"] and g["edges"]==p["edges"] and
                        (g["endpoints"] is None or g["endpoints"]==p["endpoints"]))
            return (g["items"]==p["items"] and g["resources"]==p["resources"] and
                    {(tuple(a),tuple(b)) for a,b in p["rows"]}<={(tuple(a),tuple(b)) for a,b in g["rows"]})
        return False
    except (ValueError,TypeError,KeyError,AttributeError):return False

def insert(g,focus,premise,cert):
    check(g);goal=g["nodes"][focus]["statement"]
    if focus not in frontier(g) or not replay(goal,[premise],cert):return g
    i=next((k for k,n in sorted(g["nodes"].items()) if n["statement"]==premise),None)
    if i is not None and g["nodes"][i]["status"]=="refuted":return g
    tag="cover-transfer-"+fingerprint(focus+"\n"+premise+"\n"+json.dumps(cert,sort_keys=True))[:32]
    if tag in g["observations"]:return g
    ops=[]
    if i is None:
        i="cover-node-"+fingerprint(premise)[:24]
        ops.append(dict(op="claim",id=i,statement=premise))
    old=next((k for k,e in g["edges"].items() if e["parent"]==focus and e["premises"]==[i] and e["rule"]!="rejected"),None)
    if old and g["edges"][old]["rule"]=="accepted":return g
    edge=old or tag
    if old is None:
        ops.append(dict(op="derive",id=edge,parent=focus,premises=[i],argument="Verified finite cover implication: "+cert["kind"]))
    detail=json.dumps(dict(edge=edge,certificate=cert),sort_keys=True)
    ops.extend([dict(op="observe",id=tag,focus=focus,kind="transfer",detail=detail),
                dict(op="review_edge",id=edge,decision="accepted",evidence="Replayed structural implication "+tag)])
    try:return record(g,"reformulate",focus,ops,trusted=True)
    except ValueError:return g

def auto_discharge(g,limit=2):
    check(g);count=0
    for focus in frontier(g):
        if count>=limit:break
        if focus not in frontier(g):continue
        goal=g["nodes"][focus]["statement"]
        try:s=cc.parse_statement(goal)
        except (ValueError,TypeError):continue
        candidates=[]
        # Prefer reusing an existing tighter proved obligation, then surgery.
        from proof_audit import audit
        report=audit(g)
        for i in sorted(report["proved"]):
            p=g["nodes"][i]["statement"];cert=dict(kind="monotone")
            if replay(goal,[p],cert):candidates.append((p,cert))
        if s["kind"]=="paths":
            for v in range(s["n"]):
                try:p=cc.statement(suppress(s,v))
                except ValueError:continue
                candidates.append((p,dict(kind="suppress",vertex=v)))
        for p,cert in candidates:
            h=insert(g,focus,p,cert)
            if h!=g:g=h;count+=1;break
    return g
