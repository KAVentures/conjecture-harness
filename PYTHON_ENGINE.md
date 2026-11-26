# Optional Python engine

The primary workflow is the chat-first protocol; the Python orchestrator is optional and requires Python 3.10+ (standard library). It is an experimental research tool, not a validated autonomous solver.

## Quick start

```sh
python -m unittest discover -s tests -v
python benchmarks.py
python harness.py shannon --plan
python harness.py lih-wang --plan
python harness.py example --target-file targets/example.json --plan
```

The exact benchmark finds the known maxima 2 and 5 for powers one and two of T5, with independent witness replay. The tests compare clique search against brute force on 135 small random graphs and cross-check 16 rational permanent instances. These are bounded implementation checks, not novelty or proof of a full capacity result.

## Live research

Copy config.example.json to config.json and set two trusted command arrays. Each accepts a UTF-8 prompt on stdin and returns one JSON object on stdout; diagnostics go to stderr. The optional agent_adapter.py wraps installed authenticated Codex/Claude CLIs; neither wrapper has been live-tested. Use separate providers for generation/review if possible. Configure a least-privilege disposable environment and budget before use.

```sh
python harness.py shannon --config config.json --rounds 6 --workers 4 --seed 17 --max-attempts 24 --max-seconds 14400
```

The scheduler combines forced exploration and adaptive allocation, assigns at least one prompt-blind worker per round, and rewards only independently replayed evidence. Target fingerprints bind records to definitions; completed records reload in logical assignment order. Seeds control scheduling, not provider sampling. Attempt caps apply per invocation, each with worker and reviewer; timeouts are cooperative, not billing/token/OS resource limits. Output limits are polled. POSIX process groups are terminated on timeout/completion; Windows descendants may escape. Separate work directories are not a security sandbox. Agents may access other data if allowed; blind prompts are not benchmark-grade isolation. Use trusted commands, restricted credentials and a disposable sandbox. Review run logs before sharing; do not publish credentials or private information. Remove a stale coordinator lock only after confirming no process is active.

## Custom conjecture
Make a target JSON matching targets/example.json, with a new ID, precise statement, goals, references and distinct routes. Built-in IDs are bound to their original definitions. General targets have no exact checker; review output remains unverified. Do not promote a free-text proof solely on model approval.

## Exact checkers and experiments
- python verify.py shannon witness.json — verifies pairwise distinguishability, lexicographic 2-subsets of 0..4 numbered 0–9, and compares m^3 > 12^n exactly. Independent bitmask replay; only a lower bound, never the full asymptotic capacity.
- python verify.py lih-wang witness.json — exact rational doubly stochastic matrix (n=3..12, t in [1/2,1]); Ryser permanent gap. Independent permutation replay limited to n<=8. Positive exact gaps remain pending statement and research review.
- python experiments.py shannon --seed 17 --trials 3500 --out evidence/shannon.json — random greedy search in powers 2 and 3 followed by concatenation, not direct length-five optimization.
- python experiments.py lih-wang --seed 17 --trials 250 --out evidence/lih-wang.json — random rational mixtures of permutation matrices, not exhaustive.

The shipped finite experiments and checkers do not certify a general theorem. Model approval is not proof, and there is no SOLVED status. For arbitrary targets, write problem-specific checkers and use formal proof assistants or independent expert review. Literature discovery is delegated to actual agent tools; no built-in retrieval pipeline or authenticated live model validation exists yet.
