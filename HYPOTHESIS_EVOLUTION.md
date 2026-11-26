# Counterexample-guided mathematical hypothesis evolution

This module automatically repairs a restricted class of failed auxiliary polynomial inequalities. It is a mathematical search operator, not a general conjecture generator. It does not change the frozen target.

Given target T(x) >= 0 and a failed auxiliary P(x) >= 0 with replayed exact counterexample x0, construct c = -P(x0) > 0 and propose two new claims:

    A(x) = P(x) + c >= 0
    B(x) = T(x) - A(x) >= 0

The old counterexample no longer refutes A, but A is not necessarily true. B is the compensating obligation: weakening the original lemma cannot silently weaken the target. Check the exact identity T = A + B, identical variable order and domain, and both inequalities separately. Only the conditional bridge is accepted from the identity. The target closes only if both premises are established. The failed claim and witness remain in the graph; no generation reward is given for unproved new claims. The scheduler may credit a verified bridge as distinct from established premises.

The adapter rejects trivial constant splits, equivalent repetitions, known-refuted replacement claims, invalid point evidence, mismatched domains and circular dependencies. It attempts at most two new repairs per discharge pass and does not recursively repair its own generated edges. Ordinary mathematical reasoning can propose more variants. The sum-composition adapter also verifies compatible independently proposed polynomial decompositions, without a repair step. No arbitrary model code is executed.

## End-to-end control

T = 4x^4 + 4y^4 - 4x^2 y^2 + 4xy^2 + y^2.

The existing direct polynomial solver returns unknown on this control. Supply a candidate auxiliary P = 4(x^2-y^2)^2 - 1. Its exact witness (0,0) refutes P >= 0. The repair operator generates A = 4(x^2-y^2)^2 and B = (2xy+y)^2. The coefficient bridge T=A+B is independently checked and both nonnegative summands are established by the existing rational SOS adapters. Two discharge passes close the original proof graph, without a model call. The control was selected to illustrate the limitation of the direct solver, not drawn from a held-out suite; the candidate auxiliary was supplied by the developer, not autonomously discovered from the bare target.

Run:
    python -m unittest discover -s tests -p test_hypothesis.py -v

The control and all 13 new tests pass locally. All 183 discovered regression tests passed across two runs (171 completed in a timed-out full run, 14 passed in a follow-up, two overlapping). No live-model performance, general hypothesis generation or novel open-conjecture result is asserted.
