# Historical public pilot v1

Seven public, previously settled mathematical targets: one known theorem control, two related Euler counterexample tasks, and four formerly open conjecture formulations. The corpus is intended as a pilot for pipeline validation and a heterogeneous difficulty range, not a representative sample of all mathematical research. h02 and h03 share a research family; do not treat them as independent observations. The statements are intentionally named only by opaque IDs, but a model may recognize the problems.

The answer references contain exact witnesses/short proofs where practical, and established proof or formalization locators for the difficult results. They are NOT a self-contained reproduction of all published proofs. Reviewers must check the submitted mathematical arguments, not simply match their truth values or accept citations of the target as proofs. Sources were checked for the stated results; full proofs of the advanced results have not been independently re-derived here.

This corpus is public and the statements and solutions may already occur in training data. It is not a held-out test of novelty or rediscovery, and no experimental result has been produced for it. To conduct an experiment, use the same worker/model/configuration and limits for each arm, freeze the design before running, isolate the worker environment from the reference file and arm keys, and have independent qualified reviewers examine the blinded final answers. Do not copy this reference file into worker working directories. Network and filesystem isolation are the operator's responsibility.

```sh
python engine_eval.py freeze evaluation/historical_v1/tasks.json evaluation/historical_v1/references.json experiment.json --calls 4 --timeout 120 --seconds 600
python engine_eval.py run evaluation/historical_v1/tasks.json experiment.json worker-config.json experiment-output
python engine_eval.py score evaluation/historical_v1/tasks.json evaluation/historical_v1/references.json experiment-output reviews.json
```

All benchmark facts predate this harness; no mathematical novelty is claimed. Use a larger independently curated, nonpublic corpus and separately report known-answer controls before drawing conclusions about general discovery performance.
