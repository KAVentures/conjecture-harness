# Global mathematical proof invention

This change consolidates the earlier stacked invention branches into a PR
against main and adds reusable exact discovery mechanisms. It does not claim
to solve a new open conjecture or to be a complete theorem prover.

## Stationary support classification

On a fixed rational transportation polytope a continuous polynomial
attains a minimum. At the positive support of a minimizer, all directions
in the nullspace of the row and column constraints are locally feasible
in both signs. First derivatives vanish; second directional derivatives
are nonnegative. Nonnegative entries and margins at most one imply the
entry upper bounds, so no additional upper-bound tangent assumption is needed.

The adapter searches identities expressing the objective as polynomial
multiples of margin and first-order equations, nonnegative multiples of
directional Hessians, and a box-nonnegative residual. Replay reconstructs
the tangent basis and every identity and requires all smaller supports
unless a direct box, empty or unique-point leaf closes the face. The symmetry
quotient uses only row/column swaps preserving margins and the exact
polynomial. A fully enumerated orbit can be replaced by its canonical
representative; orbit budget exhaustion falls back to the original support.
This extends the concavity-only mechanism but is not complete.

## All-index symbolic induction and generating functions

A rational formal power series P(z)/Q(z), Q(0) nonzero, satisfies a
constant-coefficient recurrence after the numerator degree. The solver
computes its exact initial state and searches rows R of an invariant cone
R*x>=0, including the goal coordinate, using monotonicity, growth and
Krylov candidates. Every row must be nonnegative initially, and its
pullback through the companion transition must be an exact nonnegative
combination of the rows. Induction proves every subsequent coefficient
nonnegative, not just a finite prefix. Negative coefficients are exact
counterexamples. Recurrence order is bounded to 16, not arbitrary
symbolic recurrence order.

Root structure uses the squarefree polynomial and exact Sturm variation
counts at minus infinity, zero from the right and plus infinity to
certify all roots real and nonpositive. For strict interlacing, normalize
two adjacent-degree polynomials to monic form and use a negative
Euclidean remainder chain: a=(x-c)b-k*c0, k>0, c0 monic, degree one
less than b. Interlacing follows inductively by alternating signs at
the simple roots of b and signs at infinity. A failed criterion is unknown.
Root certificates cover fixed rational polynomials, not general
parameter-dependent root families.

## Exact integral and binomial transforms

For nonnegative affine exponents a(n),b(n), the normalized beta integral
of x^j is (a+1) rising j divided by (a+b+2) rising j. Multiply the
integral of a polynomial by the positive inverse beta normalization
and common rising-factor denominator. The result is a rational
polynomial in n whose sign for every integer n>=start is checked by
the existing exact integer-sign decision adapter. Polynomial degree
is limited to eight.

For K~Binomial(n,t), E[(K) falling j]=(n falling j)*t^j, by counting
ordered selections of distinct successes. Stirling numbers expand
ordinary powers into falling factorials. This gives an exact sparse
polynomial in n,t from an input polynomial in n,K. The parametric
cone solver certifies the discrete prefix and unbounded integer tail,
uniformly for t in [0,1]. It can also return a negative expectation
witness. A scalar cone witness must have positive scalar coordinate,
so a negative product implies negative expectation. Input total
degree is bounded to four. These are all-index transforms, not
unrestricted symbolic combinatorial induction or arbitrary integral
discovery.

## Proof-obligation compression and invention from failure

The audit-aware Pareto planner retains multiple nondominated AND/OR
completion routes. It counts shared claim and bridge obligations once,
uses only replayed evidence to remove obligations, ignores exactly
refuted premises, and retains direct proof as an alternative.
A bounded beam and visit penalty affect exploration only, never truth.

A failed constrained-tensor lemma F and an exact violating array can
suggest an automatically generated nonnegative weighted-square
correction S from the target dictionary. Choose the rational coefficient
that cancels the observed deficit and propose F+cS and T-F-cS as two
new obligations. Their exact sum equals the original target T. A second
counterexample search rejects some poor proposals. Neither repaired
premise is accepted without its own proof certificate. This is a bounded
repair mechanism, not universal counterexample-guided theorem invention.

## Integrated run and evaluation

    python research_run.py --target lih-wang --output lih-wang-run
    python research_run.py --statement-file canonical-claim.txt --output result
    python research_run.py --target lih-wang --output model-run --worker-config config.json
    python -m unittest discover -s tests -p test_global_invention.py -v
    python core_regression.py --output core-controls

The optional worker config is an explicitly trusted command array;
the default makes zero model calls. The exact pass budget is checked
between passes, not a hard interruption of an individual solver.
The output contains the immutable target hash, Git revision when
available, state, audit result, and portable proof bundle if supported.
A fixed point or unverified graph is not proof. GitHub CI is configured
to run the new tests, a model-free Lih-Wang attempt and 48 transparent
cross-domain controls. CI artifacts preserve results rather than
assuming tests pass. Held-out matched-budget model evaluation and
independent mathematical review remain required for performance claims.
