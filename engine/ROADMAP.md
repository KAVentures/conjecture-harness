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

The opt-in historical evaluator now has a third full-engine arm with final-answer-only blinded review, actual invocation/elapsed logs and paired comparisons. It remains a matched call-cap protocol, not a measured matched-token benchmark. A finite integer dual discovery primitive also gives compact refutation certificates for combinatorial covers. See EVALUATION_ENGINE.md and COMBINATORIAL_COVER.md.

The next sweep adds general finite integer constraints (linear rows, Hall matching, allowed tables), exact positive/negative certificates, universal modular implications and checked recursive CRT obligation invention. These are domain primitives, not arbitrary mathematical proof search. See CONSTRAINT_DISCOVERY.md.

The engine now has an allowlisted bounded subprocess experiment interface, deterministic replay receipts, increasing finite-search budgets after unknown results, and a dedicated end-to-end readiness CI gate. Arbitrary code isolation, real model research effectiveness and independent universal proof review are still separate milestones.

Solution-first campaign: configured activation now runs bounded parallel research waves, preserves stagnation on resume, rotates root attacks and supports advisory complete-candidate referee logs. Remaining work: universal semantic proof checking, reliable literature/novelty tools, context compaction with exact proof-preserving archival, stronger experiment generation/isolation and matched-budget live-model effectiveness evaluation. No autonomous solving guarantee.

The campaign now also schedules allowlisted model-proposed experiments and returns advisory referee critiques and captured experiment summaries to later nonblind workers. Generic arbitrary experiment synthesis and isolation remain open; only declared exact schemas execute.
