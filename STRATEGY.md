# Evidence-driven research strategy allocation

A proposal gets zero immediate proof credit. When a subsequent trusted review establishes or refutes a target-relevant claim, or accepts or rejects a relevant implication, its verified item ID is recorded. The first proposal history entry owning that ID can receive delayed feedback (positive and adverse each capped at one per attempt), independently of the mode of the automatic checker or operator. Detached claims, observations and unreviewed prose are not credited. The ranking combines positive credit for established claims and accepted implications, a separate adverse penalty for refuted claims and rejected implications, exploration of under-sampled modes and a bounded penalty based on measured worker elapsed time. Refutation is useful to the research process but is not counted as a successful conjecture by its proposer. The adverse weight of 0.5 is a heuristic, not a learned or calibrated parameter. This is provenance-based attribution, not causal inference, a calibrated probability of mathematical success, or a learned model. Legacy history remains readable but has no retroactive verified-item credit.

After three proposal attempts without verified progress, the escape schedule rotates through all seven modes rather than permanently excluding forward reasoning, backward reasoning and refinement. The parallel portfolio ranks additional nonblind slots using the same policy while retaining a target-only slot. The serial runner now shares the portfolio's snapshot-constrained reconciliation: blind proposals cannot reference hidden claims, and equivalent typed proposals are deduplicated. Graph capacity and finite-power syntax examples are exposed to the model, with distinct finite and universal semantics. This is prompt and reference separation, not a security sandbox or proof of provider independence.

## No API worker required

From the repository root, initialize an exact typed claim and run the bounded tool-only loop:

    python -c "from discovery import new,save; from polynomial import statement; save('demo-state.json',new(statement({'variables':['x'],'domain':'real','relation':'nonnegative','terms':[[[2],1]]})))"
    python discovery_tools.py demo-state.json --passes 8 --seconds 60
    python discovery.py demo-state.json plan

Use a fresh filename: the Python example writes the state atomically but replaces an existing file. The tool-only loop never invokes an LLM, and exits on closure/refutation, a fixed point, or a pass/time limit. The time limit is cooperative between passes. A fixed point on a prose target is not a proof; formalize a useful intermediate claim and justify its bridge, or continue human/model reasoning using the chat protocol. No model key is required. Use discovery_run.py or discovery_portfolio.py for trusted external worker commands.

## Local validation

44 focused tests passed (strategy, discovery, portfolio and frontier). All 273 discovered tests at that stage were accounted for as passing across the timed-out full run (257 passing test IDs) and a successful 23-test follow-up (seven overlapping). Four subsequent model-free entry-point tests passed separately, bringing coverage to 277 distinct passing test IDs. This is not one uninterrupted 277-test run. The change does not demonstrate scientific improvement against ordinary prompting. No live model, Lean or remote CI success is claimed.

## Outcome-sensitive follow-up

The scheduler now separates successful and adverse reviewed outcomes and counts only actual proposal attempts toward stagnation. Zero-reward trusted checker events no longer advance the escape rotation. An established claim inferred through accepted dependency closure still earns positive credit. No credit is assigned to a missing edge-review decision. The source review's trust level is inherited; the policy is not a proof verifier. Falsification remains a research mode and negative evidence remains relevant to the proof state, but the new statistics do not measure causal credit for discovering a counterexample. Ten new tests pass. All 287 discovered tests passed across two invocations (227 before timeout, 72 follow-up, 12 overlapping). See evidence/strategy-outcomes.md. No comparative live-model performance is claimed.
