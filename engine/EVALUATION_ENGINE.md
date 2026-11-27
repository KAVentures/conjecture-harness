# Full-engine historical evaluation arm

The existing historical evaluator retains its two-arm default. Opt in with
```sh
python historical_eval.py run tasks.json design.json worker-config.json trial --calls 4 --timeout 60 --full-engine
```
The engine arm spends its earlier model-call slots on the actual discovery runner with exact discharge and metareasoning, preserves engine states, logs and audits, then asks for a standalone human-readable answer in the final slot. Baseline arms use their original response protocol. The review packet contains all cells (intermediate engine slots are placeholders, not claimed proofs). Review all cells and use the final answer as the engine candidate. The existing frozen references, integrity checks and review coverage apply. Engine overhead and prompt lengths differ; this is a matched maximum call-count/timeout comparison, not equal realized tokens, wall-clock compute, or costs. Record provider usage externally and do not claim matched inference until measured. Trusted worker commands must be isolated externally. No live-model experiment has yet been run.

For a stricter final-answer-only analysis, retain all packets and compare the final slot across all arms in a preregistered secondary analysis. Human reviewer independence and mathematical correctness cannot be inferred from hashes.
