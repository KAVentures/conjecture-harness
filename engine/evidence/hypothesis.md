# Local hypothesis-evolution evidence

Focused command: python -m unittest discover -s tests -p test_hypothesis.py -v

13 tests passed. A selected quartic control that the direct solver leaves unknown is closed after a seeded failed auxiliary lemma, exact counterexample, automatic repair and additive proof composition. No LLM calls.

Full regression: 171 tests completed successfully before the 40-second execution timeout. Follow-up: PYTHONPATH=tests:. python -m unittest test_project test_proof_frontier -v — 14 passed (two overlapping). Union of distinct passing test IDs: 183, matching the discovered suite count. Not a single uninterrupted test run. No remote CI result or open-conjecture discovery claimed.
