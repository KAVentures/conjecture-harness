# Optional discovery engine

The primary workflow is protocol/DISCOVERY.md, usable directly in a fresh ChatGPT conversation. The graph engine is a supplemental implementation, not a general theorem prover.

## Commands

From the repository root with Python 3.10+:
```sh
python discovery.py state.json init 'Exact conjecture statement'
python discovery.py state.json plan
python discovery.py state.json prompt
python discovery.py state.json apply proposals.json --mode backward --focus goal
python discovery.py state.json apply reviewed.json --mode backward --focus goal --trusted-review
python discovery_run.py state.json --config config.json --attempts 8 --seconds 600 --timeout 120
```

Use a new state file per immutable target. Proposals are JSON arrays of operations:

```json
[
  {"op":"claim","id":"lemma1","statement":"Precisely quantified sufficient lemma"},
  {"op":"derive","id":"bridge1","parent":"goal","premises":["lemma1"],"argument":"Conditional proof of the bridge, with hypotheses"},
  {"op":"observe","id":"test1","focus":"lemma1","kind":"experiment","detail":"Actual test, inputs and evidence path, with scope"}
]
```

This is a schema illustration, not evidence. Supported observation kinds: counterexample, experiment, proof_sketch, obstruction, transfer, refinement. Use observation details to track source locators, parent IDs and mathematical mutation rationale. The engine disallows cycles across live alternative edges (conservative DAG restriction) and exact normalized-text duplicate claims. It does not recognize semantically equivalent mathematical claims. Multiple premises are AND; alternative edges are OR.

Only the operator, after actual evidence review, may explicitly submit review_claim (established/refuted) or review_edge (accepted/rejected) with an evidence locator and explanation. Example schema:

```json
[{"op":"review_edge","id":"bridge1","decision":"accepted","evidence":"Path to reviewed conditional derivation, and reviewer rationale"}]
```

Do NOT execute this example or pass --trusted-review merely because a model suggested approval. The flag is a trust boundary for locally controlled records, not identity authentication, a formal proof verifier or a security sandbox. Exact witness replay, formal proof checking, literature and expert review are separate gates. Rejected claims remain in the graph for refinement. Contradictory reviewed evidence must be investigated; do not override the history.

## Runner and scheduler

Use config.example.json with a trusted worker command. The new runner accepts a JSON array on stdout, not the older harness.py single-object contract. It preserves prompts and raw output in state.json.runs/ and records valid batches atomically; invalid batches record zero progress. A lock prevents overlapping supported CLI mutations. The runner is serial, bounded and mock-tested only; it does not run genuine independent model agents, formal verifiers or automatically approve evidence. A blind prompt omits prior graph content but does not isolate a provider or its external memory. Work directories do not provide security isolation. Review logs before sharing. All output budgets are cooperative.

The controller tracks reachable obligations and uses reviewed graph transitions for reward. Reviewed closures, accepted/rejected reachable implications and relevant refutations count; detached claims and unreviewed observations do not. After three no-progress cycles it changes strategy; a counterexample observation in a falsification cycle triggers refinement. It favors shared dependencies and rarely visited nodes. Reward and route selection are heuristic, not calibrated; model-generated proposals do not self-certify or earn rewards. Operator review is currently required to update evidence status. The graph does not execute mathematical transformations or prove implications on its own. No guarantee of open-problem resolution or speedup.

## Verification and next experiments

Run python -m unittest discover -s tests -v. The v0.6 change added 15 targeted tests; the complete local development suite passed 63 tests. Tests exercise AND/OR semantics, rejection of cycles and duplicate claims, target drift, atomic batches, relevant reward, stagnation, refinement, mock runner resume and attempted self-certification. They do not prove mathematical soundness of operator-provided evidence or establish real-model discovery performance. Next: trusted checker adapters, stronger typed representations, semantic duplicate detection, isolated parallel researchers, and a matched-budget held-out scientific evaluation.

## Exact graph lemma lab

[LEMMA_LAB.md](LEMMA_LAB.md) adds a bounded typed counterexample search with automatic refutation only for exactly bound canonical claims. The independent replay gate does not depend on model approval. Run python lemma_benchmark.py for a small matched-budget control comparison. This is a narrow mathematical adapter, not a general falsifier.

## Route-aware frontier

The scheduler now estimates each live root alternative by counting unresolved claims and candidate implications separately. Shared obligations count once; repeated visits increase the cost proxy. It explicitly surfaces an unchecked implication when all premises are established and returns to a surviving parent after falsification. This is a greedy heuristic, not globally optimal proof search or a calibrated probability. Text duplicate detection preserves case because mathematical symbols such as delta and Delta may be different. Six additional tests cover these behaviors.

## Automatic exact proof adapter

See [AFFINE_PROOFS.md](AFFINE_PROOFS.md). Reachable canonical affine implications are automatically attempted in the runner and only established after exact certificate replay. This is a restricted proof procedure, not an arbitrary mathematical verifier. The local suite now passes 94 tests.
