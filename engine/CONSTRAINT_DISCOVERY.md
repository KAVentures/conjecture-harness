# Finite constraint and universal modular discovery

## Finite integer constraints
```json
{"domains":[[0,1],[0,1]],"constraints":[{"kind":"linear","coefficients":[1,1],"relation":"eq","rhs":1},{"kind":"different","variables":[0,1]}]}
```
Every variable has an explicit finite integer domain. A linear row has integer coefficients and relation eq/le/ge; different requires distinct values for the named variables; table permits exactly the listed tuples. All constraints must hold. The solver searches for an assignment, or constructs a postorder branch DAG proving impossibility: each leaf has a violated linear interval, a failed exact bipartite matching for all-different, or no compatible table tuple. Split nodes must contain every value of the original domain. Replay checks each leaf and split without rerunning the solver. At complete assignments each test is exact. Unknown is not refutation. Caps: 16 variables, domain size 16, 64 constraints, 768 search states.

## Modular implications on all integers
```json
{"variables":1,"modulus":6,"assumptions":[],"conclusion":{"terms":[[[3],1],[[1],-1]],"allowed":[0]}}
```
For every integer tuple x, if each assumption polynomial evaluates modulo m to an allowed residue, the conclusion polynomial must evaluate to an allowed residue. Integer polynomial evaluation commutes with reduction modulo m. Thus complete coverage of the m^n residue classes proves the unbounded integer implication; a bad residue is an exact integer counterexample. Caps: 5 variables, modulus 256, at most 65536 residues per direct call. The engine can also split unconditional divisibility into prime-power divisors, install a checked AND implication, and prove the smaller obligations independently. No claim is made about existence of solutions to general Diophantine equations.

From engine/:
```sh
python finite_csp.py constraints.json
python modular_discovery.py modular.json
python research_checkpoint.py init research.json modular modular.json
python discovery_tools.py research.json --passes 4 --seconds 60
python proof_audit.py research.json --require-verified
```
Use fresh output paths. The original universal conjecture remains unchanged; a model must justify any translation into one of these languages. The static certificate registry supports replay and portable proof bundles for proved typed claims.
