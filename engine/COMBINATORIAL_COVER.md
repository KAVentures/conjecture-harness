# Exact combinatorial cover and path partition

A reusable finite-instance language, not a proof of Gallai or any other universal theorem.

- Generic cover: items 0..items-1, nonempty allowed rows [item IDs, nonnegative integer resource vector], exact total resources and at most max_pieces rows. Each item must be covered exactly once. Resources can represent endpoint counts, quotas, colors or budgets (convert upper bounds to exact totals only with a justified encoding).
- Graph paths: simple undirected graph on 0..n-1, each edge covered once by nonempty simple paths, at most max_pieces paths, optional exact endpoint counts. Null endpoints leaves them unrestricted. Paths are enumerated by exhaustive vertex-simple DFS, with reversal deduplication; edge masks determine a simple path up to reversal. The compilation is a complete finite reduction if it finishes. If enumeration exceeds caps, return unknown, never refuted.

Example spec.json:
```json
{"kind":"paths","n":3,"edges":[[0,1],[1,2]],"endpoints":[1,0,1],"max_pieces":1}
```

Run from engine/:
```sh
python combinatorial_cover.py spec.json
python research_checkpoint.py init cover-state.json combinatorial-cover spec.json
python discovery_tools.py cover-state.json --passes 2 --seconds 60
python proof_audit.py cover-state.json --require-verified
```

The solver branches on an uncovered item with fewest eligible rows. A positive certificate lists canonical row indices; replay checks disjointness, coverage, resource equality and budget. A negative certificate is a postorder DAG of impossible states (remaining mask, remaining slots, remaining resource vector); replay reconstructs all eligible branches and requires every child already closed. An empty residual with zero resources is feasible and cannot be marked closed. A nonempty residual with no slots or eligible rows is impossible. Strictly decreasing masks establish well-foundedness. The verifier regenerates the canonical row universe; the branch-search result is not trusted. Budget exhaustion is unknown. Caps: 32 items, 4096 rows, 12 resources, 12 graph vertices, 30000 DFS visits, 512 search states. Canonical parsing and static namespace registry prevent worker impersonation.

This provides machine-checkable tests for finite graph partition hypotheses and generic exact-cover reductions. A negative result refutes only the precise typed instance. To establish a universal graph theorem from a fixed graph, supply the additional mathematical reduction or a valid counterexample to the universal statement separately. No novelty or performance gain claimed.
