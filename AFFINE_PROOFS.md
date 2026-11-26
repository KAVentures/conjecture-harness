# Exact affine proof certificates

This adapter proves a restricted class of universally quantified rational affine implications over the reals, not general mathematical conjectures.

Use the schema {"variables":["x","y"],"assumptions":[[0,1,-1],[-2,0,1]],"conclusion":[-2,1,0]}. Each row means constant plus the coefficients times the listed variables is nonnegative. The example states that x >= y and y >= 2 imply x >= 2. All coefficients are exact integers or rational strings. Use affine.statement(spec) to generate the canonical text of a proof-state claim. Do not silently identify another mathematical statement with this language; a separate implication or equivalence is necessary.

The proof search applies Fourier–Motzkin elimination to the assumptions plus the strict negation of the conclusion. Every derived row carries nonnegative rational multipliers on the original rows. When variables cancel and a constant contradicts the weak or strict inequalities, the certificate is replayed by a separate direct linear-combination calculation. An inconsistent assumption set implies the conclusion vacuously, which does not establish that the assumptions themselves are satisfiable.

```python
from affine import statement, prove, replay
from affine_lab import discharge
from discovery import new
s = {"variables":["x","y"],"assumptions":[[0,1,-1],[-2,0,1]],"conclusion":[-2,1,0]}
r = prove(s)
assert r["status"] == "proved"
assert replay(s, r["certificate"])
g, evidence = discharge(new(statement(s)), "goal", s)
```

The optional discovery runner automatically searches up to two reachable canonical affine obligations per pass, including before invoking the model. A successful exact certificate can establish that exact obligation; it cannot accept an unrelated implication in the proof graph. No generated Python or Lean code is executed. Failed searches leave the claim open. Reserved certificate observation IDs cannot be submitted as untrusted model observations. The state file remains operator-controlled, not cryptographically authenticated.

Limits: six variables, twelve assumptions, bounded pair generation, intermediate row count and coefficient size. The method is sound when the certificate checker and input semantics are correct; implementation tests are not a formal proof of software correctness. Unknown or budget exhaustion is not a disproof. No automatic translation from arbitrary prose, nonlinear reasoning, general Lean verification, or claim of novel mathematical discovery. Preserve the full specification and certificate in any research output.
