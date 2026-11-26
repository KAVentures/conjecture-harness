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

The theorem matcher now considers up to twelve distinct conclusion maps under a shared candidate budget, screens every instantiated hypothesis using bounded exact solvers, rejects maps with replayed refutations or recorded refuted premises, and prefers maps with fewer unresolved obligations. Screening is heuristic selection only; a chosen source theorem and its instantiated assumptions must still be established by the graph and independently audited. This avoids committing to the first syntactically matching but mathematically inapplicable substitution.


## Exact univariate sign decision

The univariate adapter independently decides rational polynomial
nonnegativity on the real line or nonnegative half-line, for degree at most
eight, subject to a coefficient growth limit. It extracts the product of
square-free factors of odd multiplicity using exact Euclidean division and
gcd. Sturm variations at minus infinity or the right-hand limit at zero,
and at plus infinity, count the odd-multiplicity roots strictly inside the
domain. A nonzero polynomial is nonnegative exactly when its leading
coefficient is positive and this count is zero. Even-multiplicity roots
do not change sign; zero is allowed as a boundary root on the half-line.
A negative leading coefficient or an odd interior root proves existence of
a negative value. This latter certificate is a mathematical refutation,
not necessarily an explicit rational witness. The separate sturm-sign
certificate is independently recomputed by the audit, can be transferred
as checked knowledge, and is never mislabelled as a sum-of-squares proof.
The ordinary point-search API is unchanged. The model-free integration
suite now has sixteen controls. The exact factored-domain test checks
500 generated polynomials on both domains against their known root
multiplicities; additional tests cover irrational roots and boundary cases.


## Exact univariate semialgebraic implications

The sign-cell adapter decides conditional polynomial inequalities in one
real variable by forming the square-free union of all roots of the
assumptions and conclusion. A Cauchy bound and exact Sturm bisection
isolate distinct real roots in rational intervals. Open sign cells have
rational representatives; at an isolated algebraic root, gcd and Sturm
counts determine which polynomials vanish and the sign of the others.
The nonnegative-domain endpoint zero is tested separately. The implication
holds exactly when no feasible sign cell or root makes the conclusion
negative. This handles equality-only feasible sets with irrational points,
not accessible to rational-grid search. A refutation contains either an
exact rational representative or an isolating interval and sign vector;
the latter identifies an algebraic root of the reconstructed union
polynomial, not an arbitrary floating-point approximation. Replay
reconstructs the classification from the original statement.

The search abstains on root-union degree above 32, excessive coefficient
growth or the 1024-split limit. It does not claim general multivariate
quantifier elimination. The sign-cell proof rule is separate from the
conditional SOS rule, and participates in the proof audit, portable facts
and proof bundles. The model-free controls now include eighteen cases;
800 randomized factored-domain comparisons test the sign-cell classifier
against independently generated exact representatives.


## Projective sign decision for homogeneous binary polynomials

For two-variable homogeneous inequalities and conditional theorems, each
polynomial can have a different homogeneous degree. On the chart y>0,
write (x,y)=y(t,1). On y<0 write (x,y)=|y|(t,-1). Positive scaling by
|y| raised to the polynomial's degree preserves its sign and zero set,
including for odd degrees. Both charts are reduced to univariate
semialgebraic implications, and the axis y=0 is checked at the origin and
both unit directions. The nonnegative orthant needs only the positive
chart and nonnegative axis. This gives an exact decision for supported
homogeneous binary implications, subject to sign-cell degree and resource
limits. Nonhomogeneous two-variable claims are not covered by this rule.

For two-coordinate simplex inequalities, the same engine substitutes
(x,y)=(t,1-t) and checks 0<=t<=1 using sign cells. This covers the full
segment rather than relying on a finite subdivision budget. Refutations
may identify a rational point or an isolated algebraic root on a chart.
All translations and classifications are independently recomputed by the
proof audit. The model-free integration suite now has twenty controls,
and the projective classifier has 500 exact factored-domain comparisons.

## Historical public pilot

See [evaluation/historical_v1](evaluation/historical_v1/README.md) for a
seven-task previously settled pilot corpus, including a known inequality,
two related explicit refutations and four major historical conjecture
formulations. It has separate references with known proofs or source
locators. It is not a training-data holdout, representative benchmark or
evidence of measured improvement. Run the full-engine comparison under a
configured worker and independent blinded review before reporting results.


## Equational theorem discovery and finite algebra countermodels

equational.py handles universally quantified equations over arbitrary
nonempty single-sorted algebras, with at most four variable names, five
operation symbols (arity zero, one or two), eight axiom equations and
terms of at most 24 nodes. Operations need not be arithmetic or associative
unless stated. A term is a variable string or [operation, arguments...].
Bidirectional rewriting explores substitutions into both sides of axioms,
including bounded choices for variables absent from the matched side.
A proof certificate lists the exact axiom, direction, position and full
substitution for each rewrite. Replay independently checks every
replacement and the final syntactic equality. The search is incomplete:
no general completion, unbounded paramodulation or decision claim.

Countermodel discovery searches two- and three-element operation tables
under a bounded budget. Replay verifies every universally quantified
axiom over every valuation of its variables, then checks the specific
conclusion-violating assignment. A finite countermodel refutes a universal
equational implication; finite survival never proves it.

    python equational.py algebra.json

Example: {"variables":["x","y"],"operations":{"m":2},"axioms":[[["m","x","y"],"x"]],"conclusion":[["m","x","x"],"x"]}.

The runner, audit, portable knowledge, proof bundles and worker prompts
recognize this language. The model-free controls now have 22 cases.
This is a general algebraic mechanism, not a proof of the Robbins
conjecture or a complete automated equational theorem prover.


### Critical-pair lemma invention

critical_pairs.py overlaps reducing or equal-size orientations of axioms,
renames their variables apart, and unifies overlapping terms using an occurs
check. The two reductions of a shared instance give a new equation with
a two-step original-axiom certificate. Candidate equations are independently
replayed, deduplicated and ranked by term size. The fallback solver uses
these lemmas as temporary rewrite macros under the original rewrite budget.
Any successful chain must expand back into original-axiom rewrites and
replay on the original claim; derived lemmas are never trusted axioms.
This is a bounded one-round critical-pair search, not full Knuth–Bendix
completion or a general equational decision algorithm.

    python critical_pairs.py algebra.json


## Fixed-graph structural proof search

graph_structure.py searches independence and clique upper bounds for one
specified simple graph of at most 48 vertices. Clique bounds are independence
bounds of the complement. The exact proof DAG uses clique partitions,
disconnected component sums, adjacent closed-neighborhood domination
(N[u] contained in N[v] permits deleting v), and the include/exclude
recurrence for independent sets. Each reduction preserves the stated upper
bound; replay checks the original graph and every local rule in topological
order, rather than rerunning the heuristic search. A violating independent
set (or clique in the original graph) refutes an upper bound. The solver
returns unknown on its node limit; finite examples cannot establish an
arbitrary-order graph conjecture. The runner, audit, portable facts and
proof bundles support this adapter. The test suite includes 640 comparisons
against direct subset enumeration and 24 full-engine controls in total.

    python graph_structure.py graph-claim.json

Example: {"n":5,"edges":[[0,1],[1,2],[2,3],[3,4],[0,4]],"invariant":"alpha","upper":2}.


## Universal linear graph consequences

graph_consequences.py handles the existing graph_lemma canonical language:
arbitrary finite simple nonempty graphs, minimum order, optional connected
or triangle-free hypotheses, and integer affine inequalities in
(n,m,alpha,omega,delta,Delta). It uses the following elementary theorem
basis, not finite graph survival:

| Row | Mathematical justification |
|---|---|
| order | Stated lower bound on graph order. |
| edge-nonnegative | Edge count is nonnegative. |
| independent-singleton, clique-singleton | A singleton is independent and a clique. |
| degree-nonnegative, degree-order, degree-simple | Degrees are nonnegative, minimum <= maximum <= n-1. |
| independence-order, clique-order | Both sets are subsets of the vertex set. |
| clique-independent-intersection | A clique and independent set intersect in at most one vertex. |
| independent-min-degree | Each vertex of an independent set has degree at most n-alpha. |
| clique-max-degree | A clique vertex has at least omega-1 neighbors. |
| max-degree-edges | All edges at a maximum-degree vertex are distinct. |
| degree-extremes | The degree sum includes a minimum- and maximum-degree vertex (distinct if degrees differ; if equal and n>=2 choose distinct vertices; n=1 gives zero). |
| edge-deletion-independent | Choose one endpoint of each edge, producing a vertex cover of size at most m. |
| clique-edges | A clique contains at least omega-1 edges. |
| handshake-min | 2m >= actual order times delta >= stated minimum order times delta. |
| connected-spanning-tree | A connected graph has a spanning tree and at least n-1 edges. |
| connected-min-degree, connected-edge-clique | A connected graph of order >=2 has no isolated vertex and contains an edge. |
| triangle-free-clique | A triangle-free graph has clique number at most two. |

A selected subset of at most twelve applicable rows is combined by the
exact affine certificate checker (nonnegative multipliers give a
contradiction to the strict negation of the target). The independent audit
reconstructs the rows from the exact graph statement, not from claims in
the proof certificate. This is a sufficient theorem basis, not a complete
description of all graph invariant relations. Failure to derive a bound
is unknown, not a counterexample. Finite checks of the theorem basis are
regression controls, not proofs of these universal facts.

    python graph_consequences.py graph-lemma.json

There are now 26 full-engine controls, including universal graph results.


## Multivariate equality-ideal reasoning

ideal_consequences.py performs a bounded Buchberger-style search over the
rational polynomial ring in up to four variables. It keeps an explicit
vector of original-generator multipliers for every basis polynomial.
S-polynomial construction, monic normalization and exact reduction
preserve those identities. The search caps degree at 12, sparse support
at 256 terms, basis size at 20, and processes at most 96 pairs by default.
It may skip expensive pairs, so a failed reduction is not an ideal
nonmembership result and the returned basis is not necessarily a Groebner
basis.

The conditional theorem adapter uses only equality hypotheses as ideal
generators. Three sufficient certificates are supported: 1 belongs to
the ideal (the hypotheses are inconsistent); the target is congruent to
a certified nonnegative SOS residual; or the second or third power of the
target belongs to the ideal (the target vanishes at every common zero).
The checker multiplies original generators by the supplied rational
polynomials and compares exact coefficients. It never trusts a purported
basis or a failed search. Additional inequality hypotheses may restrict
the domain further, but are never treated as ideal generators. This is
not general radical membership, real Nullstellensatz completeness or
multivariate quantifier elimination.

Example: xy=1 and y^2=1 imply x-y>=0 because
x-y = y(xy-1) - x(y^2-1). The engine can discover this identity through
an S-pair. The proof audit, portable knowledge, and proof bundles support
the new rule. The integration suite now has 28 controls.


## Weighted AM-GM nonnegativity certificates

amgm_certificates.py searches sparse polynomial decompositions beyond
ordinary sums of squares. A circuit consists of positive monomials
a_i x^alpha_i and one negative monomial -b x^beta, with positive
integer weights w_i, W=sum w_i, and sum w_i alpha_i = W beta.
On the nonnegative orthant the positive terms are nonnegative; over
all reals their exponents must be even. Apply weighted AM-GM to
a_i W/w_i times the absolute monomials, and compare the exact rational
product of (a_i W/w_i)^w_i against b^W. This proves the circuit is
nonnegative, including when a target exponent is odd. At zeros the
same inequality holds by continuity. The replay subtracts each
certified circuit from the original polynomial and checks the remaining
monomials are nonnegative on the declared domain. It never trusts a
numerical logarithm or floating-point optimizer.

Search finds positive rational barycentric weights on affinely independent
support subsets, then allocates positive coefficients by exact rational
arithmetic. The total weight is capped at 32 and at most 24 circuits are
allowed; greedy allocation and subset search are incomplete. An unknown
result is not a refutation. The classical Motzkin polynomial
x^4 y^2+x^2 y^4+1-3x^2 y^2 is a known non-SOS example, certified by
three equal weights. No novelty is claimed. The exact AM-GM proof is
separate from the SOS certificate language. The model-free integration
suite now includes 29 cases.
