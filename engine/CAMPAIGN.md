# Solution-first research campaign

With an explicitly configured trusted model wrapper:

    python activate.py run --target "exact conjecture" --output run --worker-config workers.json
    python activate.py resume --output run --worker-config workers.json

The research profile defaults to 3600 seconds, 100 proposal calls, five parallel slots, 600-second worker timeout and ten proposals per wave. Adjust with --seconds, --attempts, --timeout, --workers (1..7) and --wave-attempts. Explicit operator configuration is authorization to invoke the supplied command within these limits; it is not permission to install software, create credentials, or publish. Budget is per invocation, not lifetime, and cooperative between exact computations. A campaign may stop earlier on audited root closure, integrity conflict, recorded closure lacking replay, or exhaustion of a hard limit. Model wrappers must handle their own provider costs, model context limits and tool permissions.

Example configuration (replace paths with your own trusted absolute commands; they receive prompts on stdin):

    {"workers":[["/path/to/trusted-proposal-wrapper"]],"reviewers":[["/path/to/referee-a"],["/path/to/referee-b"]]}

Multiple slots may share a command; this does not establish independent models. Reviewer commands are optional (up to three distinct arrays). Do not use the same underlying context as independent verification. Referees receive only the immutable target and complete candidate, with different review lenses. They return strictly bound JSON critiques. The result remains advisory even when all agree. A failed or unsupported review is not proof of falsehood. Full arbitrary prose theorem checking, formalization, and literature novelty are separate obligations requiring genuine expert/formal or appropriately equipped review. The engine does not auto-promote a prose proof.

Every research wave interleaves model proposals and exact replay; a fixed point in the model-free exact phase does not end a configured campaign. Two consecutive waves without new root-connected replayed evidence trigger root-focused mechanism rotation. This conservative heuristic intentionally does not reward large numbers of disconnected verified claims. It is not a calibrated measure of progress. Target-only exploration stays isolated from the graph; diverse lenses rotate. Existing typed engines and reconciliation remain unchanged. Candidate review uses at most 20% of remaining time per wave, subject to cooperative exact-pass limits. Ordinary claims, raw logs, and sketches stay internal. A candidate is not a completion signal.

State and numbered activation receipts remain in the run directory. Additional campaign/wave-*.json files record launch counts, target, progress and pivots. campaign/reviews/ contains raw candidate and review artifacts. Do not publish these automatically. A crash can leave a partial review directory; inspect it manually. Resume checks the immutable target, retains the state and stagnation count and uses a fresh authorized per-run budget. Never resume untrusted state. Do not run competing coordinators on one directory.

Research-profile stdout is a compact status, not a full mathematical manuscript. Use --verbose to inspect the full receipt. For an exact verified goal, reconstruct the complete argument from replayable evidence and independently check the intended statement and novelty before publishing. For prose, a human-readable proof and independent validation are still required. If unresolved, report only the stopping reason and checkpoint by default.

Without a configured worker, activate.py retains its quick model-free behavior. A coding assistant should keep proposing and executing new typed obligations within its available budget; a chat assistant should use native tools and avoid premature reports. A repository URL cannot extend a host's time or reasoning limit.

No empirical improvement in open-conjecture success is asserted. Run matched-budget comparisons against prompt-only and prior-engine baselines before making such a claim.
