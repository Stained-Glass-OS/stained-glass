# SG Office 2 -- QA rendering-fidelity oracle (dev/QA only, NEVER shipped)

This directory holds the harness for measuring our own office suite's document
fidelity (see ADR 0016). It uses **ONLYOFFICE DocumentBuilder as a rendering
oracle** -- "how an open document should render" -- for QA comparison only.

**Hard rule:** the ONLYOFFICE binary is a third-party AGPL tool. It is **never**
installed system-wide, **never** committed to any repo, and **never** placed in
the OS or ISO. `fetch-oracle.sh` downloads it into a git-ignored dev/QA path
outside the image. Only this harness code is version-controlled.

## The oracle

- Package: `onlyoffice-documentbuilder_amd64.deb`
- Version pinned: **8.2.0-143**
- URL: https://download.onlyoffice.com/install/desktop/docbuilder/linux/onlyoffice-documentbuilder_amd64.deb
- SHA-256 (2026-09-29): `5dd570200cb72db9f59a4e31dc7ad8af5d2de979c194f45f4fc2a7785cf67d70`
- Runs headless, no root, no X: extract with `dpkg-deb -x`, run
  `LD_LIBRARY_PATH=<dir> ./docbuilder script.docbuilder`.
- Known quirk (this build): `GetRange(...).GetValue()` after `OpenFile` on an
  .xlsx throws `TypeError: Cannot read property 'Vd'`. Read values via
  conversion (x2t -> PDF/CSV) or rendered output, not the live GetValue API.

## Three-way scored metric (per ADR 0016)

For each corpus document, score = mean of:
  (1) round-trip feature preservation (fraction of checked features kept), and
  (2) rendered-page image similarity (x2t -> PDF -> PNG, SSIM),
reported 0-100, for three renderers:
  - **ours**   -- our ONLYOFFICE-derived engine (once it exists)
  - **msref**  -- Microsoft Office reference (expected values in the corpus)
  - **oo**     -- ONLYOFFICE oracle (this tool)
The formula corpus (sg-shell office/parity, 775 cases) keeps its existing
match/differ/missing verdicts and is engine-independent.

## Status

Phase 0: oracle installed and smoke-tested; scoring defined. The scored harness
runner and its `make test-*` gate land in Phase 1, after the lead's go/no-go on
the base (ADR 0016).
