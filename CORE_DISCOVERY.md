# Core mathematical discovery extensions

Domain-independent research mechanisms with explicit supported algebraic languages, not a general theorem prover.

## Parameterized symbolic discovery

Canonical claims mean sum_{i=0}^{n-1} f(i,x) - g(n,x) = 0 or >= 0 for **every** integer n>=0 and every nonnegative real parameter vector x. Terms are [exponent vector, rational coefficient]; first exponent is i or n. Up to three real parameters, degree 12 in f and degree 13 in g, 128 input terms. The variable n is unbounded, not sampled for proof.

    python symbolic_discovery.py spec.json --discover
    python symbolic_discovery.py spec.json

Example: {"parameters":["x"],"relation":"zero","summand":[[[1,1],2],[[0,1],1]],"rhs":[[[2,1],1]]}.

Discovery converts each coefficient polynomial in i to its Newton basis by finite differences. Since sum_{i<n} binom(i,k)=binom(n,k+1), the candidate sum is immediate. The checker uses a different representation: expand falling factorials to powers, verify q(0)=0 and q(n+1)-q(n)=f(n) by exact coefficient identities. Induction proves q equals the sum at every n; no finite interpolation result is accepted without these checks. Nonnegative coefficients in the residual Newton basis imply nonnegativity because every binomial basis value is nonnegative on integers n>=0 and parameters are nonnegative. This certificate is sufficient, not necessary. A finite counterexample is evaluated from the original sum, not the inferred closed form.

The discovery graph and read-only audit dispatch exact canonical statements. Natural-language problems must justify the mapping independently. This is a stepping stone toward general recurrences, indexed sums, parameterized inequalities and asymptotic reasoning; arbitrary recursive sequences, nonpolynomial functions, symbolic exponents and arbitrary-dimensional tensor contractions are not supported here.

## Cross-branch proof synthesis

Given a target nonnegative polynomial and existing established/derived polynomial lemmas on the same variable list and domain, search for a sparse strictly positive rational combination equaling the target. For each candidate subset solve exact coefficient equations by Gaussian elimination, then independently replay the identity. At most 24 source lemmas, subsets of size at most four, bounded search. Only exact domain-compatible combinations generate accepted implication edges. Premise status still must be audited: an accepted bridge cannot turn unsupported manually marked premises into a verified proof.

## Research and evaluation limits

These mechanisms improve the set of mathematically constructive actions available in the no-model loop. They do not prove an arbitrary conjecture or establish improved open-problem solving. The existing external worker portfolio supports distinct trusted commands and blind assignments; separate commands do not establish independent providers or security isolation. General theorem transfer still requires a proof of the mapping and all hypotheses, and human or formal review for unsupported arguments.


## Historical proof-discovery evaluation

historical_eval.py accepts an operator-curated statement-only historical task list and a separately held reference mapping. It freezes both by hash, matches blind and adaptive arms by call count and timeout, randomizes job order, retains every response, and exports a shuffled review packet without arm labels. Unlike the synthetic certificate benchmark, it requires external proof review before reporting results.

Public tasks JSON: [{"id":"case-id","statement":"exact quantified statement"}].
Private references JSON: {"case-id":{"expected":"proved","source":"verified bibliographic locator","reference":"reference proof or private locator"}}.

    python historical_eval.py freeze tasks.json private-references.json design.json
    python historical_eval.py run tasks.json design.json worker-config.json run-output --calls 4
    python historical_eval.py score tasks.json private-references.json run-output reviews.json

The worker config is {"worker":["trusted-command","argument"]}. Keep private references and the private key away from workers and reviewers until review is frozen. Give reviewers only review-packet.json; reviews.json is a list of {id,sha256,verdict,reviewer,rationale}, where sha256 is historical_eval.digest(packet_item), and verdict is proved/refuted/partial/incorrect/abstained. Do not have a candidate's own worker review itself. Use actual qualified external reviewers, adjudicate disagreement, and report reviewer independence honestly. The software validates coverage, reference consistency and hashes, not reviewer identity or mathematical correctness. Trusted subprocesses are not sandboxed and may access the filesystem; use external isolation if required.

This is a framework, not a completed historical benchmark or a claim that the tasks are absent from model training. Curate real historical problems from different domains and difficulty levels, freeze them before development, preserve a separate development set, and avoid using held-out results to tune the engine. A synthetic unit-test fixture checks the protocol only. No historical corpus or real-model results are shipped in this change.


## Checked representation transfer

representation_transfer.py searches maps from a source polynomial's coordinates into a target's coordinate space. The source and target need not have the same number of variables. It tries projections, coordinate identification, signs, scaling, shifts, pairwise sums/differences and squares. Replay accepts arbitrary polynomial images within the bounded polynomial language, verifies the source domain is preserved, expands the substitution and checks the target is exactly a positive rational multiple. A source on the nonnegative orthant requires a termwise nonnegativity certificate for every image on the target domain; a source on all reals has no such restriction. Equality and nonnegativity relations are preserved separately. Example: from x>=0 on the nonnegative orthant, substitute x=u^2 to infer u^2>=0 on all real u. From x^2>=0 on all reals, substitute x=u+v to infer (u+v)^2>=0 on all real u,v.

The runner searches a bounded set of existing established/derived lemmas and inserts only a replayed implication. The audit still requires source proof evidence. The map search is incomplete; absence of a map proves nothing. This is a general reusable transfer rule, not arbitrary theorem retrieval or semantic cross-domain proof synthesis.

Each automatic synthesis pass caps eligible target attempts as well as successful bridges; source pools and per-source map searches are bounded. The historical evaluator's current adaptive arm is a strategy-prompt baseline, not a head-to-head run of the full proof-state engine. Integrating full-runner artifacts and qualified external review on a real historical corpus is a separate evaluation milestone.


## Recurrence and invariant invention

dynamics_discovery.py treats an autonomous polynomial map T:R^d -> R^d and observable p:R^d -> R. Coordinates and observable have rational coefficients. Supported maps have at most four variables and degree at most two; observable and intermediate expansions degree <=8, recurrence order <=6, bounded coefficients and term counts.

For a proposed recurrence, replay verifies the polynomial identity sum_j w_j p(T^j(x))=0 with last weight 1. Substituting x=T^n(x0) proves it for every real initial state and all n>=0. Discovery builds the symbolic Krylov sequence p,p∘T,... and computes an exact rational nullspace, searching for a monic dependency. This is not fitting a finite numerical sequence.

For a supplied rational initial state, an orbit-zero claim is p(T^n(x0))=0 for all integers n>=0. A replayed global recurrence and exact zero initial values imply the claim by induction. If this fails, ideal_induction.py starts with p and repeatedly divides pullbacks by a finite basis, adding necessary residual equations if they vanish initially. Replay independently checks that every basis polynomial vanishes at x0 and that each pullback equals a polynomial linear combination of the basis. Induction proves the common zero set is preserved and hence p=0 at every iterate. The certificate is sufficient, not complete: no Groebner basis or arbitrary invariant ideal completeness claim. The basis is capped at six, division and expansion bounded, and certificate size capped.

The invariant-basis command computes the nullspace of q∘T-q on the space of polynomials of degree at most 1, 2 or 3, omitting constants (which are always invariant). When it completes, it spans the invariants modulo constants in that selected degree space. Every returned nonconstant basis element is separately replayed as a recurrence of order one. No claim is made for higher degrees.

    python dynamics_discovery.py system.json --mode invariants --degree 2
    python dynamics_discovery.py observable-system.json --mode recurrence
    python dynamics_discovery.py claim.json

Example system (x,y) -> (x+1,y+2x+1): {"variables":["x","y"],"transition":[[[[1,0],1],[[0,0],1]],[[[0,1],1],[[1,0],2],[[0,0],1]]]}. The discovery engine can recover the invariant y-x^2 (up to nonzero scaling). For a recurrence-discovery input add observable, e.g. [[[1,0],1]]. For a canonical recurrence claim also set kind="recurrence" and weights, or kind="orbit-zero" and initial. A counterexample is an exact rational initial state (for a universal recurrence) or a violating iterate index (for a fixed orbit). All claims bind to the exact transition and observable; unsupported recurrence growth and bounded search failure return unknown. Natural-language problems need a separately justified encoding into these systems.


## Dimension-free indexed symbolic algebra

indexed_algebra.py handles sums of products of arbitrary real tensors with a common index range 1..n for every integer n>=1. Tensor rank 1..3, at most six declared tensors, five distinct dummy indices and six factors per term; symmetric and fully alternating tensors are supported. Each term has a rational coefficient, explicit n_power, and a list of [tensor_name, index_list] factors. Repeated index labels identify indices; every distinct label is summed exactly once. An unused summed index must be expressed as a factor n, not silently discarded. Rank-two delta declarations denote the fixed Kronecker equality indicator, not an arbitrary tensor. The normalizer merges equality-connected dummy indices by union-find and accounts for isolated classes with exact dimension factors. Finite witness replay evaluates the indicators directly (their array list is empty). There are no free indices, inequality claims or general tensor symmetries in this language.

The normalizer enumerates dummy-index permutations, normalizes symmetric slots and alternating signs, sorts commuting factors and combines equivalent contraction terms. A repeated alternating index or a sign-reversing automorphism gives zero. Cancellation in this normal form is sound in every dimension, though the normal form is incomplete for all possible identities. If cancellation fails, bounded exact rational assignments in dimensions 1..3 can refute the claim. Finite survival is unknown.

Example: contraction of a symmetric matrix S with an alternating matrix A is zero:
{"tensors":{"S":{"rank":2,"symmetry":"symmetric"},"A":{"rank":2,"symmetry":"alternating"}},"terms":[{"coefficient":1,"n_power":0,"factors":[["S",[0,1]],["A",[0,1]]]}]}.

    python indexed_algebra.py indexed-claim.json

## Constrained algebra and extremal reduction

simplex_discovery.py handles rational polynomials of degree at most six in two to four nonnegative real coordinates summing to one. Homogenize to degree d using (sum x_i)^(d-k) for every degree-k term. The normalized homogeneous coefficients are Bernstein coefficients; if nonnegative, the polynomial is nonnegative on the whole simplex. For a sub-simplex with rational vertices, compose the polynomial with the barycentric map and repeat. Exact midpoint edge splitting covers the parent simplex with two children; replay requires a valid certificate on both children. Degree elevation and deterministic longest-edge subdivision are bounded, incomplete searches. Negative coefficients are not counterexamples; only an exact negative evaluation at a feasible rational point refutes a claim.

extremal_reduction.py discovers exchange-concavity reductions. For a pair i,j, freeze all other coordinates and their sum x_i+x_j. If -(partial_i-partial_j)^2 p is nonnegative on the simplex, p is concave along each feasible exchange segment. Its minimum on the segment is attained at an endpoint, on x_i=0 or x_j=0. Thus the original inequality follows from three explicit obligations: the negative exchange curvature and the two face restrictions. The graph generates lower-dimensional claims and accepts only this exact conditional implication; independent replay must verify all three premises before closing the original claim. Search tries pairs with a replayable curvature certificate and does not presume convexity, concavity or the extremizer from sampling.

    python simplex_discovery.py simplex-claim.json

Example: {"variables":["x","y"],"terms":[[[2,0],1],[[1,1],-2],[[0,2],1]]}. This is (x-y)^2 >=0 on the simplex; a midpoint split exposes nonnegative Bernstein coefficients on both halves.

These adapters are reusable algebraic building blocks, not unrestricted arbitrary-dimensional tensor algebra or a global optimization engine for general semialgebraic domains. A mapping from a natural-language conjecture must be justified separately.


## Conditional theorem discovery and hypothesis completion

conditional_theorems.py represents a universally quantified polynomial implication over real or nonnegative real variables (one to four). Each of at most eight assumptions is a polynomial equality or nonnegativity inequality; the conclusion is a polynomial nonnegativity inequality. Example: {"variables":["x"],"domain":"real","assumptions":[{"relation":"nonnegative","terms":[[[1],1]]}],"conclusion":[[[3],1]]}. This states x>=0 implies x^3>=0. Search discovers a polynomial identity by subtracting monomial multiples of individual assumptions or pairs, then tries an exact sum-of-squares residual certificate. Replay accepts products of up to three distinct assumptions: a multiplier on an all-inequality product must be termwise nonnegative on the base domain; any product containing an equality vanishes on the feasible set so its multiplier can have either sign. The residual must have a checked SOS certificate. Only a feasible exact negative point refutes a theorem. Incomplete searches return unknown.

theorem_application.py treats a known or proposed conditional theorem as a reusable mathematical abstraction. It searches a polynomial map and positive scale making the source conclusion exactly the target conclusion, using the checked representation-transfer rule. It then generates a distinct proof obligation for the source theorem itself and every substituted hypothesis; an equality generates both nonnegative signs. For conditional targets, these obligations keep the target's assumptions and base domain. Exact domain preservation is required before applying the theorem. A checked application is an implication edge, not proof of any premise. The proof audit independently replays the edge and requires verified source and hypothesis evidence. Unproved source theorems remain open, even when supplied with a citation.

    python conditional_theorems.py theorem.json
    python theorem_application.py proof-state.json source.json --focus goal

The source file is {"theorem":{...},"source":"bibliographic citation or URL","locator":"theorem and page number"}. It records provenance in the graph without treating it as proof, checking the publication, or claiming the source was fetched. The automatic runner also searches a bounded pool of conditional theorem claims already present in the graph. External researchers can use literature search to supply exact theorem statements, hypotheses and locators, but the software does not autonomously retrieve or semantically parse arbitrary papers. Unsupported theorem languages and unverified literature transfers require separate mathematical review.


## Portable mathematical knowledge

knowledge_bank.py exports directly replayable mathematical certificates from one proof graph and imports them into another. Export ignores manual review labels and composite-only proofs; it replays each supported certificate and rejects reported evidence conflicts. Import replays every certificate again, creates established typed lemmas or resolves matching existing claims, and records the originating claim/observation and target fingerprint. The origin fields are provenance metadata, not authenticated authorship. Imported refutations only apply to identical existing claims. Imported proved facts can be reused by existing theorem application, representation transfer and synthesis passes. No imported result can prove an unrelated target merely by retrieval similarity.

    python knowledge_bank.py export old-proof-state.json old-facts.json
    python knowledge_bank.py merge combined.json old-facts.json other-facts.json
    python knowledge_bank.py import new-proof-state.json combined.json --limit 8

The library is capped at 256 facts per bank and imports at most 32 per call. Retrieval scores are only heuristics, not mathematical equivalence or applicability. This first version supports direct exact certificates; it does not yet package entire multi-step proof DAGs or retrieve papers autonomously. For literature-derived but unverified statements, use theorem_application.py and retain the source theorem as an open obligation.


## Portable multi-step proof DAGs

proof_bundle.py exports the exact proof route selected by the independent audit, including direct certificates, checked conditional implication edges and verified equivalence steps. It strips unrelated observations, worker history and manual review labels. Each step is replayed in dependency order against its exact statement; the root must depend on every included step. A bundle can be imported as a verified lemma into another graph, and the read-only audit replays it again. The current format is limited to 32 steps and 18,000 serialized characters, and rejects nested bundles rather than allowing unbounded recursive certificates. Only supported exact proof rules are portable; prose or unsupported manual proofs are not.

    python proof_bundle.py export old-state.json proof.json
    python proof_bundle.py verify proof.json
    python proof_bundle.py import new-state.json proof.json


## Source-bound literature pipeline

literature_discovery.py optionally retrieves arXiv abstract metadata via the fixed public API, or ingests an operator-supplied verbatim paper text file with source and page/theorem locator. External trusted worker commands receive bounded overlapping source spans and the exact target. They propose supported conditional polynomial theorem structures and verbatim excerpts. The coordinator checks the quote exists in the source span and binds it to the full document hash and absolute offset. It cannot certify that an extracted formalization is semantically faithful, that the paper is correct, or that a citation is novel. All source claims remain open until supported proof evidence is replayed.

    python literature_discovery.py search 'cat:math.CO AND all:inequalities' docs.json
    python literature_discovery.py add-text paper.txt local-docs.json --source 'citation' --title 'paper title' --locator 'pp. 3-5'
    python literature_discovery.py extract state.json docs.json worker-config.json extraction-output
    python literature_discovery.py apply state.json docs.json extraction-output/leads.json

Search is opt-in and returns abstracts, not full papers; use add-text for actual theorem passages. No automatic arbitrary URL fetch, PDF parsing or web search beyond arXiv metadata is included. The extraction runner requires a configured external worker and treats source text as untrusted data; it is not a security sandbox. Application searches exact supported maps and creates source and hypothesis obligations; no publication is triggered. Preserve original documents and extraction logs for correspondence review.


## Audit-grounded strategy learning

    python strategy_profile.py profile.json state-a.json state-b.json --audited

The opt-in audited mode counts proposal attempts, attributes positive credit only to first proposers on an independently replayed goal proof route, and assigns adverse credit to exactly refuted proposed claims. Each attempt receives at most one positive and one adverse credit. Manual review labels, unsupported claims and irrelevant verified lemmas are not positive evidence. This complements the existing review-based profile, retaining the same bounded prior format; it is retrospective attribution, not proof of causal improvement. Historical provenance itself is not authenticated. Compare profiles in matched experiments rather than claiming a breakthrough rate from training data.


## Audit-aware metareasoning

    python metareasoning.py state.json
    python discovery_run.py state.json --config workers.json --metareasoning
    python discovery_portfolio.py state.json --config workers.json --metareasoning

The optional planner independently replays the proof state to distinguish
verified premises from recorded review labels. It reports implications ready
for verification, exactly refuted premises, recorded-only rejections, unchecked
accepted edges, blocked routes and shared unresolved obligations. It prioritizes
ready bridges with a short retry cap, repairs newly refuted premises and
redirects stagnating exploration. It preserves the baseline blind worker;
blind prompts receive no diagnostic, history or proposed-strategy content.

Non-blind workers can propose new mathematical mechanisms through a normal
refinement or obstruction observation. The detail JSON has exactly
{"research_strategy":{"mode":"reformulate","mechanism":"...","test":"...","rationale":"..."}}.
The coordinator accepts bounded text and a recognized research mode, retrieves
recent strategies for reachable obligations, and records the normalized
mechanism/test fingerprint when an attempt uses one. Cards are untrusted
research proposals, not commands or proof evidence; they cannot change the
execution configuration. Deduplication is lexical, not semantic. The planner
halts on contradictory exact evidence or reports recorded closure requiring
operator review when the audit cannot independently reproduce it.

The feature is opt-in to preserve baseline behavior for comparison. It
provides a concrete mechanism for adaptive research, not a guarantee of
novel insights, optimal strategy selection or autonomous software extension.


## Adaptive exact adversarial search

The ordinary polynomial adapter now reserves part of its point budget (at
budgets >=64) for deterministic multiscale rational exploration after the
initial grid and quadratic coordinate probes. It uses evaluated incumbents,
coordinate and paired-coordinate directions, fine dyadic displacements and
remote axis/diagonal configurations. Each distinct new point consumes one
unit of budget and must remain in the declared domain. The existing replay
checks the exact witness independently. Failure to find a counterexample is
unknown, not a proof of nonnegativity. This is a bounded heuristic, not a
complete global optimizer.

## Optional Lean 4 / Mathlib verification

    python lean_bridge.py export state.json HarnessCheck.lean --tactic nlinarith
    python lean_bridge.py verify state.json --project /path/to/trusted/mathlib-project --timeout 60 --report lean-report.json

Supported exact claim languages: real and nonnegative polynomial identities
and inequalities, conditional polynomial inequalities, simplex inequalities,
and affine implications. The generator creates its own variable names,
exact real rational coefficients, domain assumptions and conclusion; no
worker-supplied Lean commands or imports are executed. Export is explicitly
unverified. Verification runs a bounded portfolio of predefined tactics using
the operator's local Lake project, requires a successful Lean exit and the
expected theorem's axiom dependency report, and rejects sorry and dependencies
outside propext, Classical.choice and Quot.sound. It records source and claim
hashes, toolchain and manifest file hashes, tactic and command outputs.
The trusted project and executable installation must actually be checked by
the operator; manifest hashes alone do not authenticate installed binaries
or dependencies. No remote Lean toolchain is installed automatically.
A report is not consumed as a Python proof certificate, and live verification
does not automatically mark a claim established in the graph. The bridge
only checks the generated formal statement, not correspondence to an
informal conjecture. Real Lean execution needs an installed Mathlib project;
mock unit tests exercise the coordinator contract only.

Lean axiom reporting reference: https://lean-lang.org/doc/reference/latest/Axioms/


## Full-engine matched-budget evaluation

    python engine_eval.py freeze tasks.json private-references.json experiment.json --calls 4 --timeout 60 --seconds 300
    python engine_eval.py run tasks.json experiment.json worker-config.json experiment-output
    python engine_eval.py score tasks.json private-references.json experiment-output reviews.json

The new evaluator compares independent model proposals, iterative model
proposals, and the actual discovery runner with metareasoning and exact
discharge. All three receive the same worker-call ceiling and wall-time
target, reserving one call for final prose synthesis. An engine that closes
a typed target early may use fewer calls; elapsed time and actual call counts
are reported. The wall-time limit for an in-process exact adapter is soft;
overruns are explicitly counted. Token budgets and compute are not matched.
The final answers are shuffled without arm labels and must all be reviewed
against the exact task. Reference solutions are separately held and hashed,
not sent to workers. The engine's saved state is independently replayed
during scoring, with its exact certificate result reported separately from
the final prose review. Hash commitments detect changed artifacts relative
to the recorded manifest; they do not authenticate the experiment. Trusted
worker commands are not sandboxed. Keep private reference and arm-key files
away from workers and reviewers, and isolate workers externally if needed.

Use the same model/configuration for all arms, pre-register the task set and
budget, and use genuine independent mathematical reviewers. A benchmark
with historical statements is not guaranteed to be absent from model
training data. The runner does not itself establish improved performance.

## Model-free regression controls

    python core_regression.py --output core-control-results

This runs 14 transparent synthetic controls across affine, polynomial,
parameterized summation, dynamical recurrence/ideal induction, indexed
tensor, simplex and conditional theorem languages. Each goes through the
actual automatic discovery pipeline; independent audit must return the
expected proof or refutation. It saves states, state digests, pass counts,
elapsed times and any invalid observations/errors, and exits nonzero on
failure. The unit test suite includes this end-to-end control. These cases
are development controls, not blind or difficult historical problems.
