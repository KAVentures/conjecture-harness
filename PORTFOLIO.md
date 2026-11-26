# Parallel mathematical discovery portfolio

This optional runner combines the proof-state graph with multiple bounded proposal workers, an explicit target-only branch and deterministic reconciliation. It does not require parallel tooling for the chat-first method.

```sh
python discovery.py state.json init 'Exact quantified target'
python discovery_portfolio.py state.json --config config.json --workers 3 --attempts 12 --seconds 600 --timeout 120
```

Use the existing worker command array in config.json or provide a workers array containing one or more trusted command arrays. The runner rotates through configured commands; each accepts a prompt on stdin and returns a JSON operation array. To use different providers configure their authenticated CLI wrappers explicitly. No provider calls were made in the local tests.

Every round starts from a frozen state snapshot. Assignments include the controller-selected route, a target-only blind branch if multiple calls fit, and distinct remaining research modes. Each worker has a separate process and working directory. This is prompt-level separation, NOT a security sandbox, provider-independent context or proof of statistical independence. Trusted commands may access the same filesystem, credentials or provider memory. Use disposable, least-privilege external isolation where appropriate. The controller never claims separate agents actually ran unless they did.

Workers cannot establish or refute claims or approve implications. Their local IDs are mapped into a deterministic namespace. Exact normalized-text duplicate claims share a node; duplicate premise sets are not added twice, but original arguments remain in raw response logs. Claims and derivations from a worker are applied as an atomic batch; cross-snapshot references, cycles, invalid operations and attempts to impersonate reserved certificate evidence are rejected. This is textual deduplication, not semantic mathematical equivalence. Reconciliation order is assignment order, not completion order. The controller writes each accepted batch to persistent state and retains rejected responses. One failed worker does not invalidate its peers.

Exact affine and polynomial proof adapters run between rounds before spending further model calls. These can establish or refute their canonical claims only, after replay. Unchecked graph bridges remain obligations. Model-call limits are per invocation; the wall-time and output limits are cooperative, not billing quotas or hard OS resource isolation. Inspect raw logs before sharing them.

Tests use mock commands only; one test uses a process barrier to establish concurrent execution, another verifies that one worker failing does not discard a successful peer. The complete local regression suite passed 122 tests (12 new). Live frontier-model performance, mathematical novelty and speedup on unseen conjectures remain unvalidated.
