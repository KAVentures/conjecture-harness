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
