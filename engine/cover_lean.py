"""Generate a Lean proof of an explicit compiled finite cover.

For graph instances the graph-to-rows translation is still Python; this is
not an independent formalization of graph theory or a universal theorem.
"""
import argparse,json
from pathlib import Path
import combinatorial_cover as cc
from runtime import read_json

def render(spec,certificate):
    s=cc.normalize(spec)
    if cc.replay(s,certificate)!="proved":raise ValueError("positive certificate required")
    n,resources,rows=cc.compile_rows(s)
    def nums(xs):return "["+", ".join(map(str,xs))+"]"
    def row(r):return "("+nums(i for i in range(n) if (r[0]>>i)&1)+", "+nums(r[1])+")"
    def table(rs):return "["+", ".join(row(r) for r in rs)+"]"
    allowed=table(rows);chosen=table([rows[i] for i in certificate["rows"]])
    conditions=["chosen.length ≤ "+str(s["max_pieces"]),
                "chosen.all (fun r => allowed.contains r) = true"]
    conditions += ["(chosen.flatMap Prod.fst).count "+str(i)+" = 1" for i in range(n)]
    conditions += ["(chosen.map (fun r => (r.2["+str(i)+"]?).getD 0)).sum = "+str(v) for i,v in enumerate(resources)]
    return ("import Mathlib\n\nset_option maxHeartbeats 2000000\n"
            "def allowed : List (List Nat × List Nat) := "+allowed+"\n\n"
            "theorem harness_checked : ∃ chosen : List (List Nat × List Nat),\n  "+
            " ∧\n  ".join(conditions)+" := by\n  refine ⟨"+chosen+", ?_⟩\n  decide\n\n#print axioms harness_checked\n")

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("spec");p.add_argument("result");p.add_argument("output")
    a=p.parse_args();source=render(read_json(a.spec),read_json(a.result)["certificate"])
    with Path(a.output).open("x",encoding="utf-8") as f:f.write(source)
    print("Exported unverified Lean attempt for compiled finite cover; build in trusted pinned mathlib project.")
if __name__=="__main__":main()
