"""Portable exact-engine interface. No network or external model calls."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

import combinatorial_cover
import finite_csp
import modular_discovery
from runtime import read_json

MODULES = {"cover": combinatorial_cover, "constraint": finite_csp, "modular": modular_discovery}
LIMITS = {"cover": combinatorial_cover.MAX_STATES,
          "constraint": finite_csp.MAX_STATES, "modular": modular_discovery.MAX_RESIDUES}


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write(path, data, new=False):
    path = Path(path)
    if new:
        with path.open("x", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     delete=False) as f:
        tmp = Path(f.name)
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def audit(state):
    if state["schema"] != 1 or state["target_sha256"] != digest(state["target"]):
        raise ValueError("invalid target binding")
    findings = []
    root = set()
    for entry in state["experiments"]:
        module = MODULES[entry["kind"]]
        statement = module.statement(entry["spec"])
        if statement != entry["statement"]:
            raise ValueError("statement mismatch")
        result = entry["result"]
        status = result["status"]
        if status in ("proved", "refuted"):
            if module.replay(entry["spec"], result["certificate"]) != status:
                raise ValueError("certificate replay failed")
            findings.append(status)
            if statement == state["target"]:
                root.add(status)
        elif status == "unknown":
            findings.append("unknown")
        else:
            raise ValueError("unknown result status")
    if len(root) > 1:
        raise ValueError("conflicting root certificates")
    return {"mode": "portable-exact-subset", "target": state["target"],
            "root_status": next(iter(root), "unverified"), "experiments": len(findings),
            "replayed": sum(x != "unknown" for x in findings), "statuses": findings,
            "scope": "Only exact typed statements are closed; no inference to prose targets."}


def selftest():
    cases = [
        ("cover", {"kind": "cover", "items": 3, "rows": [[[0,1,2],[]]],
                   "resources": [], "max_pieces": 1}, "proved"),
        ("cover", {"kind": "cover", "items": 3, "rows": [[[0],[]],[[1],[]],[[2],[]]],
                   "resources": [], "max_pieces": 1}, "refuted"),
        ("constraint", {"domains": [[0,1]]*3, "constraints": [
            {"kind": "different", "variables": [0,1,2]}]}, "refuted"),
        ("modular", {"variables": 1, "modulus": 6, "assumptions": [],
            "conclusion": {"terms": [[[3],1],[[1],-1]], "allowed": [0]}}, "proved")
    ]
    for kind, spec, expected in cases:
        m = MODULES[kind]
        r = m.solve(spec)
        if r["status"] != expected or m.replay(spec, r["certificate"]) != expected:
            raise ArithmeticError("portable control failed: " + kind)
    return {"mode": "portable-exact-subset", "passed": len(cases), "total": len(cases)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest="command", required=True)
    s.add_parser("selftest")
    r = s.add_parser("run")
    r.add_argument("--target", required=True)
    r.add_argument("--output", required=True)
    for name in ("resume", "audit"):
        r = s.add_parser(name)
        r.add_argument("--output", required=True)
    r = s.add_parser("solve")
    r.add_argument("--output", required=True)
    r.add_argument("--kind", choices=sorted(MODULES), required=True)
    r.add_argument("--spec", required=True)
    r.add_argument("--budget", type=int)
    a = p.parse_args()
    if a.command == "selftest":
        out = selftest()
    else:
        folder = Path(a.output).resolve()
        path = folder / "state.json"
        if a.command == "run":
            if not a.target.strip():
                p.error("empty target")
            folder.mkdir(parents=True, exist_ok=False)
            state = {"schema": 1, "target": a.target, "target_sha256": digest(a.target),
                     "experiments": []}
            write(path, state, new=True)
        else:
            state = read_json(path, limit=32*1024*1024)
        out = audit(state)
        if a.command == "solve":
            module = MODULES[a.kind]
            spec = module.normalize(read_json(a.spec))
            budget = LIMITS[a.kind] if a.budget is None else a.budget
            result = module.solve(spec, budget=budget)
            entry = {"kind": a.kind, "spec": spec, "statement": module.statement(spec),
                     "result": result}
            state["experiments"].append(entry)
            out = audit(state)
            write(path, state)
            out["latest"] = entry
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
