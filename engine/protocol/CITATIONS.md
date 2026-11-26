# Citation and provenance contract

## Cite this harness
Read CITATION.cff at the same revision as the protocol. Cite the actual version and immutable commit URL (or archive SHA-256 for local snapshots). Prefer a verified version-specific DOI if issued. Give credit independently of AI disclosure; neither implies authorship or endorsement. No DOI is required and none has been issued for this preview.

## Mathematical source ledger
Maintain research/references.json (schema 1; references array) plus research/SOURCES.md and research/CLAIMS.md. Each ledger record has key, type (article/book/inproceedings/misc/techreport), authors (actual names), title, year, role (target/theorem/related_work/method/software/data/novelty), state (checked/unverified), and at least one of url, doi or venue. Optional version, corporate_authors, locator, checked_on, evidence. Checked records require an actual page/theorem/revision, date of actual inspection and evidence describing what was examined and why it supports the claim. Unverified leads must not appear in the bibliography. Record each claim's source key, exact location, hypotheses and implication. A metadata match does not establish correctness or relevance. Check primary sources, not search snippets. Record failed access and limitations; avoid copying copyrighted works. Never invent identifiers, metadata or inspection evidence.

Generate paper/references.bib and, if useful, paper/references.tex from checked records; ensure all manuscript citations resolve and remove unchecked citations. Manually check source identities, hypotheses and statements even if automated validation passes.

## Every discovery must be citable
Before publishing, obtain the confirmed human author names, actual paper title, actual repository URL and actual manuscript URL (e.g. the immutable PDF or TeX file; never point at an absent artifact). Use a root CITATION.cff with CFF 1.2.0 and a preferred-citation describing the real paper. For an unpublished manuscript use type: unpublished, not article or an invented journal. Example template (replace every placeholder; not release metadata):

```yaml
cff-version: 1.2.0
message: Please cite the manuscript and/or reproducibility package.
title: "[Research package title]"
type: software
authors:
  - given-names: "[Confirmed given names]"
    family-names: "[Confirmed family names]"
repository-code: "[Actual repository URL]"
preferred-citation:
  type: unpublished
  title: "[Actual manuscript title]"
  authors:
    - given-names: "[Confirmed given names]"
      family-names: "[Confirmed family names]"
  url: "[Actual manuscript URL]"
```

Create root CITATION.bib with two distinct citation keys (paper and repository), and CITATION.md with the same entries and human-readable guidance. Add a "How to cite" section/link in README. Maintain citation-metadata.json as the canonical confirmed metadata; regenerate all three outputs consistently. In multi-conjecture repositories give every paper separate metadata and distinct keys, plus repository-level credit. Include actual year/version and verified DOI(s) where available; omit unknown values. Do not reuse a repository DOI for a different paper. Do not imply peer review or novelty. If a preprint or published article exists, use its actual bibliographic details after verification. Validate CFF against the official 1.2.0 schema using cffconvert --validate when available, otherwise explicitly report manual-only validation. Check title, authors, URLs and BibTeX against manuscript, remote tree and confirmed metadata. CFF validity alone cannot verify identity, authorship or DOI registration.

## DOI workflow
With user approval, archive a frozen tagged release through Zenodo or another appropriate archive, verify issued DOI and archived files, then update metadata in subsequent versions. No fake DOI, fake release, or assumed automatic integration. See https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files and https://citation-file-format.github.io/. Never attribute AI as an author; disclose contributions accurately.
