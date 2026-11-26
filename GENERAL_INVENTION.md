# General theorem-invention primitives (experimental)

These are general-purpose additions, not hardcoded conjecture solvers. They
are usable directly from Python without external dependencies, except the
opt-in numerical SDP search. The square-product cone adapter is wired into
the automatic graph dispatcher and proof audit. Other results remain
candidate obligations unless their complete hypothesis mapping is verified.

## 1. Combinatorial algebra

`combinatorial_invention.centered_contractions(k)` groups the partition-lattice
expansion of k! M_k by bipartite multigraph isomorphism under independent
row/column relabeling. Any singleton index vanishes if the underlying matrix
has zero row and column sums. The unrestricted mathematical expansion is
valid for any k, but enumeration is capped (including partitions and pairs).
The empty matching is 1. The group coefficients are signed, not certificates
of positivity.

`matching_coefficients(A)` implements the weighted matching recurrence:
for a row v, Z_G(z)=Z_{G-v}(z)+z sum_{u~v} w(v,u) Z_{G-v-u}(z).
Proof: a matching either avoids v or contains exactly one incident edge.
This applies to arbitrary bipartite weighted graphs, even with signed rational
weights. The finite evaluator uses memoized used-column sets; it is not an
unbounded induction prover. `recurrence_residual` independently checks a
first-row decomposition on a specified matrix.

## 2. Inequality invention and PSD verification

Sparse polynomials are dictionaries from exponent tuples to rational
coefficients (Python int or Fraction). Given explicit nonnegativity
hypotheses and arbitrary polynomial atoms, the cone search proposes products
of up to two hypotheses times a squared atom, or a constant. Exact phase-I
simplex chooses rational weights; the replay checks the polynomial identity
and every nonnegative weight. Example: x(1-x)>=0 follows from x>=0 and 1-x>=0.

Supply both signs of an equality as nonnegativity assumptions when needed.
All assumptions must hold on the intended domain; the certificate proves a
conditional result only. Search caps and dictionary choices are incomplete.

`replay_gram` checks a supplied rational Gram matrix using exact LDL
factorization and polynomial identity replay, including singular matrices.
It can be used after external numerical SDP discovery and rational recovery.
The optional sdp_discovery.search uses CVXPY to propose a Gram matrix,
then attempts rational recovery. It accepts only exact replay, not numerical
solver status. Install CVXPY separately if desired; the default run does not
require it.

## 3. Affine extremal structure

`affine_extremal_invention` generates rational nullspace directions for an
affine equality system on the unit box, tries combinations, and attempts a
certificate for the negative second directional derivative on the entire
box. If verified, the objective is concave along each feasible segment;
a minimum exists at one of its two endpoints. A nonzero direction on a
compact box hits a boundary at both endpoints unless the segment degenerates.
`endpoints` computes the exact interval. The result is a conditional
boundary-reduction mechanism, not a classification of global extremizers.
Face coverage, dimension reduction and any face inequality must be proved
separately. The automatic cone search currently supports up to six box
coordinates; the nullspace calculation supports up to 32.

## 4. Theorem recombination and strategy

`theorem_network.plan` retains multiple inclusion-minimal sets of unresolved
obligations for explicitly instantiated theorem rules. Shared obligations
are counted once; rule proofs (including source correspondence) are separate
obligations. It rejects self-dependency and does not close circular routes.
Only independently audited IDs should be supplied as verified. This is
a bounded planner, not a theorem parser, proof audit or formal verifier.
Search uses subset pruning and reports cap saturation; weights rank surviving
routes, not calibrated proof difficulty. The metareasoning diagnosis now
exposes alternative obligation plans based on independently replayed graph evidence.

`theorem_network.evaluate` checks matched task/budget allocations and
summarizes externally reviewed results. It does not authenticate reviewers,
run models or replace historical_eval.py. No improvement in open-problem
solving has been measured.

Run focused tests: python -m unittest discover -s tests -p test_general_invention.py -v

## Next integration gates

- Typed graph dispatch for additional combinatorial and extremal certificates.
- Broader SDP bases, constrained SDP multipliers and more robust rational recovery.
- Symbolic partition-family induction and general indexed inequality search.
- Recursive affine face classification with checked coverage.
- Semantic theorem instantiation and cross-representation invention.
- Full-engine matched-budget experiments with separate qualified reviewers.

Failure to find a certificate is unknown, never evidence of falsity.
