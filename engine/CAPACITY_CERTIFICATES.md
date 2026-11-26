# Graph-to-matrix theorem transfer

This adapter transfers graph capacity claims to exact algebraic certificates. It uses classical methods, not a newly discovered theorem. A canonical spec has n (1..32 vertices), edges (zero-based pairs u<v, no duplicates), and upper (a positive rational). Edges represent confusability. The target is the Shannon capacity of the graph under strong powers, bounded above by upper.

## Proof of the certificate rules

**Gram route.** Let B be a symmetric real matrix with diagonal 1, zero entries on every distinct nonadjacent pair, and B-J/t positive semidefinite, with J the all-ones matrix and t>0. Write B=J/t+C with C positive semidefinite. Expanding the k-fold tensor power shows B^⊗k-J^⊗k/t^k is positive semidefinite, because every remaining summand is a tensor product of positive semidefinite matrices. For an independent set S in the k-fold strong power, its principal submatrix of B^⊗k is the identity: any distinct independent pair has a nonadjacent coordinate. Thus, evaluating the PSD inequality on the indicator vector of S gives |S| - |S|²/t^k >= 0. Consequently alpha(G^⊠k) <= t^k for every k and the capacity is <= t. The replay checker verifies every hypothesis using exact rational Schur complements, including singular pivots. No floating eigenvalue tolerance is used.

**Rank route.** Let M over a prime field have nonzero diagonal and zero entries on all distinct nonadjacent pairs. Its tensor power fits the corresponding strong graph power. On an independent set the principal submatrix is diagonal with nonzero diagonal, so |S| <= rank(M^⊗k)=rank(M)^k. Thus capacity <= rank(M). Replay uses modular Gaussian elimination over an explicitly allowed prime field. This is the classical Haemers rank bound.

**Refutation route.** An explicit independent set of size m in the kth strong power refutes capacity <= t exactly when m > t^k; all pairs and the rational inequality are checked. This is a lower-bound witness, not an exact capacity proof.

## Search and integration

The automatic search attempts a greedy clique partition, the regular-graph candidate B=I+cA with c=(n/t-1)/d, fitting matrices I+wA over several small prime fields, and finally bounded greedy finite packings in powers one and two. These are intentionally incomplete searches, not SDP or minrank optimizers. A failure remains unknown. Arbitrary supplied matrices can be replayed within the schema, including nonregular graphs. The runner attempts one canonical reachable capacity claim per pass; original statement and certificate are retained. Untrusted proposals cannot forge reserved evidence IDs. To use the module:

    from capacity import statement, solve, replay
    spec = {"n":2, "edges":[[0,1]], "upper":"1"}
    report = solve(spec)
    assert report["status"] == "proved"
    assert replay(spec, report["certificate"])

Model-facing research can use the exact canonical statement from capacity.statement(spec). A transfer from a prose target must still justify graph convention and the corresponding inequality.

## Reproduced controls, not new results

For the triangular graph T5 (vertices are 2-subsets of a five-element set, adjacency is intersection), the solver verifies the classical capacity upper bound 5/2 using B=I+A/2. The stronger requested bound 12/5 remains unknown; this neither proves nor refutes it. For C5 it verifies the rational upper bound 9/4 (not the sharp irrational sqrt(5)). Complete and empty graphs provide exact integer controls. The capacity problem for T5 is not resolved by these tests.

Classical source: L. Lovasz, "On the Shannon capacity of a graph", IEEE Transactions on Information Theory 25(1), 1–7 (1979), DOI 10.1109/TIT.1979.1055985. The elementary tensor derivations above are provided in full so replay does not rely on an unsupported black-box theorem assertion. See also the rank-bound discussion in I. Sason, "Observations on the Lovasz theta-function, graph capacity, eigenvalues, and strong products", Entropy 25(1), 104 (2023), DOI 10.3390/e25010104.

Local validation: 224 tests passed in 37.534 seconds, including 15 new capacity tests. No live-model calls, novel bound, held-out benchmark or general breakthrough claim.
