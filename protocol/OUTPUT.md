# Output and publication contract

Each conjecture has its own research package; multi-problem repositories have a root index and separate conjectures/<id>/ directories.

```
README.md                 # result, precise status, reproduction and citation links
target.json               # exact immutable statement and provenance
STATUS.json               # research status, novelty, verification, human review
research/STATE.md         # checkpoint and next tests
research/PROOF_STATE.json # proof-state graph for discovery runs (or explicit text equivalent)
research/ATTEMPTS.md      # routes, derivations, failures and evidence
research/SOURCES.md       # dated search queries and source audit
research/CLAIMS.md        # claims, dependencies, precise source locations
research/REVIEW.md        # independent/self/formal checks and open gaps
research/references.json  # canonical source ledger
paper/paper.tex           # complete candidate or explicitly incomplete draft
paper/references.bib      # mathematical references
paper/references.tex      # optional generated LaTeX bibliography
paper/paper.pdf           # only if actually compiled and inspected
repro/README.md           # exact commands, dependencies, expected/actual results
repro/                    # machine-readable inputs, verifiers, logs as applicable
AUTHORSHIP.md             # confirmed human authors, AI disclosure, approval status
citation-metadata.json    # confirmed title, authors, URLs, actual version/DOIs
CITATION.cff              # REQUIRED for public discovery; preferred paper citation
CITATION.bib              # REQUIRED: distinct paper and repository entries
CITATION.md               # REQUIRED: readable guidance for citing both artifacts
manifest.json             # hashes and file sizes; integrity only
```

## Manuscript
Include title, confirmed author or explicit draft placeholder, abstract scoped to actual status, precise original statement and definitions, relevant prior work, main claim and rigorous proof/disproof, limitations, reproducibility instructions, acknowledgments/AI disclosure and verified references. Mark incomplete manuscripts visibly; do not write a solved abstract when gaps remain. Do not fabricate dates, affiliations, ORCID, logs or peer review. AI is not an author; credit actual assistance. Confirm the human's contributions, consent, review and venue-specific authorship policy. If review is pending, say so. Suggested disclosure: "Generative AI (ChatGPT, model/version if known) assisted with [actual activities]. Human review [actual status]." Never infer approval.

## Reproducibility
Include exact code/data for computational claims, pinned dependencies and tool versions, commands, seeds, expected results and actual logs. Pure analytic proofs require checkable derivations, not invented computational experiments. Compile TeX without shell escape when possible, inspect the resulting PDF and report any uncompiled status. Compilation does not verify mathematics. Freeze exact target and candidate hashes, replay verifiers in a clean environment and check source references. The manifest is an integrity inventory, not a signature, proof or novelty attestation.

## Public release gate
Before publication, review exact theorem correspondence, open gaps, provenance, citation files, authorship, license and visibility, private/secret data and claims. Every public discovery MUST contain CFF, BibTeX (both entries), readable citation instructions and verified links. Ensure paper title and authors match manuscript and metadata; label unpublished/unreviewed papers accurately. If no DOI exists omit it. Verify author credit, user approval and actual destination. If tools support GitHub creation, create the agreed repository or populate the user-designated repo; otherwise supply a complete ZIP and request an empty repo if needed. Preserve existing files, use branch/PR for existing repositories, never force push. A public draft PR is public. Verify remote files, citation metadata and actual CI outcomes; never report pending checks as passed. Do not submit to journals/arXiv without separate explicit approval. License research artifacts only with confirmed terms and rights; the harness license does not carry over.

If tools do not permit file generation, deliver text and a file-by-file plan; report what is unverified. Do not fabricate a repository, paper PDF, CI result or DOI. Refer to CITATIONS.md.
