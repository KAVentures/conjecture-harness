# Activation and execution

**Engine-first:** when a local checkout and execution are available, use the coding-agent commands below and consult CAPABILITIES.json. Only fall back to chat/native tools when that execution is unavailable. The root HARNESS.md is the public entry point; this document specifies the runtime contract.

**Chat fallback:** paste the repository URL and target. The AI reads HARNESS.md at a pinned revision, then works immediately. If necessary paste the raw canonical document into the conversation. The URL does not inject system instructions, force tools or grant shell access. Chat checkpoints are self-reported, not tamper-proof receipts.

**Coding agent:** clone or open the checkout, read HARNESS.md, then run:
```sh
python activate.py plan --target "Exact mathematical statement"
python activate.py run --target "Exact mathematical statement" --output my-run
python activate.py resume --output my-run
```
The plan uses conservative keyword hints plus a general fallback, not semantic classification. For exact work on a typed subclaim see QUICKSTART.md and the suggested docs. A prose target may not be recognized by exact tools. Use the existing state graph to propose typed claims and justify their bridges. Do not report a tool-only fixed point as a proof.

**Runtime:** optionally supply `--worker-config path.json` containing a trusted operator-provided command array under "worker" (see agent_adapter.py and STRATEGY.md). This invokes the existing bounded model runner with metareasoning, and passes the scoped canonical instructions through its shared prompt builder. The CLI does not install agents, provide credentials, enforce provider isolation, or guarantee a breakthrough. Never pass an untrusted command. Budget limits are cooperative between exact passes; a single exact computation may overrun.

The run directory contains activation.json, state.json, numbered checkpoint and receipt files, and underlying worker logs if any. Resume preserves the same target and existing graph; receipts include before/after state digests, document digests, audit outputs and actual worker-log hashes. A revision can change across resumes and is recorded, not silently equated. Receipts are local evidence, not authenticated logs or proof of semantic instruction adherence. Interrupted/failed execution may leave state and raw logs without a completed receipt. Do not resume untrusted states. No credentials or external publication are required.

For stronger reproducibility pin the checkout revision, review local changes, retain the whole directory and replay the proof independently. Keep private mathematical data and raw worker logs private unless explicitly approved. The old commands remain supported.

## Interactive engine loop without an external worker

A coding assistant itself can act as the proposal worker. The initial `run` creates an immutable target and state; a prose target often produces an unresolved receipt because it is not directly machine-checkable. This is expected, not a reason to abandon the engine.

From engine/:
```sh
python discovery.py research-run/state.json plan
python discovery.py research-run/state.json prompt
# Write proposals.json as the JSON operations described in the generated prompt.
python discovery.py research-run/state.json apply proposals.json --mode backward --focus goal
python activate.py resume --output research-run
python proof_audit.py research-run/state.json
```

Use the actual focus and mode selected by the planner. For finite constraint or modular obstacles consult CONSTRAINT_DISCOVERY.md; its modular residue proofs cover all integer tuples at a fixed modulus. For finite graph or exact-cover obstacles, consult STRUCTURAL_DISCOVERY.md: generate a typed obligation, let the engine invent checked structural reductions, run declarative experiments, replay witnesses, and vary hypotheses without replacing the original target. A proposal may contain claim, derive and observe operations. Keep its mathematical bridge explicit, and never use `--trusted-review` for model-generated claims. Do not mark an auxiliary statement as a theorem just because a finite instance was verified. The engine can discharge typed obligations automatically; arbitrary semantic implications remain unverified until justified by a supported checker or reviewed mathematical proof. Continue from the existing state, preserve failed hypotheses, and change mechanism after stagnation.

For a fixed finite typed problem, construct the canonical statement using the relevant module's `statement(spec)` (see its documentation), then use it as the argument to `activate.py run --target`. This preserves activation receipts; alternatively `research_checkpoint.py init` and `discovery_tools.py` provide the lower-level typed workflow. Do not overwrite or replace the original universal target with a finite experiment.

## Bounded experiments and readiness

Use [EXPERIMENT_RUNTIME.md](EXPERIMENT_RUNTIME.md) for executable allowlisted experiments and receipts. Before a new serious conjecture attempt on an upgraded engine, run `python engine_readiness.py --output engine-readiness-results` and require a passing result and clean audit; inspect actual evidence instead of assuming readiness. Activation records both the root public prompt and engine worker contract hashes.

## Sustained research profile

With --worker-config, activation now defaults to the solution-first research campaign (see [CAMPAIGN.md](CAMPAIGN.md)); use --profile quick for the previous short single-worker behavior. Research stdout is compact; --verbose prints the full receipt. Without worker configuration, quick exact activation is unchanged. No model command is inferred.
