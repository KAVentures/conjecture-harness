# Conjecture Harness

**A standalone research prompt for ChatGPT, Claude and other reasoning models.** It is designed to guide mathematical discovery, not to require a software installation.

## Use it

**[Open the research prompt →](HARNESS.md)** · **[Raw text](https://raw.githubusercontent.com/KAVentures/conjecture-harness/main/HARNESS.md)**

Paste the entire prompt into a fresh conversation, followed by your conjecture. Or ask:

> Read HARNESS.md in full from https://github.com/KAVentures/conjecture-harness and use it to prove or disprove [conjecture]. Start substantive research immediately.

If the AI cannot access the link, paste the prompt itself. When returning to an unresolved problem, say “continue” and retain its mathematical checkpoint. For diverse attempts, use separate fresh chats and cross-review their results.

The prompt directs the model to invent competing approaches, execute real mathematics, transfer literature, seek counterexamples, evolve hypotheses, pivot when stuck, and adversarially verify results. It can use native tools or problem-specific code, but neither is required.

## What's in this repository?

- [HARNESS.md](HARNESS.md): the complete prompt; the only required research document.
- [SOURCES.md](SOURCES.md): research inspiration, limitations, and how to test the prompt.
- [engine/](engine/): preserved optional mathematical software, tests, protocols and evaluation from the earlier architecture. Not required in chat. See [engine/ACTIVATION.md](engine/ACTIVATION.md) if you want to run it.

The prompt is experimental, not a guaranteed theorem prover. A URL alone cannot enforce instructions in every AI host; pasting the full prompt is the reliable way to provide the instructions. No comparative effectiveness gain has yet been established. Proof and novelty require independent scrutiny.

MIT license. Cite the revision used.
