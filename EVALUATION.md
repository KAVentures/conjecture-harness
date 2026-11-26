# Discovery evaluation: certificate elicitation and exact tool baseline

This is a preliminary component-level evaluation, not a test of the entire discovery graph or open-conjecture solving. The generator produces seeded elementary affine, polynomial and graph controls, with exact reference answers replayed before running. Five recurring families are used; repeated templates and duplicate instances are possible, so this is not a held-out mathematical benchmark. Do not infer statistical generalization.

Three model arms use the same external command, exact statement, certificate contract, verifier, per-call timeout, output limit and maximum number of calls. Blind attempts get no previous answer, continuation gets the immediately preceding answer, and adaptive gets that answer plus an exact checker outcome and a rotating research instruction. All arms stop on valid proof or counterexample. A shuffled order is recorded; raw outputs, invalid certificates, abstentions, tool failures, calls and paired success counts are retained. No answer or expected label is in the task prompt. This is prompt separation, not filesystem/provider isolation; use a trusted stateless wrapper in a disposable restricted environment. Never give the worker access to the reference suite. Call caps are not matched inference tokens, actual compute, or cost. Record the actual model, version and inference settings before making comparisons.

Run from the repository root:

    python discovery_eval.py generate suite.json --seed 1729 --count 25
    python discovery_eval.py tools suite.json
    python discovery_eval.py run suite.json config.json trial --calls 4 --timeout 60 --order-seed 1 --model-label 'Actual model and configuration'

The model command must read stdin and return one certificate JSON object; unlike the discovery runner it must not return graph operations. The separate tool-only baseline invokes bounded exact proof/search adapters with no model calls. It is deliberately not compute-matched to the model arms. An interrupted trial has partial logs but no complete report; do not silently omit failures. Review logs for secrets before sharing.

No authenticated frontier model was available in the development runtime. Mock commands test the experimental plumbing, not reasoning performance. The first baseline (before coordinate-search improvements) resolved 21/25 controls, missing four shifted false polynomial inequalities. Exact suite fingerprint: 0f7b0fe5a0ff30bbe5f8d2e8457e67d4b6d6a657d68fa2d9207445605dcf9bc3. This identifies a concrete tool weakness; it does not demonstrate a discovery breakthrough.

Next scientific gate: independently curated or family-held-out targets with problem-specific exact endpoints, preregistered model/compute budgets, identical tool access, blinded review of non-machine-checkable claims, explicit novelty audit, and full-system ablation against ordinary prompting. Do not select test cases after seeing outcomes or reward disconnected lemmas as solved targets.
