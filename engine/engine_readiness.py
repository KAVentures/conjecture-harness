"""End-to-end, no-model readiness controls; no claim of open-problem solving."""
import argparse,json,tempfile
from pathlib import Path
from activate import execute
from proof_bundle import export,replay
from runtime import read_json
import finite_csp as fc
import modular_discovery as md
import combinatorial_cover as cc
import experiment_dispatch as ed

def run(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    cases=[
        ("cover-positive",cc.statement(dict(kind="paths",n=4,edges=[[0,1],[1,2],[2,3]],endpoints=[1,0,0,1],max_pieces=1)),"proved"),
        ("cover-negative",cc.statement(dict(kind="paths",n=3,edges=[[0,1],[1,2],[0,2]],endpoints=None,max_pieces=1)),"refuted"),
        ("constraint-negative",fc.statement(dict(domains=[[0,1]]*3,constraints=[dict(kind="different",variables=[0,1,2])])),"refuted"),
        ("modular-universal",md.statement(dict(variables=1,modulus=6,assumptions=[],conclusion=dict(terms=[[[3],1],[[1],-1]],allowed=[0]))),"proved"),
        ("untyped-open","Prove an unspecified universal mathematical assertion; no hypotheses or conclusion supplied.","unverified"),
    ]
    rows=[]
    for name,target,expected in cases:
        folder=output/name
        r=execute(folder,target,passes=4,seconds=30)
        a=r["audit"];bundle_ok=None
        if a["status"]=="proved":
            b=export(read_json(folder/"state.json",limit=32*1024*1024))
            bundle_ok=replay(b,target)
            (folder/"bundle.json").write_text(json.dumps(b,indent=2),encoding="utf-8")
        rows.append(dict(id=name,expected=expected,actual=a["status"],bundle_replayed=bundle_ok,
                         passed=a["status"]==expected and not a["conflicts"] and not a["invalid_observations"] and bundle_ok is not False and not r["worker_logs"]))
    q=dict(operation="modular",budget=16,spec=dict(variables=1,modulus=2,assumptions=[],conclusion=dict(terms=[[[2],1],[[1],-1]],allowed=[0])))
    receipt=ed.execute(q);ok=receipt["outcome"]["status"]=="captured" and ed.replay(receipt)
    (output/"experiment.json").write_text(json.dumps(receipt,indent=2),encoding="utf-8")
    rows.append(dict(id="experiment-receipt",passed=ok))
    result=dict(passed=sum(x["passed"] for x in rows),total=len(rows),cases=rows,model_calls=0,
                scope="transparent integration controls only; no scientific effectiveness or new theorem claimed")
    (output/"report.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",required=True);a=p.parse_args()
    r=run(a.output);print(json.dumps(r,indent=2))
    if r["passed"]!=r["total"]:p.exit(1)
if __name__=="__main__":main()
