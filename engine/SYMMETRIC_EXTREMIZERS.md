# Structural extremizer discovery: certified few-level reductions

This adapter handles symmetric polynomial inequalities on an n-dimensional
probability simplex. It uses power sums p_j=sum_i x_i^j for j=2,3,4, with p1=1.
The objective F(p2,p3,p4) has weighted degree <=6. All coefficients are rational.
It is not a reduction theorem for arbitrary matrices.

Example spec: {"dimension":12,"terms":[[[0,1,0],1],[[2,0,0],-1]]}
asserts p3-p2^2>=0 on the entire 12-dimensional simplex. Run
`python symmetric_level_lab.py spec.json` or use the canonical statement
in a model-free discovery graph.

## Reduction theorem and proof

Let k be the largest active power-sum index, with k=1 for a constant.
Continuity and compactness give a minimum of F. Restrict to the positive
coordinates of any minimizing point, keeping the zero coordinates fixed.

If the derivative of F with respect to p_k is a nonzero constant, the
Lagrange multiplier condition for sum x_i=1 is
sum_{j=2}^k j*(partial F/partial p_j)*x_i^(j-1) = lambda for each
positive coordinate. This is a polynomial of degree exactly k-1 in x_i,
so every minimizer has at most k-1 distinct positive values.

Otherwise choose, among all minimizers, one maximizing p_{k+1}, which exists
by compactness. If it has k+1 or more distinct positive coordinate values,
choose k+1 coordinates with distinct values. The Jacobian of the map from
these coordinates to (p1,...,p_{k+1}) has entries j*x_i^(j-1) and nonzero
determinant (a Vandermonde determinant times a nonzero constant). By the
inverse function theorem, the first k power sums can remain exactly fixed
while p_{k+1} increases, in a sufficiently small neighborhood preserving
positivity. The objective remains fixed, contradicting maximality.
Thus some minimizer has at most k distinct positive values. For a constant
one may take a simplex vertex.

This proof applies in arbitrary finite dimension. It does not assert that
every minimizer is few-level in the secondary-extremum case. The adapter
limits the input dimension and chart count for computational reasons.

## Cover every reduced configuration

For each number r up to the justified bound, enumerate all positive
integer multiplicities m1<=...<=mr with sum <=n. Relabeling levels allows
this ordering without imposing an ordering on the coordinate values.
Set y_i=m_i*x_i. Then y is in the r-simplex, and
p_j=sum_i y_i^j/m_i^(j-1). Every few-level minimizer is covered.
Allowing coincident or zero levels in a chart is harmless: these points
lift to legitimate simplex points as well.

Replay reconstructs the exact list of multiplicities; missing or changed
charts invalidate a certificate. One-level charts are constant checks;
two-level charts use y=(t,1-t) and exact projective Sturm classification;
three- or four-level charts use bounded rational simplex Bernstein covers.
A negative rational chart point lifts back to the full original simplex and
is rechecked directly. Finite survival and coverage budget exhaustion are
not proof. Current chart budget is 384, so some large fixed-dimensional
claims remain unknown despite the general reduction theorem.

The integration uses the canonical proof graph, audit registry, knowledge
bank, portable proof bundles and research prompt. No claim is made that
this solves Lih–Wang, classifies doubly stochastic matrix extremizers, or
improves benchmark results without evaluation. Future work: parameterized
multiplicities, higher weighted degrees, symmetry under multiple coordinate
groups and certified matrix transportation-polytope reductions.
