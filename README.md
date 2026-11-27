# Conjecture Harness

**Engine-first mathematical discovery for AI reasoning models.** A standalone research contract plus executable exact solvers, adaptive research orchestration, proof graphs and independent certificate replay.

## Start here

Ask your AI:

> Read HARNESS.md in full from https://github.com/KAVentures/conjecture-harness and use engine mode to prove or disprove [exact conjecture]. Execute relevant capabilities, preserve the proof frontier, and continue until a verified result or an honest stopping condition.

[Read the canonical instructions](HARNESS.md) · [Capability registry](engine/CAPABILITIES.json) · [Engine activation](engine/ACTIVATION.md)

If the host has a checkout and shell, run from engine/:

```sh
python activate.py plan --target "exact mathematical statement"
python activate.py run --target "exact mathematical statement" --output research-run
python activate.py resume --output research-run
```

A configured trusted model worker is optional. Without one, the exact pass makes no model calls. Natural-language targets need justified typed subclaims; a fixed point is not a solution. In chat without a checkout, use native computation and consult relevant capability documentation; disclose what actually ran.

## Architecture

- HARNESS.md: required engine-first research contract for every host.
- engine/: flagship executable discovery engine, exact mathematics, persistent frontier, adaptive allocation, certificate checking and evaluation.
- [Engine roadmap](engine/ROADMAP.md): priorities and falsifiable completion gates.
- SOURCES.md: research inspiration and evaluation caveats.

The engine is experimental. It does not guarantee a proof or novel result, and comparative effectiveness has not yet been established. A repository URL cannot grant shell access or enforce host instructions. Proof and novelty require independent scrutiny.

MIT license. Cite the revision used.
