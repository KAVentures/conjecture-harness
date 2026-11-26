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
