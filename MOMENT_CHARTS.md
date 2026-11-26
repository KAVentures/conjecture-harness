# Dimension-free moment charts

This adapter handles nonlinear polynomial inequalities in the first three
moments of arbitrary probability measures on [0,1], and (via a one-way
transfer) symmetric polynomial inequalities on simplices of *every* finite
dimension. No enumeration of coordinate multiplicities is required.

Canonical input: {"domain":"probability" or "simplex","terms":[...]}.
The exponents refer to (m1,m2,m3); weighted degree <=6 with weights (1,2,3).
For probability claims m_j=E[X^j]. For simplex claims m_j=sum_i x_i^(j+1)
where the number of coordinates is arbitrary, all coordinates are
nonnegative, and sum_i x_i=1. Example:

    {"domain":"simplex","terms":[[[0,1,0],1],[[2,0,0],-1]]}

This asserts p3 >= p2^2 for all dimensions. Run
`python moment_chart_lab.py spec.json` or use the canonical proof graph.

## Exact chart and proof

Let a=m1. Necessarily a^2<=m2<=a. For 0<a<1 set
b=(m2-a^2)/(a*(1-a)) in [0,1], q=a+(1-a)*b, r=a*(1-b).
Weighted Cauchy-Schwarz, with weights X and 1-X respectively, gives

    m3 >= m2^2/a
    m3 <= m2 - (a-m2)^2/(1-a).

The two endpoints are attained by the probability laws supported on
{0,q} with mass a/q at q and on {r,1} with mass (1-a)/(1-r) at r.
Both have first moment a and second moment a*q; the remaining masses
make total mass one. Their third-moment difference simplifies to
a*(1-a)*b*(1-b). Thus every possible moment triple, and only such a triple,
has the polynomial representation

    m1 = a
    m2 = a*(a+(1-a)*b)
    m3 = a*(a+(1-a)*b)^2 + c*a*(1-a)*b*(1-b)

for a,b,c in [0,1]. For a=0 or 1 the measure is concentrated at that
endpoint and the formulas remain valid; if the width vanishes any c works.
Conversely a mixture of the lower and upper two-atom laws with weights
1-c and c realizes each chart point. All polynomial substitutions and
rational atomic realizations are explicitly checked in the adapter.

For simplex claims, take the law that puts mass x_i at x_i. Its total
mass is one and its moments are the required shifted power sums.
The chart is therefore a sound *relaxation* of the simplex domain.
It is not asserted that every moment triple comes from such a simplex.
A negative chart point can refute a probability claim, but a simplex
refutation must supply actual coordinates with sum one. Replay enforces
this distinction.

## Certificates and limits

A positive certificate is a complete exact rational Bernstein box cover
of the pulled-back polynomial, with both children at every split.
Negative probability certificates reconstruct a feasible rational measure.
Negative simplex certificates check actual simplex vectors directly.
Search is bounded and may return unknown even for a true statement.
The algebraic chart is dimension-free; the current polynomial degree,
term count, subdivision budget and counterexample search are not complete.

The proof graph, auditor, knowledge bank, portable bundles and model
prompts register this typed domain. Transfer to arbitrary matrix
invariants requires a separate valid mapping; no Lih-Wang resolution,
matrix extremizer theorem, or benchmark performance gain is asserted.
