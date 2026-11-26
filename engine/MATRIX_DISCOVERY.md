# Matrix inequality discovery (experimental)

A first nonlinear domain adapter, motivated by permanent inequalities. No novel conjecture resolution is claimed. The universal claim syntax covers every order n >= 3 and every real doubly stochastic matrix; finite certificates/search use rational matrices of order 3..7 (automatic search 3..5). The two statements are:

- `matrix-permanent:{"kind":"lih-wang"}`: per((1-t)J+tA) <= (1-t)per(J)+t per(A) for 0<=t<=1/2.
- `matrix-permanent:{"kind":"signed-prefix"}`: all signed coefficient prefixes defined below are nonnegative, for all such A. A stronger sufficient conjecture, not an equivalence or established result.

Optional matrix field fixes one exact rational matrix; use canonical compact JSON via statement(). The discovery graph binds evidence to the exact claim; universal finite search can only refute, never establish. Run:

    python matrix_permanent.py lih-wang --budget 64
    python matrix_permanent.py signed-prefix --budget 64
    python discovery.py --help

The normal discovery runner and discovery_tools.py dispatch canonical claims. A natural-language target needs a separately justified transfer to canonical syntax. Search combines block families, mixtures of permutations and feasible rational 2x2 transportation moves. Scores use signed prefixes or the exact chord gap at a finite t-grid. Search is bounded and not exhaustive; no negative witness is not proof. For fixed matrices, exact Bernstein coefficients on a partition of [0,1/2] can prove the polynomial inequality across the whole interval. Independent scalar permutation replay checks point counterexamples. Prefix counterexamples refute only the prefix claim.

## Dimension-independent algebra

Write B=A-J and F(t)=per(J+tB)/per(J)=sum c_k t^k, with c_0=1,c_1=0. Let M_k(B) sum products over all unordered k-edge matchings of the complete row-column bipartite graph. Expanding the permanent gives c_k=n^k (n-k)! M_k(B)/n!. Enforce distinct row and column indices in the ordered matching sum by partition-lattice inclusion-exclusion. For partitions R,C of [k], the weight is mu(R)mu(C), where mu(P)=product over blocks D of (-1)^(|D|-1)(|D|-1)!. Sum the product of k entries over unrestricted indices, identifying row indices within R and column indices within C; divide by k!. Any singleton block makes the contraction vanish because B has zero row and column sums. matching_identity(k) enumerates these symbolic contractions up to k=5 without fixing n. In particular M_2=sum B_ij^2/2 and M_3=2 sum B_ij^3/3. These identities are not general positivity certificates.

## Checked conditional theorem synthesis

Put w_k=2-2^(2-k) and P_m=sum_{k=2}^m w_k c_k. The normalized gap divided by t is sum c_k(1-t^(k-1)). For 0<t<=1/2 the ratios r_k=(1-t^(k-1))/w_k are positive and nonincreasing. Indeed (1-t^d)/(1-2^(-d)) is (1-t)/(1-1/2) times the ratio of geometric sums of length d; that ratio is a weighted mean of (2t)^j with weights 2^(-j), nonincreasing when an additional term is added. Abel summation gives P_n r_n + sum_{m=2}^{n-1} P_m(r_m-r_{m+1}) >=0 if every prefix is nonnegative. At t=0 equality is immediate. The graph synthesizes this typed implication, not the unproved premise; proof_audit independently recognizes the rule only for matching matrix scopes.

## Research protocol extension

For nonlinear families, branch on (1) symbolic coefficient contractions, (2) extremal feasible directions and structured support, (3) alternative certificates on a compact scalar interval, and (4) typed sufficient inequalities retaining cancellation. Transfer results between branches only through explicit implications. Record the first failed premise, witness and possible repair; do not make a stronger conjecture an accepted fact. For general dimension, explore recurrences, partition grouping, block induction and literature-derived inequalities; all remain candidate arguments until reviewed. No external model, SDP solver, general symbolic theorem prover or independent human reviewer is bundled here. Evaluate held-out historical targets with matched budgets and independently reviewed proof completion before making scientific claims.
