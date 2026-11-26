# Exact equivalence and mathematical transformations

The typed equivalence adapter recognizes variable renaming, variable permutations (up to four variables), positive scaling, reordered or duplicated affine assumptions, and removal of tautological constant affine assumptions. Polynomial equalities additionally permit nonzero signed scaling. All operations are exact rational operations on validated canonical typed statements. Domain, relation and inequality sign are preserved. Larger affine systems recognize positional renaming only. Unequal signatures mean unknown, not inequivalence. No natural-language or embedding-based mathematical equivalence is claimed.

Parallel proposal reconciliation reuses equivalent typed nodes; candidate bridges still require proof. The original target statement is never rewritten. Existing graph nodes with reviewed status can transfer that status to an equivalent reachable node, citing the original evidence. This inherits the source's review trust level, not a new formal certification; conflicting equivalent reviews stop the run. Unchecked observations do not establish facts. Reserved evidence IDs cannot be submitted by untrusted workers.

## Polynomial reformulation

For a real univariate rational polynomial P of degree d >= 2, the transformer tries z = x - h, where h = -a_(d-1)/(d a_d). This eliminates the next-leading coefficient. It expands Q(z) = P(z+h) exactly, calls the existing solver, transports any weighted squares or rational witness back to the original variable, and replays the certificate on the original claim. Translation is a bijection on the reals; this adapter deliberately refuses orthant translation. An unsuccessful transformation leaves the claim unresolved. It is a bounded heuristic, not a complete polynomial decision procedure.

The automatic runner attempts this transformation after the ordinary polynomial solver leaves a supported obligation open. Two elementary regression controls demonstrate the behavior: the previous solver leaves (x-3)^4 >= 0 unresolved, while translation produces a replayed proof; it also misses a counterexample to (x-7)^4-1 >= 0, whereas the transformed search finds x=7 and verifies it exactly. These are targeted controls, not evidence about general mathematical novelty.

Local validation: python -m unittest discover -s tests -v — 170 tests passed in 32.617 seconds (21 new tests). No live-model performance or open-problem result is claimed.
