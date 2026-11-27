# Bounded experiment runtime and readiness gate

The executable engine exposes allowlisted declarative experiments rather than treating worker-supplied code as trusted. Example request:
```json
{"operation":"modular","budget":16,"spec":{"variables":1,"modulus":2,"assumptions":[],"conclusion":{"terms":[[[2],1],[[1],-1]],"allowed":[0]}}}
```
Other operations: cover, finite-csp and cover-graphs (the last uses budget:null and the graph experiment's own limits). The schema validates all inputs. The subprocess command is fixed by the engine, uses a temporary working directory, wall-time and output caps, and receives JSON only. A receipt binds the request and actual code files by SHA-256, records outcome and elapsed time, and checks decisive certificates. Replay repeats the same bounded experiment and compares the deterministic outcome, failing closed on changed source or timeout. This is process containment for trusted code, not an OS security sandbox, and does not provide hard memory quotas. Arbitrary generated Python must not be sent through this interface.

```sh
python experiment_dispatch.py run request.json receipt.json --seconds 20
python experiment_dispatch.py replay receipt.json
python engine_readiness.py --output engine-readiness-results
```
The readiness job exercises actual activation, audit, positive/negative graph and constraint controls, universal modular claims, proof bundle replay, a deliberately unverified prose goal, and subprocess experiment receipts. It runs without a model key. It is an integration gate, not evidence that the engine can solve an open conjecture. Once the exact revision has green CI and the readiness artifact passes, proceed to a fresh Gallai research run and a separately frozen matched-budget evaluation. Preserve the revision, exact target, engine receipts and independent proof review. Do not mark the conjecture solved based on finite tests.
