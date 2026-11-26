# Preview integration regression

New focused coverage: 43 strategy/profile/portfolio tests passed in 10.794 s; seven checkpoint tests passed in 2.613 s. Seventeen new tests in total.

Full command: python -m unittest discover -s tests -v
Timed out after 230 successful test IDs (45-second execution cap).
Follow-up command:
PYTHONPATH=tests:. python -m unittest test_project test_proof_frontier test_recursive_invention test_research_checkpoint test_strategy test_strategy_outcomes test_strategy_profile test_theorem_transfer -v
76 tests passed in 9.150 s (two overlap), covering all 304 discovered test IDs across both invocations. Not an uninterrupted full run.

New tests use synthetic reviewed states and mock workers; they demonstrate bounded strategy transfer and checkpoint lifecycle, not scientific discovery superiority. Remote CI and live-model evaluation remain separate gates.
