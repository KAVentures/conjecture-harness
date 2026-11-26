# Recursive lemma invention

The new bounded recursive search extends sparse-square extraction by trying multiple nested decompositions when a residual remains unresolved. Each extracted square is certified immediately; the residual becomes the next proof obligation. The search uses iterative deepening, exact direct-result caching, local duplicate elimination, ancestor exclusion, bounded branch width and a shared extraction budget. A counterexample to a residual only rejects that branch. Exhaustion is unknown.

A successful certificate is a tree: every internal node has two summands on the identical domain and an exact coefficient identity; every leaf has a replayable SOS certificate. The whole tree is replayed against the unchanged original target before atomic installation in the AND/OR proof graph. Unknown results do not earn proof credit. Existing candidate routes are preserved. The default bound is three decomposition levels, 16 candidates per expansion and 384 candidate extractions, with maximum supported depth four. This is a bounded chain of square extraction and residual subproblems, not a general recursive theorem prover.

## Reproduce

From the repository root:

    python -m unittest discover -s tests -p test_recursive_invention.py -v

For six selected parameter combinations, run:

    PYTHONPATH=tests:. python - <<'PY'
    from test_recursive_invention import target
    import polynomial as p
    from lemma_invention import invent
    from recursive_invention import search,replay
    for v in [(4,2,1,4,2,1),(3,1,2,7,2,3),(5,2,1,8,3,2),(6,1,3,5,2,1),(2,1,1,3,1,2),(8,3,1,7,3,2)]:
        s=target(*v);r=search(s)
        print(v,p.solve(s)['status'],invent(s)['status'],r['status'],r['tested'],replay(s,r['tree']))
    PY

Each is the sum of two members of the earlier selected quartic family on disjoint variable pairs, supplied only as expanded coefficients. The direct and shallow solvers returned unknown on all six; the recursive method proved all six with exact replay after 18 candidate extractions each. The first control has two decomposition levels, three certified leaves and two accepted bridges. These selected same-family results do not establish generalization, equal total compute, live-model gains or an open-conjecture breakthrough. Twelve targeted tests passed locally.
