# Evaluation and regression evidence

Local Python 3.13.5, no authenticated model invocation.

Generated 25 seeded controls per suite; all reference answers replayed exactly. Tool-only baseline before coordinate search: seed 1729, 21/25 (five affine proofs, five affine refutations, five graph refutations, five polynomial proofs, one polynomial refutation, four polynomial abstentions). Improved search: seed 1729, 25/25; seed 2718, 25/25. No model calls and no claim about real open problems. Reproduce using EVALUATION.md and its pinned prior commit.

Focused tests: 10 evaluation and 20 polynomial tests passed. Full suite: 149 discovered tests; first invocation timed out after 128 successful tests; separate test_portfolio, test_project and test_proof_frontier invocation passed 27 tests, six overlap, giving 149 distinct successful test IDs. Not a single uninterrupted full-suite run.

This is deliberately a component-level synthetic evaluation, not evidence that adaptive prompting or the full harness beats ordinary ChatGPT on unseen conjectures.
