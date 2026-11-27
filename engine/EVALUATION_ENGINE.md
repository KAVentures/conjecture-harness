# Full-engine historical evaluation arm

The existing historical evaluator retains its two-arm default. Opt in with
```sh
python historical_eval.py run tasks.json design.json worker-config.json trial --calls 4 --timeout 60 --full-engine
```
At least two model-call slots are required. The three arms are ordinary target-only prompting, full HARNESS.md prompt with reasoning-only fallback, and actual engine research with exact discharge and metareasoning. The engine spends earlier slots on proposal/adapter cycles, preserves states, logs and audits, then asks for a standalone human-readable answer in the final slot. In full mode only the final answer in every arm is presented for blinded review; intermediate outputs remain in private logs. No arm gets extra model-call slots. Engine may use fewer calls when it closes early. The usage.json records actual invocation counts and elapsed wall time; exact overhead and prompt lengths differ. This is a matched maximum call-count/timeout comparison, not equal realized tokens, wall-clock compute, or costs. Record provider usage externally and do not claim matched inference until measured. Trusted workers must be isolated externally. No live-model experiment has yet been run.

The frozen references, integrity checks, review coverage, paired engine-vs-control comparisons and external review still apply. Human reviewer independence and mathematical correctness cannot be inferred from hashes. Preregister the comparison before running and keep reference answers away from workers.
