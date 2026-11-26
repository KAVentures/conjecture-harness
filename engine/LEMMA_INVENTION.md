# Target-only lemma invention

The new exact sparse-square extraction operator constructs additive proof obligations from a bare typed polynomial nonnegativity target, without a user-supplied auxiliary lemma, prior counterexample or model call.

For a positive even monomial d x^(2u) and another target term c x^e, consider a square w(x^u + (c/(2w))x^(e-u))^2 for finitely many rational weights w derived from d. If the exponent is admissible, this square matches the cross term exactly. The other diagonal monomial need not have positive coefficient in the original polynomial: the algorithm subtracts its contribution from the residual. This is the crucial difference from the fixed Gram support heuristic. The residual is sent to the existing exact proof adapter. The original coefficient sum and both universal certificates are replayed. Negative points and unknown outcomes cannot establish either lemma.

The automatic runner tries one bare reachable multivariate target per discharge pass after direct polynomial proof search abstains. It proposes and certifies two nonnegative summands and installs an accepted additive edge atomically. It preserves the exact original statement, coefficients, both certificates, and evidence dependencies. Existing proof routes are preserved; this conservative implementation does not yet recursively split unsuccessful residuals. Candidate search is bounded (96 by default), and unsuccessful search is unknown. No model-generated source executes.

## Reproduce

    python invention_benchmark.py
    python -m unittest discover -s tests -p test_lemma_invention.py -v

The original direct solver abstained on all 24 development controls and 12 additional parameter controls, drawn from the same selected family a(x^2-y^2)^2 + (bxy+cy)^2. The invention operator recovered two exact nonnegative summands for all 36 expanded inputs. Each successful decomposition was replayed. These are deliberately selected elementary same-family controls, not independently held-out problems, general nonlinear completeness, novel theorems or live-model performance. Fourteen focused tests passed, including tampering, domain mismatch, abstention and false controls.
