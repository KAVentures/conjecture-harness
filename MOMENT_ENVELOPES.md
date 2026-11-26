# Sharp moment envelopes and extremal distributions

This adapter proves inequalities for every finite probability distribution on
[0,1], irrespective of its number of atoms (and the same proof extends to
probability measures by integration). It is a reusable conditional inequality
engine, not a solution to a particular open conjecture.

## Input and commands

A canonical claim is made by `moment_envelope_lab.statement(spec)`. Its
`assumptions` are polynomial expectations with relation zero or nonnegative,
`objective` is a polynomial, and `bound` a rational lower bound. Terms use
[[degree], coefficient]. Example: mean 1/2 implies second moment >= 1/4.

    {"assumptions":[{"relation":"zero","terms":[[[1],1],[[0],"-1/2"]]}],
     "objective":[[[2],1]],"bound":"1/4"}

    python moment_envelope_lab.py spec.json
    python moment_envelope_lab.py spec.json --discover

Negate the objective for upper bounds. Arbitrary-size vectors of bounded
entries can be encoded as their empirical distributions after explicitly
proving the mapping and moments; arbitrary matrix interactions cannot be
discarded without a separate argument.

## Mechanism and exact replay

For assumptions E[h_i]>=0 or E[h_i]=0, synthesize rational multipliers
lambda_i (nonnegative for inequalities, unrestricted for equalities) so that
q(x)=f(x)-bound-sum lambda_i h_i(x) is nonnegative on [0,1].
The search proposes envelopes with a rational cone of nonnegative endpoint
powers and squared interior factors. The checker recomputes q and substitutes
x=u/(1+u); multiplying by (1+u)^degree yields a polynomial on u>=0, checked by
the existing exact Sturm sign classifier. Continuity covers x=1. Integrate
the pointwise inequality to prove the claimed bound; no discretization enters
the dual proof.

A separate rational atomic search proposes distributions on an adaptive grid,
including linear-moment roots. The checker requires positive masses summing
to one, exact moment feasibility and strict violation for refutations.
A grid failure is unknown. A bound is sharp only if a feasible atomic
distribution attains the independently replayed dual bound. Every attaining
distribution must be supported on the zeros of q, with all positively weighted
inequality assumptions active. This is a necessary equality characterization,
not an assertion that the witness is unique.

The discover mode tries the objective of a feasible atomic distribution as a
candidate sharp bound, then bisects when both a certified lower bound and a
feasible upper bound are available. Each endpoint has separate evidence.
It may return a bracket or unknown; exact attainment is not guaranteed.

## Limits

Degree <=8, <=6 moment assumptions, bounded rational coefficients, <=24 atoms
in a witness, bounded cone and grid search. No floating point certification.
The graph adapter, certificate registry, knowledge bank and proof bundles
bind certificates to the exact original canonical claim. Sharpness metadata
must be rechecked with sharpness(), not inferred from a proof flag. This is
a general moment abstraction: constraints involving correlations, arbitrary
support domains, higher-dimensional moments and automatic application-specific
theorem mappings remain open. No benchmark performance gain is asserted.
