# General invention deep sweep

The core discovery engine gains three typed exact proof families and two
audited recombination bridges. These are bounded research primitives rather
than an autonomous solution of Lih–Wang or another open conjecture.

## 1. Constrained, dimension-free tensor inequalities

`constrained_tensor_lab.statement` extends the existing indexed algebra
language with nonnegative array symbols and declared zero-marginal slots of
nonsymmetric arrays. A contraction vanishes when, after delta elimination,
a summed index occurs in exactly one slot and that slot has a zero marginal.
This is justified by summing that index first. Repeated indices do not vanish.

The certificate is a positive combination of sums of weighted squares.
Each weight is a product of entrywise nonnegative symbols or Kronecker
deltas, using only free indices; the square's private summation indices
are renamed independently in each factor. Expansion, delta elimination,
singleton marginal cancellation and canonical dummy-index normalization
must reproduce the original target exactly. The solver invents square
candidates from factor splits and uses a rational cone to select weights.
All dimensions are covered by the identity. Caps on factor count, index
count, degree and cone columns make the search incomplete.

## 2. Sharp signed-cone bounds

`sharp_ratio_lab.statement` encodes rows*x>=0, equalities*x=0
implying f*x>=k*d*x, for arbitrary real signed x. A positive combination
of rows and both signs of equality rows must equal f-k*d.
`discover(spec)` enumerates independent rational dual bases containing d
and proposes k. A separately reconstructed primal point with d*x=1 and
f*x=k proves that no larger k can satisfy the implication. A dual bound
without attainment is not labeled sharp. Negative witnesses are rechecked
on the original cone. The search may miss violations with d*x<=0,
unbounded optima, or sharp constants outside the bounded enumeration.

## 3. Transportation support-face extremizer reduction

`transport_face_lab.statement` describes rectangular nonnegative arrays
with fixed rational row/column margins in [0,1] and a polynomial objective.
The margin restriction implies every entry is in [0,1]. It searches
alternating four-cycle directions and simple longer support cycles.
Each proposed direction preserves both margins; replay checks this
explicitly. A nonzero such direction has both signs, and maximal
segments in that direction reach a zero entry at either endpoint.
If the objective is concave along the segment (certified by a rational
Bernstein cover of minus its second directional derivative on the support
box), its minimum occurs at one of the endpoints. Replay requires
every moving coordinate's zero face, not just a chosen favorable face.
The support strictly decreases, so the certificate DAG is well-founded.
Leaves use exact infeasibility/unique-point elimination or a checked box
certificate. Forest supports have at most one feasible point, but the
solver also handles other unique-point leaves. No assumed global
permutation-matrix or block extremizer classification is used.

## 4. Audited theorem recombination

`tensor_recombination` synthesizes a positive combination of previously
audited constrained or unconstrained tensor inequalities and new weighted
squares. The checker verifies source tensor declarations and inclusion of
source nonnegative/marginal hypotheses in the target context; stronger
source assumptions cannot transfer to a weaker target.

`transport_moment_bridge` instantiates audited probability-moment or
simplex-power-sum bounds on each positive-margin row/column after dividing
by its exact margin. Fixed-dimensional source theorems require an exact
dimension match. Source hypotheses are preserved by normalization, and
size-biased weights give the moment interpretation. A nonnegative
combination of instances plus manifestly nonnegative monomials must
reproduce the target polynomial. The search and proof audit use only
audited sources; each source remains a separate proof premise.

All three direct certificates are registered in the graph dispatcher,
auditor and portable proof systems. Both bridge families are reserved
against worker impersonation and independently replayed by proof_audit;
a valid implication does not prove its premises. Recombination is automatic
for supported live goals. No arbitrary semantic theorem transfer is
claimed. Further work includes automatically discovering application
encodings, unrestricted dimension-parameterized tensor degree and
multiplicities, and independently reviewed held-out evaluations.
