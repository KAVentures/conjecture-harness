# Exact conditional proof composition and Lean export

The discovery runners automatically attempt typed affine implication bridges. Given a goal with hypotheses H, and premise claims of the form A_i => B_i, the bridge first proves each required A_i from H and previously obtained conclusions, then admits B_i conditionally on the premise claim. A final rational certificate proves the goal's conclusion from the resulting rows. A replay verifier checks every step against the original claim specifications. A bridge never certifies the premise claims themselves: the AND/OR graph still requires their independent establishment. Variable names and order must match exactly. Unsupported or exhausted searches stay unknown. The search is bounded, greedy, and incomplete.

Use affine_bridge.synthesize(goal, premises) and affine_bridge.replay_bridge(goal, premises, certificate), where premises is a mapping from claim IDs to canonical affine specs. Automatic bridge observations use reserved IDs and cannot be forged through normal worker operations.

## Lean source generation (not yet validated in Lean)

Run:

    python lean_export.py affine spec.json Claim.lean
    python lean_export.py polynomial spec.json Claim.lean

The exporter uses a fixed syntax generator and validated rational inputs; it never interpolates arbitrary model-supplied Lean commands. It emits a theorem over real variables, its hypotheses, a bounded tactic attempt, and a print-axioms command. This is a proof attempt, not a compiled proof or a new trusted acceptance path. In an independently pinned Lean 4 + mathlib project, run lake env lean Claim.lean, retain exact toolchain and mathlib commit information, inspect the actual theorem's correspondence to the source statement, and audit its transitive axiom list, rejecting sorryAx and unexpected axioms. Never trust an exit-code string supplied by a model. Lean is unavailable in the development runtime, so no successful compilation is claimed.

Local regression: 135 tests passed (12 new). These validate Python bridge search/replay, missing hypotheses, tampering, budget behavior, conditional graph integration, reserved evidence IDs, and Lean source rendering only. The bridge test uses synthetic, deliberately unestablished premise claims to exercise conditional sufficiency; it is not a mathematical theorem discovery. No authenticated model calls, general formal verification, or measured breakthrough-rate gains are claimed.
