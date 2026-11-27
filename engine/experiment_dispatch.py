"""Bounded subprocess interface for allowlisted, declarative mathematical experiments.

No arbitrary command, source, import, URL or file paths are accepted from specs.
The trusted engine is not an OS sandbox for arbitrary third-party code.
"""
import argparse,hashlib,json,sys,tempfile
from pathlib import Path
from runtime import invoke,strict_json,read_json
import combinatorial_cover as cc
import finite_csp as fc
import modular_discovery as md
import cover_experiments as ce

ROOT=Path(__file__).resolve().parent
MODULES={"cover":cc,"finite-csp":fc,"modular":md}
FILES=("experiment_dispatch.py","runtime.py","combinatorial_cover.py","finite_csp.py","modular_discovery.py","cover_experiments.py")
def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def code_hashes():
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in FILES}

def validate(req):
    if not isinstance(req,dict) or set(req)!={"operation","spec","budget"}:raise ValueError("experiment request")
    op=req["operation"];budget=req["budget"]
    if op in MODULES:
        module=MODULES[op]
        maximum={"cover":cc.MAX_STATES,"finite-csp":fc.MAX_STATES,"modular":md.MAX_RESIDUES}[op]
        if type(budget) is not int or not 1<=budget<=maximum:raise ValueError("budget")
        spec=module.normalize(req["spec"])
    elif op=="cover-graphs":
        if budget is not None:raise ValueError("graph experiment budget lives in spec")
        spec=ce.validate(req["spec"])
    else:raise ValueError("unsupported experiment")
    return dict(operation=op,spec=spec,budget=budget)

def compute(req):
    q=validate(req);op=q["operation"]
    if op=="cover-graphs":return ce.run(q["spec"])
    return MODULES[op].solve(q["spec"],q["budget"])

def check_result(req,result):
    q=validate(req);op=q["operation"]
    if not isinstance(result,dict):return False
    if op=="cover-graphs":
        # Use full deterministic replay for a separate verification command;
        # during capture check every saved witness and sample independently.
        if result.get("spec")!=q["spec"] or result.get("spec_sha256")!=ce.digest(q["spec"]):return False
        return all(cc.replay(x["instance"],x["result"]["certificate"])==status
                   for name,status in [("counterexamples","refuted"),("examples","proved")]
                   for x in result[name])
    status=result.get("status")
    if status=="unknown":return "certificate" not in result
    return status in ("proved","refuted") and MODULES[op].replay(q["spec"],result.get("certificate"))==status

def execute(req,seconds=20):
    q=validate(req)
    if type(seconds) not in (int,float) or not 0<seconds<=120:raise ValueError("wall time")
    encoded=json.dumps(q,sort_keys=True,separators=(",",":"))
    if len(encoded.encode())>200000:raise ValueError("request size")
    before=code_hashes()
    with tempfile.TemporaryDirectory(prefix="harness-experiment-") as d:
        raw=invoke([sys.executable,str(ROOT/"experiment_dispatch.py"),"--child"],encoded,seconds,d,500000)
    if raw["returncode"]!=0:
        outcome=dict(status="unknown",reason=raw.get("termination") or "child-error",result=None)
    else:
        try:
            result=strict_json(raw["stdout"])
            if not check_result(q,result):raise ValueError("invalid result")
            outcome=dict(status="captured",result=result)
        except (ValueError,TypeError,KeyError,ArithmeticError):
            outcome=dict(status="unknown",reason="invalid-result",result=None)
    if before!=code_hashes():raise ValueError("engine changed during execution")
    return dict(schema=1,request=q,request_sha256=digest(q),code_sha256=before,
                wall_seconds=seconds,elapsed_seconds=raw.get("elapsed"),outcome=outcome,
                scope="trusted allowlisted experiment; capture is not universal proof; timeout is unknown")

def replay(receipt):
    try:
        if receipt["schema"]!=1 or receipt["code_sha256"]!=code_hashes():return False
        req=validate(receipt["request"])
        if receipt["request_sha256"]!=digest(req) or receipt["outcome"]["status"]!="captured":return False
        return execute(req,receipt["wall_seconds"])["outcome"]==receipt["outcome"]
    except (ValueError,TypeError,KeyError,ArithmeticError):return False

def main():
    if sys.argv[1:]==["--child"]:
        data=sys.stdin.buffer.read(200001)
        if len(data)>200000:raise ValueError("request size")
        print(json.dumps(compute(strict_json(data.decode()))));return
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest="action",required=True)
    a=sub.add_parser("run");a.add_argument("request");a.add_argument("output");a.add_argument("--seconds",type=float,default=20)
    a=sub.add_parser("replay");a.add_argument("receipt")
    args=p.parse_args()
    if args.action=="run":
        r=execute(read_json(args.request),args.seconds)
        with Path(args.output).open("x",encoding="utf-8") as f:json.dump(r,f,indent=2)
        print(json.dumps(dict(status=r["outcome"]["status"])))
    else:
        ok=replay(read_json(args.receipt));print(json.dumps(dict(replayed=ok)))
        if not ok:p.exit(1)
if __name__=="__main__":main()
