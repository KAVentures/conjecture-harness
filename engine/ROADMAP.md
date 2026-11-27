# Engine-first development roadmap

Prefer executable, reusable discovery mechanisms over conjecture-specific prompts. Keep the existing exact verification and immutable proof-state infrastructure. Avoid claiming "general invention" from narrowly selected demonstrations.

| Priority | Deliverable | Acceptance gate |
|---|---|---|
| P0 | Engine-first activation, mode selection, receipts, continuation | Host with shell actually executes relevant tools; unavailable hosts disclose fallback; prose fixed point remains unknown. |
| P0 | Generic combinatorial exact cover / edge partitions | Replay positive and complete negative certificates; malformed or truncated proofs rejected; budget exhaustion unknown. |
| P1 | Structural graph surgery and reducibility | Typed local rules with verified preconditions and lifts; discover candidate configurations from exact witnesses; test against adversarial instances. |
| P1 | Dynamic experimentation | Bounded isolated experiment runner with explicit input, code hash, time/memory limits, outputs, replay; no arbitrary worker code by default. |
| P1 | General lemma invention and evolutionary search | Diverse typed mechanisms, persistent negative evidence, noncircular bridges, recursive frontier selection, measured progress rather than prose count. |
| P1 | Theorem transfer | Structured quantified hypotheses, exact object maps, missing obligations, source locators, replayable supported bridges. |
| P2 | Formal proof export and review | Exact statement and assumptions match; independent proof checker; report unsupported prose honestly. |
| P2 | Matched-budget evaluation | Frozen historical controls and independently selected held-out tasks; compare ordinary prompting, prompt-only and full engine with same model/tools/compute; blinded review. |

Use Gallai, Shannon, permanent inequalities and number-theoretic problems as stress tests, not hardcoded core targets. The current patch implements P0, adds a first audited structural-surgery and monotone-transfer family, replayable declarative experiments, finite counterexample-driven budget evolution, and positive finite-cover Lean export. General graph transformations, arbitrary isolated experiment execution, universal lemma invention and theorem transfer remain open. No Lean build or comparative live-model evaluation is asserted. No open conjecture or effectiveness gain is asserted.
