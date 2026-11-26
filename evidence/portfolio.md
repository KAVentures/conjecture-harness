# Parallel portfolio regression

Local command: python -m unittest discover -s tests -v

Ran 122 tests in 18.621s — OK. Twelve new tests cover distinct modes, local ID collisions, exact claim deduplication, forward local references, blind/snapshot restrictions, untrusted review rejection, deterministic reconciliation, bounded calls and resume, proof discharge without worker calls, rejected batches, actual process overlap via a barrier, and preservation of successful peers after a failure. Mock commands only; no authenticated model runs or novel result.

Follow-up: strip prior route metadata from blind worker assignments even when the scheduler itself chooses blind mode. Ran 123 tests in 18.736s — OK. This is prompt/assignment minimization, not filesystem or provider isolation.
