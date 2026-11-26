# Exact finite strong-power search

A finite claim states alpha(G strong-power k) <= b for a nonnegative integer b. Edges of G denote confusability. This is intentionally a different typed claim from a universal Shannon capacity bound.

The algorithm constructs the distinguishability graph on words: two words are adjacent when at least one coordinate is distinct and nonadjacent in G. Independent sets of the strong power are exactly cliques in this graph. At each branch, a proper coloring of remaining candidates bounds any clique by the number of colors. Otherwise branching on a vertex v, then removing v from the remaining mask, partitions the possible nonempty extensions by the first chosen vertex in the branch order. The replay checker verifies every color class is independent, every candidate is covered exactly once at each branch, and every resulting clique bound is <= b. It does not rely on the heuristic ordering or a solver's success flag.

Optional symmetry reduction is exact: supply one automorphism mapping vertex zero to each base vertex. Their coordinatewise products imply transitivity on the words of the strong power. Every nonempty clique may therefore be mapped to one containing the all-zero word. The finder uses bounded adjacency-preserving backtracking; if it fails, it makes no claim of nontransitivity. Replay checks each permutation and every mapped edge. The reduced branch proves the original finite statement, not a restricted search subproblem. All lower witnesses are checked pairwise.

The runner automatically tries this adapter on a canonical finite claim, with at most 500 search nodes and a bounded symmetry search; direct API permits up to 10,000 search nodes and 1,024 words. Recursion and proof-tree size are bounded. Exhaustion is unknown, not infeasibility. A proof of a finite upper bound cannot establish a capacity upper bound; a finite packing supplies only a capacity lower bound.

## Reproduction

    python -m unittest discover -s tests -p test_finite_power.py -v

On the known triangular graph T5 square (100 words), with explicitly verified base automorphisms:
- Upper bound 5: exact proof in 52 search nodes; unreduced search returns unknown after 2,000 nodes.
- Upper bound 4: a five-word witness in 15 nodes versus 98 unreduced.
- Together they reproduce alpha(T5 strong-square) = 5.
- On the cube, an attempted bound of 12 remains unknown at the 2,000-node budget.

These node counts exclude symmetry discovery and graph construction, so they are not wall-clock speedups or matched-compute comparisons. All 75 labeled base graphs on one through four vertices were checked against brute-force independent-set enumeration. No new Shannon capacity bound or open-problem breakthrough is asserted.

Local validation: all 14 focused tests passed. The full test command timed out after 210 successful tests; a corrected follow-up command on the final four modules passed 39 tests (11 overlapping), yielding 238 distinct passing test IDs. An initial follow-up command mistakenly named a nonexistent test_verify module; the corrected run removed that name. Remote CI is separate.
