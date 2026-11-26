# Exact structural graph reductions

Let G have edges representing confusability, and H be an induced subgraph. A map f from G to H which sends every distinct nonadjacent pair to a distinct nonadjacent pair preserves distinguishability. Applied coordinatewise, f sends an independent set of every strong power of G injectively into the corresponding independent set of H: every pair of distinct codewords has at least one distinguishable coordinate, whose images remain distinguishable. Inclusion of H in G gives the reverse inequality. Thus alpha(G^k)=alpha(H^k) for every positive k and their Shannon capacities agree.

The automatic finder repeatedly deletes v when another surviving vertex u has closed neighborhood N[u] contained in N[v]. Mapping v to u preserves distinguishability: a nonneighbor of v cannot belong to N[u]. The composite map to the remaining induced subgraph is independently replayed against all nonedges of the original graph. The checker also verifies that the map fixes the induced subset. It can replay valid maps not discovered by the greedy folding algorithm.

The adapter tries the existing exact capacity solver on the reduced graph after the direct solver abstains. A reduced upper certificate is replayed together with the full graph map; any lower witness is lifted and checked in the original graph. Unknown remains unknown. The algorithm does not solve general graph homomorphism or prove minimality of the reduced graph.

## Controls

Three six-vertex extensions of C5, formed by adjoining a vertex adjacent to respectively {0,1,4}, {0,1,2,3,4}, and {0,1,2,4}, all reduce to C5. The direct capacity solver returns unknown for upper bound 9/4 on each; the new solver establishes all three via a five-vertex certificate. These selected elementary controls are not new capacity results or evidence of general performance.

All 75 labeled graphs of orders one through four were examined; 68 admit the greedy reduction. For those 68, brute-force independent-set computation on the first and second strong powers matched before and after reduction (136 comparisons). Twelve targeted tests passed, including tampered map, invalid subset, lifted witness and proof-state integration.

Run python -m unittest discover -s tests -p test_graph_reduction.py -v.
