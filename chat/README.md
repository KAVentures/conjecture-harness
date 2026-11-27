# Automatic chat activation

The user should normally supply only the repository link and conjecture.
Do not ask them to clone or upload a ZIP before trying the host's available
retrieval and execution tools. A URL cannot grant capabilities the host lacks.

## 1. Full engine, no git required

Read the root HARNESS.md. Resolve the default branch to an immutable 40-character
commit SHA (GitHub repository/branch lookup or equivalent). Use that same
revision for the instructions, source review, and all downloads.

If your Python or shell environment has network access, retrieve
`chat/bootstrap.py` from that revision using your supported file retrieval
tool. Inspect it. Run:

```sh
python chat/bootstrap.py --revision COMMIT_SHA --output harness-checkout
```

If only a browser/download tool has internet access, first try its direct
file-to-runtime download of the pinned archive:
`https://codeload.github.com/KAVentures/conjecture-harness/zip/COMMIT_SHA`.
Then use the same bootstrap with `--archive PATH` (it does not fetch again).
A GitHub Actions connector is another possible transfer route: the `chat-transport` job builds and tests a complete ZIP from the exact checkout, then uploads an artifact named `harness-chat-COMMIT_SHA` (30-day retention). Find a successful run for that SHA, list its artifacts, and download the matching artifact using the host connector. If the returned file can be mounted in the runtime, extract the outer artifact ZIP, then use its inner `harness-COMMIT_SHA.zip` with `--archive` and the digest from `SHA256SUMS`. Do not assume a connector file reference is a local filesystem path. If no host file handoff exists, try section 2 instead.

An independently known archive SHA-256 can be passed via `--sha256`.
A receipt records actual bytes and the requested revision; it is not proof of
authenticity or safety. Review trusted source before running it.

Run from the extracted `engine/`:

```sh
python engine_readiness.py --output readiness
python activate.py run --target "exact conjecture statement" --output research-run
python discovery.py research-run/state.json plan
python activate.py resume --output research-run
```

Use the full interactive loop from [ACTIVATION.md](../engine/ACTIVATION.md).
The AI itself can supply proposals; no external model API is required.
The normal engine's external workers require separately configured commands.

## 2. Connector/text-only acquisition (no network in runtime)

If archive transfer fails, try the host's GitHub connector, raw-text reader,
or equivalent to retrieve **chat/portable.py** at the pinned revision.
It is a generated, standard-library-only Python file containing actual
upstream exact cover, finite CSP and modular solvers and their replay logic.
This is the portable exact subset, not the full orchestration engine.

Prefer a connector's direct file-to-runtime transfer when supported. Otherwise
copy the returned **complete** UTF-8 source into a file in the Python runtime.
If the connector truncates content, retrieve consecutive line ranges or
complete bytes using the available file tool. Do not reconstruct missing
source from memory. Verify the copied file against the Git blob SHA from the
connector when available:
```python
import hashlib
from pathlib import Path
b = Path("portable.py").read_bytes()
print(hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest())
```
If verification fails, retry transfer rather than execute corrupt source.
Review the source (the embedded strings are real code) before execution.

```sh
python portable.py selftest
python portable.py run --target "exact conjecture statement" --output research-run
python portable.py solve --kind cover --spec claim.json --output research-run
python portable.py resume --output research-run
```

Kinds: `cover`, `constraint`, `modular`. The JSON spec formats and bounds are
the existing [cover](../engine/COMBINATORIAL_COVER.md) and
[constraint/modular](../engine/CONSTRAINT_DISCOVERY.md) formats.
The AI invents exact subclaims, writes spec JSON, runs solve, inspects
certificates and iterates. Use `--budget` within the upstream bounds.
`resume` and `audit` replay all stored certificates and report the immutable
root. Only a certificate for the exact canonical typed root may close it;
a finite experiment cannot settle a prose conjecture. This subset does not
include the full engine's proof graph, campaign or other adapters.

## 3. Native or reasoning fallback

If the host cannot transfer even this file, retrieve the relevant upstream
solver and its runtime dependency individually, or use native computation.
State exactly what ran. Do not request user intervention by default; offer it
only when actual retrieval and execution are blocked. No remote execution,
credentials, external model calls or conjecture publication are implied.

## Maintenance

Run `python chat/build.py` after changing any embedded module or portable
interface. CI checks source equivalence, exercises exact controls, and
tests the archive bootstrap with a local fixture (without network).
