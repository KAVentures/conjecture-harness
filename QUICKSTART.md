# Start, continue and checkpoint a research problem

## Chat first (no installation)

In a fresh conversation, use the README prompt, link to this repository at a single revision, state the exact target, and ask for substantive research. Follow the discovery and output protocols. If source files or tools are inaccessible, state what is missing. A model without a shell cannot claim to have executed the Python adapters. A prose conjecture is not a machine-verifiable certificate.

## Local typed workflow

Python 3.10+; no model credentials required for exact adapters. Use fresh filenames. Example polynomial spec saved as spec.json:

    {"variables":["x"],"domain":"real","relation":"nonnegative","terms":[[[2],1]]}

    python research_checkpoint.py init state.json polynomial spec.json
    python discovery_tools.py state.json --passes 8 --seconds 60
    python research_checkpoint.py checkpoint state.json checkpoint.json
    python research_checkpoint.py resume checkpoint.json restored.json
    python discovery.py restored.json plan

The elementary example is a known control, not novel. The initialization languages are prose (literal statement), affine, polynomial, capacity and finite-power (JSON file). For other mathematical problems, initialize prose and generate precisely justified typed subclaims as appropriate. A tool-only fixed point on an unresolved claim is not a solution.

The checkpoint retains the entire graph, history and recorded evidence. It checks that the summary matches the state on resume and refuses to replace an existing file. It does not independently prove arbitrary reviewed claims, authenticate a file, or include external raw run directories; preserve those separately. It contains potentially sensitive research content. Use only trusted states and inspect before sharing.

## Optional cross-target research learning

From reviewed local states, create an aggregate profile:

    python strategy_profile.py profile.json previous-a.json previous-b.json

Then pass --strategy-profile profile.json to discovery_run.py or discovery_portfolio.py along with their regular state and worker config arguments. No existing files are replaced. Prior statistics are stratified by supported statement type, exclude identical target hashes, average per-target rates and contribute only a weak bounded ranking bias. They do not transfer any theorem, review, proof, or raw research text. Target hashes can still identify known or guessable conjectures; the profile is not anonymous. Retain the exact profile and command with experiment logs for reproducibility.

Default operation without a profile is unchanged. Stagnation escape remains active. The profile relies on trusted local history and is not an empirically trained general mathematical model.

## Release and scientific gates

This is a usable v0.6 preview, not a general autonomous theorem solver. See RELEASE_GATES.md, EVALUATION.md and individual mathematical certificate documentation. Do not claim a novel result without a complete target-faithful proof and separate novelty investigation.
