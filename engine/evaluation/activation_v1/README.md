# Activation v1 comparison protocol (not yet run)

Freeze an independently curated target set, reference revision, worker/model version, tool permissions, token/call and wall-time ceilings, and randomization seed before running. Include known controls for pipeline checks; report them separately from genuinely unresolved targets. The existing historical_v1 public pilot is not held-out or novelty evidence.

Four arms: A ordinary prompting; B legacy harness pinned to b03d5bc2eb47bf4d7ea633df940b1614ab059028; C canonical HARNESS.md in chat with the same native tools as B; D canonical contract plus activate.py and trusted runtime. Use identical models and target statements. Match model calls/tokens/time as far as measurable; explicitly report exact computation and budget overruns separately. Do not expose answer keys to workers. Randomize cells and blind qualified reviewers to arm and self-reported confidence.

Record target fidelity, complete proof/disproof (reviewer validated), verified intermediate lemmas, first invalid step, target-connected refutations, meaningful pivots, actual executed tool logs, access failures and elapsed budget. Keep compliance separate from mathematical correctness. For chat, distinguish observed tool traces from self-reported use; for runtime retain receipts and replay logs. Have independent reviewers resolve disagreements. A citation of a known result is not a new proof.

Use the existing engine_eval.py for its original three-arm experiment; it does not implement these four arms. The scorecard utility here validates and aggregates externally collected blinded review results; it does not launch model experiments or infer mathematical truth. No comparative results yet.
