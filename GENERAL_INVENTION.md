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


## Additional symbolic and extremal tools

`shape_coefficient(columns)` calculates a specified singleton-free
multigraph contraction coefficient at arbitrary edge order (resource caps
apply), without enumerating all labeled partitions. If its multiplicity
matrix is H, its coefficient in k! M_k is

    k! * product_v [(-1)^(deg(v)-1) (deg(v)-1)!]
       / (|Aut_bipartite(H)| * product_ij H_ij!).

Reason: assign k distinct labels to edge slots, then quotient by permutations
of parallel edges and bipartite vertex automorphisms. Each labeled pair of
partitions has the same product of partition Möbius weights. This formula is
dimension-free; it does not imply the sign of a sum of contraction values.
The exact search counts degree-preserving row permutations and matching
column permutations. Exhaustion of the automorphism budget raises an explicit
error rather than silently using an approximate count.

`box_bernstein` uses exact tensor Bernstein coefficients and a checked
midpoint splitting tree over a unit box. All leaves must be nonnegative;
the binary split covers the original box. A negative Bernstein coefficient
is not a negative point. The grid and tree are bounded.

`transportation_directions` generates elementary four-edge cycle moves
preserving row and column sums. `search_box_directions` verifies concavity
via exact Bernstein certificates, including arrays beyond the six-coordinate
cone limit when sparsity permits. This is a local-to-boundary reduction
primitive, not a proof that every extremizer belongs to a proposed family.


## Index-dependent induction

`inductive_invention` supports recurrences x(n+1)=M(n)x(n)+b(n)
with rational polynomial coefficients and simultaneously proposed affine
state inequalities c(n,x(n))>=0. Coefficients are ascending powers of n.
It synthesizes a symbolic identity for every next-step inequality using
nonnegative linear combinations of binomial(n,k) times existing invariants
and binomial(n,k) alone. For integer n>=0 all these factors are
nonnegative. Replay checks the base state and each exact pullback identity,
establishing the invariants by simultaneous induction for every n>=0.
The state dimension and polynomial degree are bounded but n is not sampled.
A small candidate generator tests simple polynomial lower bounds; arbitrary
nonlinear invariant invention remains outside this adapter.


## Recursive affine-box proof and automatic induction

The canonical `affine_face_lab.statement` claim asserts p(x)>=0 for
every x in the unit box satisfying specified rational affine equalities.
The proof engine restricts to faces, checks inconsistency or unique-point
leaves by exact Gaussian elimination, and tries direct box Bernstein
certificates. Otherwise it searches feasible nullspace directions with
a checked nonpositive second derivative. Each endpoint of a maximal
segment in that direction is on a face obtained by fixing at least one
moving coordinate to 0 or 1. Replay therefore requires **both** faces of
**every** moving coordinate; recursive coverage, not an asserted extremizer,
closes the proof. A face DAG avoids duplicate checks. The dimension, search
budget and certificate size are bounded.

`inductive_lab.statement` asserts a single affine state inequality for
all nonnegative integer indices of a specified affine recurrence. Backward
pullbacks, coordinate signs, and pairwise differences generate potential
auxiliary invariants. All auxiliary invariants are proved simultaneously
with the goal, including their initial conditions. The certificate binds
to the original recurrence, initial state and goal; auxiliary hypotheses
are never presumed. Both adapters run automatically in the proof-state
runner, use reserved observation IDs, and are independently replayed by the
existing proof auditor. The chat research prompt now includes both exact
claim syntaxes. Failure to find a certificate remains unknown.


## Dimension-free tensor inequality invention

`tensor_sos_lab` adds inequalities (not merely identities) on arbitrary
real tensors in every positive integer dimension. Its certificates write
a target contraction as a positive rational combination of summed squares
of partially contracted expressions. Free indices are summed outside
the square; each copy of a private index is independently renamed inside
the product. Unused free indices contribute an explicit dimension factor.
Expansion and exact alpha-renaming/symmetry normalization must reproduce
the original target. This verifies the inequality for all dimensions,
not just finitely many matrices. Candidate squares are generated by
factor bipartitions, then chosen by exact rational cone search. For
example the Cauchy--Schwarz deficit is half the sum over i,j of
(A_i B_j - A_j B_i)^2. The certificate language retains the existing
indexed algebra's bounded number of factors and dummy indices; it does
not prove arbitrary high-order tensor inequalities or assume nonnegative
matrix entries. The solver, claim syntax, reserved certificate namespace
and read-only audit are integrated into the runner.


### Exact early falsification

All three new canonical adapters now search for counterexamples before
attempting proof. Affine-box search fixes selected coordinates and solves
the original rational equalities; a negative witness must replay every
original equality and bound. Recurrence search reconstructs the exact
finite orbit from its initial state and verifies negativity at a supplied
index. Tensor search evaluates original contractions on exact small
arrays satisfying all declared symmetries. Each refutation is checked by
the registered auditor. Failed finite searches remain unknown.


## Joint theorem instantiation and recombination

`theorem_recombination` searches exact positive rational combinations
of multiple polynomial theorem instances, including instances of the same
source under different substitutions. Unlike single-theorem transfer,
the source conclusion need not be proportional to the goal: intermediate
terms may cancel. Context constraints can supply additional terms. Search
prioritizes sources and hypotheses already independently replayed.
Every source theorem and every nontrivial substituted hypothesis is
still an explicit proof obligation. Context-only discharge is limited to
positive multiples of inequalities, either sign of equalities, and
manifestly nonnegative monomials. Nonnegative-domain source images must
satisfy the existing exact domain-preservation rule. The audit checks
the entire combination before propagating proof closure. Literature
extraction can now try joint theorem applications with source-bound
provenance when individual transfer is insufficient. Search is bounded
and cannot semantically formalize arbitrary papers.
