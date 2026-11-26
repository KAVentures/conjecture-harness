# Read-only proof certificate audit

Run `python proof_audit.py state.json` to distinguish local review status from independently replayed mathematical evidence. Add `--require-verified` to return a nonzero exit code if the target is not proved or refuted by the supported certificate checkers, a conflict exists, or a recognized direct proof observation fails replay.

This tool reconstructs supported direct results using the exact original statement and certificate, including affine and polynomial proofs, polynomial and graph witnesses, finite graph-power certificates, graph capacity, structural reductions and recursive polynomial invention. It also checks additive polynomial identities, recorded affine bridge certificates and recorded graph-capacity transfer maps, and propagates proof only when every premise has replayed mathematical evidence. Exact typed equivalence can transfer verified results. Manual review flags alone never qualify. The report lists unverified recorded claims and refutations, conflicts and invalid recognized direct observations. Unsupported certificates or rejected bridge replays do not establish a result. It is not a complete auditor of arbitrary prose, proof history, all rejected/unused branches or mathematical novelty. It uses the repository's Python replay functions, not an independent implementation or proof-assistant kernel. Treat state files as untrusted research data, not authenticated records.

## Validation

Thirteen targeted tests pass, including tampered witnesses, manual-review-only claims, unsupported premises, recursive trees, direct certificates, graph-power proofs, theorem transfer and read-only behavior. Two disjoint regression batches ran successfully: 160 and 157 tests, 317 total.

The preview does not claim a solution to an open conjecture, independent fresh-chat acceptance, live-model superiority or successful Lean compilation.
