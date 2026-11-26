# Discovery protocol — v0.6 proof-state research

This is the default research loop for open conjectures. It extends RESEARCH.md; all statement fidelity, source, proof review, citation, authorship and publication gates remain mandatory. No installation is required for the chat method. No guarantee of a solution, independent agents, or background execution.

## 1. Maintain an actual mathematical frontier

Freeze the original quantified theorem and definitions. Maintain a branching proof state, not a chronological stream of standalone attempts. Keep research/PROOF_STATE.json (or a structured text equivalent when file tools are absent). Every node has an immutable statement, assumptions/domain, status, evidence locator, and unique ID. Every implication/hyperedge has an explicit argument: ALL its premises must hold to establish its conclusion; alternative sufficient sets are OR branches. An unproved bridge is an obligation too. Never combine lemmas under incompatible hypotheses. Reject circular dependencies; do not silently change a claim after seeing a counterexample. A new statement gets a new ID. An equivalence requires both directions independently; use separate directional obligations rather than a circular proof graph.

Maintain three kinds of evidence separately: established arguments or independently verified certificates; candidate arguments or observations; refuted hypotheses with exact counterexamples. Distinguish an AI self-review from independent human/formal verification. If the graph says a target is derivable, expand the entire dependency chain into a standalone proof and audit it again. A graph is not a theorem prover.

## 2. Begin substantive discovery immediately

Use three materially distinct representations as a starting portfolio, not three parameter variants. Identify a concrete bridge in each representation, and actually derive or falsify something in the first research cycle.

**Backward:** Negate the target or work backward from the desired inequality/construction. Find a sufficient lemma strictly more tractable than the original. Prove the implication conditionally before expending a long budget on the lemma; if the implication itself remains open record it as such. Decompose recursively into minimal jointly sufficient obligations. Avoid just restating the target, stronger conjectures with no leverage, or transferring the original difficulty into notation.

**Forward:** From exact established facts and genuinely applicable literature, derive consequences and bounds with their full hypotheses. Seek a nontrivial consequence that overlaps a backward obligation. A shared missing lemma used by multiple routes is a high-value focus. Record evidence and what uncertainty was removed.

**Reformulate:** Transfer to different mathematics (e.g. graph codes to algebraic, information theoretic or optimization objects). Specify maps, domains, preserved invariants, and direction of implication. Do not call a relaxation an equivalence. Ask: which theorem becomes available only in the new representation? Demonstrate a concrete application, or identify the first condition that fails.

## 3. Recursive hypothesis evolution

For each decisive missing lemma, generate competing hypotheses with distinct mechanisms, including one high-risk possibility and one deliberately weak sufficient hypothesis. Before deep proof work, attack the most fragile assertion with small, boundary, equality, degenerate and adversarial examples. Use exact computation if available; finite survival is not proof.

A falsified lemma is useful only if the failure changes the search. Preserve its exact witness, the failed assumption, scope of failure, and unaffected subclaims. Produce new hypotheses by relaxing the conclusion, restricting the domain (then separately proving coverage of the original domain), changing a parameter, replacing an invariant, adding a justified missing hypothesis or combining complementary premises from separate branches. Give each a new ID, record its parent IDs and prove/review the new bridge. Reuse counterexamples as a regression suite for variants. Do not reward a weaker lemma if it no longer suffices. Never treat a counterexample to an auxiliary lemma as a disproof of the original conjecture.

For literature transfer, identify a specific theorem in a primary source, write its exact hypotheses and conclusion, construct a mapping from our objects, find the obstruction to applying it, and try to discharge that obstruction. A list of references is not a mathematical advance.

## 4. Stagnation and resource policy

A research cycle ends with an explicit derivation, checked witness, refutation, obstruction, justified reduction, or clearly reported no-progress attempt. Distinguish new candidates from established facts. Give zero progress credit to unreviewed claims, repeated numerical results, cosmetically altered formulations, disconnected easy lemmas and model confidence. Give positive credit to justified reductions, verified relevant lemmas or counterexamples that remove real target-connected routes. Record time/tool calls/actual model usage where measurable; do not invent tokens or costs. These are heuristics, not calibrated success probabilities.

Default escape rule: after three consecutive cycles without reviewed target-relevant progress, stop repeating the incumbent method. Alternate a target-only fresh branch, cross-domain reformulation, recombination of surviving premises and exact falsification. After a concrete counterexample, prioritize a corrected hypothesis. If the same missing lemma recurs, split it, seek a weakening that still suffices, or switch to a different bridge. For computation, vary the mathematical construction family, symmetry assumptions or encoding; do not merely increase random seeds around a known incumbent. Record explored restrictions separately from universal exclusions. Revisit a stalled route only with a stated new mechanism or evidence.

Reserve effort for both exploration and exploitation; use observed progress per comparable budget and uncertainty to choose routes. Avoid starving risky but genuinely distinct representations. The executable scheduler uses an uncalibrated upper-confidence-style heuristic and a deterministic escape rotation; it is not an empirically calibrated expected-value estimator.

## 5. Independence and execution

If separate contexts/models actually exist, give a blind worker only the frozen statement and goal, without failed approaches, proposed endpoint or incumbent solution. Reconcile its findings only after it finishes. If using one ChatGPT conversation, call this a fresh-route exercise, never independent research. Run falsification and review separately from generation. A model cannot certify itself by returning an accepted label. Do not execute untrusted candidate code or expose credentials; use constrained, reviewed tools. Report which actual searches, computations and reviews ran.

Optional executable: discovery.py initializes and maintains an AND/OR state, validates graph updates, plans modes, and accepts explicit operator-reviewed decisions; discovery_run.py invokes a trusted model command for bounded proposal cycles. The worker returns claims, candidate derivations and observations only. Human/operator evidence acceptance is not formal verification. Keep separate exact verifier outputs and formal proof checks as required by RESEARCH.md. The existing harness.py portfolio and finite checkers remain available. No automatic general counterexample solver, semantic theorem prover, Lean bridge or genuine parallel blind orchestration has been integrated into the new graph yet.

## 6. Checkpoint, output and scientific claims

At the end of each turn preserve the exact statement fingerprint, proof-state graph, relevant established nodes, candidate bridges, unresolved frontier, refuted claims and actual evidence, last strategy, stagnation count, budget spent, and highest-value next test. On "continue" load this state; do not begin another unanchored attempt. In chat without files, provide a compact structured checkpoint. A cycle that yields no progress is legitimate; do not invent a mathematical result to satisfy the protocol.

For a candidate result, apply RESEARCH.md and OUTPUT.md in full. Include the proof graph and experiment logs in the generated research repository alongside the complete paper, citations, AI disclosures and reproducibility files. Scientific evaluation remains separate: compare against matched-budget baselines on frozen held-out targets, with independent correctness review. A failure on Shannon is diagnostic, not proof of general ineffectiveness, and a solved control is not evidence of novelty.

## Shannon example — research instructions, not a result

For the triangular graph T5 (complement of the Petersen graph), maintain distinct goals for exact Shannon capacity and for finite lower-bound improvements. A 63-word length-five code would improve on the lower bound 12^(1/3), but not establish the exact capacity. Do not presume the upper endpoint is attainable. A possible backward branch is an exact pairwise distinguishable code with the required cardinality; a different branch seeks asymptotic constructions that do not require that finite milestone. An upper-bound branch must prove a valid bound on every strong power. Record the actual word alphabet, graph convention and pairwise criterion. Prove transfers between graph powers, zero-error codes, algebraic encodings and optimization bounds before treating them as equivalent. A failed search in a fixed symmetry class does not rule out arbitrary codes. In particular, the new graph layer does not produce a Shannon breakthrough by itself.

## Executable falsification adapter

For supported graph-invariant lemmas, use [LEMMA_LAB.md](../LEMMA_LAB.md): create a precise canonical graph claim, test structural families before exhaustive enumeration, independently replay any counterexample, and refine the failed hypothesis using its witness. Do not mark a natural-language claim refuted unless its correspondence with the canonical claim has been justified. The adapter never promotes finite survival into a proof. For other domains, use actual exact checkers or record the gap explicitly.

## Route prioritization

Compare alternative paths by their distinct unresolved lemmas AND unchecked implications; count shared dependencies once. If all premises of a candidate bridge are established, stop generating new premises and audit that implication directly. After a refutation, revisit a reachable parent and replace the failed premise or bridge. Penalize repeated unproductive visits, but do not mistake the number of obligations for proof difficulty. Preserve case-sensitive mathematical notation when detecting textual duplicates.

## Automatically prove intermediate claims

When a missing lemma can be reduced to a universal rational affine implication, use [AFFINE_PROOFS.md](../AFFINE_PROOFS.md). State every assumption and variable domain; prove the mapping from the original lemma. Generate an exact nonnegative-combination certificate using the bounded elimination engine and replay it directly. Preserve the certificate and exact claim. For unsupported mathematics, continue seeking proof or verified counterexamples; never substitute a narrower supported problem for the intended target. In chat without execution, derive and check the same certificate manually and report that no tool ran.

## Nonlinear algebraic discovery

Where appropriate, reduce candidate lemmas to exact rational polynomial identities or nonnegativity on the reals/nonnegative orthant. Justify the variable map and all domain restrictions. [POLYNOMIAL_PROOFS.md](../POLYNOMIAL_PROOFS.md) provides exact normalization, weighted-square certificates and rational counterexamples. Try symbolic factorization or a sum of squares; independently expand the certificate and verify weights/domain. Failure of a particular decomposition is not disproof, and finite grid survival is not proof. Do not misrepresent general constrained polynomial inequalities as unconstrained claims.

## Parallel discovery portfolio

When separate execution contexts actually exist, freeze one proof-state snapshot for each batch, give researchers distinct mathematical modes and at least one target-only branch, then reconcile their outputs by exact claim and dependency correspondence. Retain all original arguments and rejected attempts. Never merge a model's proposed truth status into reviewed evidence. Use [PORTFOLIO.md](../PORTFOLIO.md) for the optional concurrent subprocess implementation; separate prompts and working directories do not establish actual provider independence or security isolation. In a single chat, run distinct research routes without claiming independent execution.

## Compose proven lemmas and certify bridges

Use [PROOF_COMPOSITION.md](../PROOF_COMPOSITION.md) to attempt typed affine bridges. Prove every prerequisite of each premise before using its conditional conclusion. Check the final implication independently, and never treat acceptance of a conditional bridge as proof of its premises. Lean export generates typed proof attempts only; check in an actual pinned environment and audit assumptions before claiming formal verification.

## Exact equivalence and reformulation

Use [TRANSFORMATIONS.md](../TRANSFORMATIONS.md) to avoid repeated typed claims under renaming, positive scaling and supported permutations. Never infer equivalence from similarity in prose. Preserve assumptions, domain and inequality directions; justify both directions of new representations. For real univariate polynomials, attempt an exact translation that eliminates the next-leading coefficient and transport any certificate back to the original statement. Independently replay it on that statement. Candidate transformations without a verified bridge remain research hypotheses.

## Evolve a failed nonlinear hypothesis

For compatible polynomial nonnegativity obligations, a replayed point refuting P can suggest the shifted lemma A=P-P(x0) and compensating lemma B=T-A. The identity T=A+B must be checked exactly and both claims independently proved. A corrected value at one witness does not prove the revised claim. See [HYPOTHESIS_EVOLUTION.md](../HYPOTHESIS_EVOLUTION.md). For general mathematics, keep the same discipline: a revised hypothesis must discharge a precise target-connected obligation, and any missing compensation must become a separate proof obligation.

## Invent lemmas directly from the target

For supported multivariate polynomial nonnegativity, try [LEMMA_INVENTION.md](../LEMMA_INVENTION.md): derive sparse square candidates from target coefficients, subtract the exact contribution, and seek a certificate for the residual. Do not restrict the square support to positive even monomials of the original target; cancellation can conceal terms needed in the proof. Replay both universal certificates and the exact additive bridge on the unchanged target. A failed decomposition does not refute a target. Generalize the research principle, not the algebraic guarantee, to other domains.

## Recursive invention and proof-tree replay

When a useful decomposition leaves an unresolved residual, recursively search for simpler obligations. Preserve alternative branches, avoid repeated exact states, and bound the depth and total search work. A refuted residual eliminates that decomposition only. [RECURSIVE_INVENTION.md](../RECURSIVE_INVENTION.md) implements this for sparse square extraction; each internal additive bridge and every leaf is replayed on its exact original statement. The full proof tree must close before the target is established. Do not confuse bounded algebraic decomposition with general theorem proving.

## Transfer graph capacity to algebraic certificates

Use [CAPACITY_CERTIFICATES.md](../CAPACITY_CERTIFICATES.md) for rational Gram and finite-field rank certificates of Shannon capacity upper bounds, with graph edges interpreted as confusability. Every hypothesis of the tensor-product theorem is checked exactly. An independent packing can refute a proposed upper bound, but finite failure cannot prove one. Explicitly distinguish graph complements and strong products; a known bound is a control, not a new result. An unsuccessful search remains unknown.

## Symmetry-aware finite combinatorial proofs

Use [FINITE_POWER.md](../FINITE_POWER.md) for bounded clique search on distinguishability graphs, verified automorphisms and replayable coloring trees. Only use symmetry to restrict the search after establishing a valid orbit argument. Require an explicit witness for a finite lower bound and exhaustive certified branch coverage for a finite upper bound. Neither finite upper bounds nor exhausted search justify a universal Shannon-capacity upper bound.

## Discover structural graph reductions

Before spending effort on graph powers, seek a distinguishability-preserving map into a smaller induced graph. [GRAPH_REDUCTION.md](../GRAPH_REDUCTION.md) gives the all-powers proof and exact checker, including a closed-neighborhood folding search. Verify every nonedge, not merely sample graph powers. A certified upper bound on the reduced graph transfers back to the original; a lower witness must also be lifted and checked. Failure to reduce does not prove irreducibility under all maps.

## Literature-to-lemma theorem transfer

[THEOREM_TRANSFER.md](../THEOREM_TRANSFER.md) implements a checked graph-capacity rule based on complement homomorphisms from strong powers. Search for maps into graphs with useful known bounds, independently replay the map and bound arithmetic, and retain the source and all required premise claims. Never assume arbitrary product multiplicativity or disjoint-union additivity of Shannon capacity. For other literature theorems, extract the exact hypotheses, justify the mapping and make missing conditions explicit proof obligations; a citation is not evidence that a theorem applies.

## Evidence-driven strategy selection and tool-only operation

Credit the strategy that originally proposed a target-relevant verified obligation, not automatically the checker that later discharged it. Avoid counting an unreviewed observation as progress. Use bounded cost-aware exploration and periodically revisit all research modes. [STRATEGY.md](../STRATEGY.md) documents the optional scheduler and no-API exact adapter loop. An exact tool fixed point is only a checkpoint: continue substantive mathematical reasoning and seek new representations when a target remains unresolved.

## Nonlinear matrix discovery

Use [MATRIX_DISCOVERY.md](../MATRIX_DISCOVERY.md) for permanent inequalities: symbolic matching contractions, signed sufficient conditions, exact feasible cycle moves and bounded Bernstein certificates. Distinguish finite-matrix proofs, universal refutations and unresolved universal claims. Synthesize typed bridges without establishing their unproved premises. For other domains, generalize the discovery mechanisms rather than claiming unsupported automated certification.

### Cross-domain synthesis and extremal structure

For general nonlinear targets, require each research cycle to identify the representation and invariant, propose a proof mechanism (not merely a new statement), derive the transfer explicitly, and test the strongest vulnerable step. When dimensions are unbounded, seek parameterized identities, recurrences or induction before increasing the finite search budget. For extremal arguments, derive feasible variations, first/second-order necessary conditions and boundary cases; a sampled extremizer is not a reduction theorem. For literature transfer record exact hypotheses, conclusion, variable correspondence and missing premises. Recombine branches only if their dependencies and quantified domains match. Prioritize a verified new reduction over another numerical experiment. Preserve a blinded historical control with its proof withheld from worker prompts, and score discovery separately from certificate replay; no benchmark claim without actual matched-budget runs and review.
