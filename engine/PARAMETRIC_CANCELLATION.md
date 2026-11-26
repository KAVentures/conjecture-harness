# Parametric cancellation and unbounded-dimension certificates

The adapter proves linear implications for signed coefficient or invariant
vectors with polynomial weights depending on an integer dimension n and a
continuous parameter t. It is not a permanent-specific theorem prover.

Canonical statement: `parametric_cone_lab.statement(spec)`, where the spec has
`start` (nonnegative integer), `rows` (constant rational inequality row
vectors), `equalities` (constant rational equality row vectors), and
`weights` (one sparse rational bivariate polynomial per vector coordinate,
terms encoded as [[n-degree,t-degree], coefficient]). The semantics are:

For every integer n >= start, every real t in [0,1], and every real vector x
with rows*x >= 0 and equalities*x = 0, weights(n,t)*x >= 0.

For example, x>=0 and x+y>=0 imply x+t*y>=0. The coefficient y can have either
sign. The solver discovers the cancellation by expressing Bernstein coefficient
vectors as nonnegative combinations of the assumption vectors. Equalities
contribute both signs. The original matrix/invariant constraints must be
proved separately; this adapter cannot assume that arbitrary coefficients
satisfy an invented prefix inequality.

## Proof rule

A certificate chooses a nonnegative integer offset d. It covers each integer
n=start,...,start+d-1 separately and covers n>=start+d by substituting
n=start+d+u, u>=0. In each region it expands in ordinary powers of u and
Bernstein polynomials in a local t coordinate. The coefficient vectors must
each be exact nonnegative combinations of the rows and both signs of equality
rows. All scalar basis factors are nonnegative, so the complete sum is
nonnegative. A binary midpoint split covers both halves of a t interval.
The replay recomputes every coefficient and checks the full cone combination
and coverage; it does not trust the simplex output. No numerical solver is used.

The finite prefix is discrete: e.g. n(n-1)>=0 for all integers n>=0 is proved
by checking n=0 and the shifted tail n=1+u. It does not assert nonnegativity
on the entire real half-line n>=0.

## Scope and limits

Up to eight signed invariants, total polynomial degree eight, sixteen
generators, sixteen prefix slices, three interval split levels and 640
distinct coefficient-cone searches. Resource exhaustion gives unknown.
Sparse exact point search may produce a genuine counterexample to the typed
implication, not to an application whose hypothesis mapping is still open.
Certificates bind the original statement in the ordinary proof graph, audit,
knowledge-bank and proof-bundle machinery.

This can automate Abel-type weighted prefix implications and dimension-uniform
bounds, but does not prove that the prefix hypotheses themselves are true.
Variable-dependent assumption rows, arbitrary-degree symbolic induction,
automatic probabilistic representations and independent benchmark results are
still future work.
