# Structural discovery, proof evolution and finite experimentation

## Checked surgery and transfer

For a degree-two vertex v with distinct nonadjacent neighbors a,b, suppress v and insert ab, relabeling the remaining vertices. If an endpoint vector is prescribed require b(v)=0. Every path decomposition of the reduced simple graph lifts by replacing its unique use of ab by a-v-b. No other path uses v; simplicity, edge coverage, number of pieces and remaining endpoint counts are preserved. Only this direction is asserted. The automatic adapter invents the reduced typed claim and a checked implication, then recursively discharges the frontier. The reduced claim remains an independent obligation. A refuted reduced claim does not refute the original. The monotone transfer rule also reuses audited tighter finite cover claims: allowed rows may be enlarged, the piece budget increased, and exact endpoint constraints dropped, but resources cannot silently change. Proof bundles replay these bridges through the existing audit.

## Declarative experimental engine

Use a JSON specification:
```json
{"min_n":2,"max_n":4,"connected":true,"min_degree":0,"bound":[1,2,0],"graph_budget":128,"state_budget":128}
```
The bound is ceil(a*n/b)+c. Enumerate labeled simple graphs in deterministic order, filter by the specified properties, solve each finite cover instance and independently replay every decisive certificate. An enumeration prefix is not exhaustive; unknown is distinct from proved. The report includes exact input, counts, trace digest and bounded witness samples. Replay recomputes the complete report. No arbitrary worker code executes.
```sh
python cover_experiments.py run experiment.json report.json
python cover_experiments.py replay report.json
python cover_experiments.py frontier cover-spec.json --hi 6
```
The frontier command tests neighboring finite piece budgets and reports an exact minimum only when all smaller nonnegative budgets have been refuted and a positive witness replays. Use actual witnesses to invent changed hypotheses, never infer universal bounds from survival.

## Formal export
```sh
python combinatorial_cover.py cover-spec.json > result.json
python cover_lean.py cover-spec.json result.json Cover.lean
lake env lean Cover.lean
```
The generated theorem existentially asserts an explicit finite list of allowed rows meeting all exact item counts, resource totals and the piece budget. It uses a concrete witness and decide, not an unchecked axiom. Check the build and axiom report in a trusted pinned mathlib project. Python validates the finite compilation; graph-to-row compilation is not formalized in Lean. Negative certificates still use the Python verifier. Export is not proof of a successful Lean build.

These are deliberately bounded generic mechanisms, not unrestricted structural invention or a solved open conjecture. The runner must still explore alternative representations and use model reasoning for untyped universal bridges.
