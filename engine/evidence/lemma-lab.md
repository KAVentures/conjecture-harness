# Local lemma-lab evidence

Ran python -m unittest discover -s tests -v: 75 tests, OK (14.637 seconds). New tests: 12. The 75 labeled graphs of orders one through four were cross-checked with separate bitmask and set-based algorithms.

Matched-budget controls (16 graph evaluations maximum per strategy):
| Control | Enumeration | Structural seeds |
|---|---:|---:|
| Dense clique | not found | found at 2 |
| Sparse degree | found at 16 | found at 2 |
| Independence lower bound | not found | found at 2 |
| Triangle-free degree | not found | found at 7 |
| Edge bound | not found | found at 2 |
| Order dominates independence (true) | not found | not found |
| Connected size (true) | not found | not found |
| Sparse edge | found at 2 | found at 2 |

Reproduce with python lemma_benchmark.py. No model calls. Hand-selected, known elementary controls; not a held-out evaluation or evidence of a novel breakthrough. No claim of proof from finite survival.
