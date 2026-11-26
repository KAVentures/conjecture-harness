# Conjecture Harness

**Turn a conversation into a reproducible mathematical research project.** No installation needed for the core protocol.

Version 0.6.0-preview — ready for fresh-chat testing, not a scientifically validated autonomous theorem prover. No guarantee of resolving an open problem.

## Start

Paste this into a new ChatGPT conversation:

> Use https://github.com/KAVentures/conjecture-harness as your research harness. Read README.md, AGENTS.md, protocol/RESEARCH.md, protocol/DISCOVERY.md, protocol/OUTPUT.md, protocol/CITATIONS.md and CITATION.cff at one revision. Help me solve [conjecture], or find a genuinely open problem if I haven't specified one. Start substantive research immediately, pursue competing approaches, independently audit the result, and prepare a complete reproducibility package and citable paper if warranted. Do not publish anything without my approval.

If access fails, download the repository ZIP and upload it to the chat. Do not pretend to have read inaccessible files. Tool availability varies by environment; no API key or local installation is necessary for the reasoning protocol. Repository creation, file generation, web search and formal verification depend on actual capabilities. No ongoing background work is implied.

For the optional local end-to-end workflow and cross-problem learning, see [QUICKSTART.md](QUICKSTART.md).

## Workflow

1. Freeze the exact statement, source and status. Check known stronger results and equivalent formulations.
2. Maintain a branching proof state. Work backward to sufficient lemmas and forward from established facts, falsify and evolve hypotheses, and pivot after stagnation. See protocol/DISCOVERY.md.
3. Audit every proof step, replay exact witnesses, formalize where useful and investigate novelty separately.
4. Produce a LaTeX manuscript, evidence, references, reproducibility instructions and honest AI disclosure. Build a PDF only when tools permit.
5. With confirmed human author credit, generate a root CITATION.cff with preferred paper citation, a two-entry CITATION.bib and human-readable CITATION.md. Publish only with explicit user approval, actual access and agreed licensing/visibility.

## Read the protocol

- [AGENTS.md](AGENTS.md) — assistant entrypoint.
- [Matrix inequality discovery](MATRIX_DISCOVERY.md) — exact permanent coefficients, adversarial transportation moves, symbolic contractions and typed sufficient-condition synthesis.
- [Discovery protocol](protocol/DISCOVERY.md) — recursive lemma discovery, bidirectional proof-state search, counterexample-driven evolution and stagnation escape (default for chat).
- [Exact polynomial proofs](POLYNOMIAL_PROOFS.md) — identities, weighted squares and rational counterexamples.
- [Adaptive strategy and model-free tool loop](STRATEGY.md) — delayed verified credit, bounded exploration and no-API execution.
- [Checked theorem transfer](THEOREM_TRANSFER.md) — automatically discover and verify conditional graph-capacity bridges.
- [Structural graph reductions](GRAPH_REDUCTION.md) — discover and replay capacity-preserving induced reductions.
- [Exact finite graph-power search](FINITE_POWER.md) — symmetry reduction, coloring proof trees and checked packings.
- [Graph capacity certificates](CAPACITY_CERTIFICATES.md) — exact graph-to-matrix transfer, universal bounds and finite refutations.
- [Recursive lemma invention](RECURSIVE_INVENTION.md) — bounded multilevel proof search with replayable certificate trees.
- [Target-only lemma invention](LEMMA_INVENTION.md) — discover and certify additive obligations without an auxiliary seed.
- [Hypothesis evolution](HYPOTHESIS_EVOLUTION.md) — counterexample-guided additive repair and conditional proof composition.
- [Exact transformations and equivalence](TRANSFORMATIONS.md) — reuse typed lemmas and transport polynomial proof certificates.
- [Discovery evaluation](EVALUATION.md) — matched call-cap experiment, exact scoring and evaluation-driven solver improvements.
- [Proof composition and Lean export](PROOF_COMPOSITION.md) — conditional certificate bridges and typed formal proof attempts.
- [Exact affine proofs](AFFINE_PROOFS.md) — automatically certify supported universal linear implications.
- [Exact lemma lab](LEMMA_LAB.md) — structural graph counterexample search and independently replayed refutation.
- [Parallel discovery portfolio](PORTFOLIO.md) — bounded concurrent workers and deterministic proof-state reconciliation.
- [Discovery engine](DISCOVERY_ENGINE.md) — optional persistent graph and bounded runner.
- [Research protocol](protocol/RESEARCH.md) — search, proof, counterexample, novelty and continuation.
- [Output contract](protocol/OUTPUT.md) — repository structure and publication gates.
- [Citation protocol](protocol/CITATIONS.md) — cite the harness, mathematical sources, result repositories and papers.
- [Optional Python engine](PYTHON_ENGINE.md) — stochastic workers, exact checkers and benchmark.
- [Known control](examples/known-star/README.md) — reproducible elementary counterexample and LaTeX paper (not novel).
- [Local test evidence](evidence/README.md) — previous test and exact finite benchmark logs.
- [Read-only proof audit](PROOF_AUDIT.md) — replay supported certificates without trusting review flags.
- [v0.6 regression evidence](evidence/release-audit.md) — 317 passing tests across two completed, disjoint batches; see release gates for scope.
- [Release gates](RELEASE_GATES.md) — limitations and scientific evaluation.
- [Cite the harness](CITATION.cff) · [BibTeX](CITATION.bib).

A successful mathematical proof requires a valid argument, not model confidence, many attempts or a passing software test. A catalogue's open label is not proof of novelty. A compiled paper is not peer review.

## License and credit

The original harness code and documentation are offered under the [MIT License](LICENSE). Project attribution: KAVentures. Cite the exact revision used. No DOI has been issued. The harness license does not automatically apply to research outputs or third-party sources.

## Core discovery extensions

- [Core mathematical discovery extensions](CORE_DISCOVERY.md) — exact symbolic discovery, invariants, theorem application, knowledge reuse, metareasoning, Lean export and matched-budget evaluation.
- Run transparent model-free controls: `python core_regression.py --output core-control-results`.
- [Historical public benchmark pilot](evaluation/historical_v1/README.md) — seven previously settled tasks with separate references; no model performance results yet.

## Optional local package utilities

Python 3.10+; no credentials required for exact tools. Run from this repository. The optional model-free loop in [STRATEGY.md](STRATEGY.md) runs supported certificates to a bounded fixed point; external workers remain optional.

```sh
python -m unittest discover -s tests -v
python project.py init my-result --id my-result --statement 'Exact statement' --author 'Confirmed human name'
python citations.py generate my-result
# Replace all example data with confirmed actual metadata first:
python discovery_citation.py my-result confirmed-metadata.json
python project.py seal my-result
python project.py validate my-result --publication
```

The publication flag checks citation consistency; it is not authorization, authorship validation, DOI verification or proof certification. Always inspect the actual manuscript and target. [Example metadata](examples/confirmed-metadata.example.json) is a synthetic fixture and must never be published as real research metadata.
