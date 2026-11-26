# Outcome-sensitive strategy regression

Local focused command: PYTHONPATH=tests:. python -m unittest test_strategy_outcomes test_strategy test_discovery test_discovery_tools test_portfolio test_proof_frontier -v
58 tests passed in 10.635 seconds.

Full regression: python -m unittest discover -s tests -v timed out after 227 passing test IDs. Follow-up:
PYTHONPATH=tests:. python -m unittest test_portfolio test_project test_proof_frontier test_recursive_invention test_strategy test_strategy_outcomes test_theorem_transfer -v
72 tests passed in 9.007 seconds. Exact test-ID union: 287, with 12 overlapping, matching all 287 discovered tests. This is not one uninterrupted run.

Ten new tests cover positive vs adverse outcomes, caps per attempt, inferred closure, ranking, detached reviews, untrusted feedback, and stagnation bookkeeping. Synthetic trusted review fixtures are not mathematical discoveries. No live model execution or remote CI success is claimed.
