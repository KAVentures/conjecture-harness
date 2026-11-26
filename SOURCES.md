# Research basis and evaluation

The prompt is an original synthesis of research practices, not a reproduction of proprietary system prompts. These examples inform its design; they do not prove that our prompt improves performance.

| Source | Design lesson | Limit |
|---|---|---|
| Yichen Huang, [Autonomous disproofs of the sum-product conjecture over R with GPT-5.5 Pro](https://arxiv.org/abs/2607.20525) (2026) | Simple plan, proof construction and review stages; 7/8 successful trials reported. | Specific rediscovery case; not evidence of general effectiveness or novelty of our prompt. |
| Donald Knuth, [Claude's Cycles](https://cs.stanford.edu/~knuth/papers/claude-cycles.pdf) (2026) | Reformulate, experiment, record failures and extract a general construction from patterns. | Guided case study, not a controlled prompt comparison. |
| OpenAI, [Disproof of the planar unit-distance conjecture](https://openai.com/index/model-disproves-discrete-geometry-conjecture/) (2026) | General-purpose reasoning and transfer across mathematics can produce new constructions. | Does not establish which prompts are necessary. |
| [Autonomous Mathematical Discovery in an Open-World Multi-Agent Environment](https://arxiv.org/abs/2608.23691) (2026) | Diverse mathematical approaches and exchange of concrete discoveries. | Multi-agent setting; a single chat cannot reproduce independence or compute scale. |
| [Advancing Mathematics Research with AI-Driven Formal Proof Search](https://arxiv.org/abs/2605.22763) (2026) | Formal proof search and verification can complement mathematical invention. | Tool-intensive system; formalization must match the target. |
| OpenAI, [Ten advances in mathematics and theoretical computer science](https://openai.com/index/ten-advances-in-mathematics/) (2026) | Frontier reasoning can address substantial research questions; scrutinize proofs and context. | Different models and budgets; no causal evidence for this prompt. |

## Test the prompt, not the size of the repository

Compare the same model, reasoning effort and tools under (A) ordinary problem-only prompting, (B) the prior harness, and (C) the standalone prompt. Optionally add (D) the executable engine. Freeze target statements, conditions and budget before testing; use multiple fresh chats per problem. Include both known-answer controls and independently selected unresolved problems, and report them separately. Avoid giving answer keys to the model. Randomize and blind qualified reviewers to condition.

Primary outcome: correct full proof or disproof of the actual target. Secondary: rigorously checked target-relevant intermediate results, first fatal gap, meaningful pivots, actual tool usage, time and compute. Separate instruction adherence from mathematical correctness and novelty. Do not reward verbosity, attempted lemmas, repository size, or self-reported confidence. Report negative results and uncertainty. No live comparative experiments have been completed for this prompt.

The previous software evaluation artifacts are preserved in [engine/evaluation/](engine/evaluation/).
