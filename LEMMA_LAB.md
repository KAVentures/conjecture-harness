# Exact lemma falsification laboratory

The first domain adapter searches linear inequalities involving graph order, size, independence number, clique number, minimum degree and maximum degree, optionally requiring connectedness or triangle-freeness. It is deliberately limited to finite simple undirected graphs of order at most six during search. The quantified claim can be unbounded; a counterexample refutes it, but finite survival does not prove it.

Example spec.json (known false control):
```json
{"min_n":1,"properties":["connected"],"coefficients":{"alpha":1,"n":-1},"constant":0}
```
Run:
```sh
python graph_lemma.py spec.json --strategy families_first
python graph_lemma.py spec.json --replay witness.json
python lemma_lab.py state.json lemma1 spec.json --max-n 5 --budget 40000
python lemma_benchmark.py
```
The replay file contains only the witness object from the search report. For proof-state integration, create an open claim whose statement exactly equals graph_lemma.statement(spec). The canonical statement prevents an unrelated counterexample from refuting arbitrary natural language. If an independently implemented bitmask and set-based checker agree on a counterexample, the lab records it and marks only that claim refuted; surviving hypotheses remain open. The next research mode is refinement. No model-generated code executes. Operators should preserve the mathematical mapping from their original lemma to the canonical statement and review it separately.

The structural strategy seeds empty and complete graphs, stars, paths, cycles, complete bipartite graphs, unions of two cliques, and complements before enumeration. It skips duplicate labeled graphs within each order and reports budget exhaustion, empty scope, or completed orders accurately. The benchmark compares two deterministic strategies with a matched budget of 16 graph evaluations on each of eight hand-selected elementary controls. Six are false and two are true. Local results: exhaustive order found 2/6 false controls, families-first found 6/6, neither produced a false positive on the two true controls. These controls favor simple structural families; the result is not evidence of general superiority, held-out performance, live model performance or open-problem discovery. Run the script to regenerate witnesses and counts. The local regression suite passed 75 tests (12 new lab tests). Remote CI is separate.

For unsupported domains, use exact problem-specific checkers and keep results unverified until reviewed. Do not force Shannon capacity into this graph-invariant language. The Shannon code-construction checker remains distinct. No general automated theorem prover or Lean integration is supplied by this module.
