# SG Office 2 -- QA fidelity harness + round-trip gate (dev/QA only, NEVER shipped)

This directory is the fidelity harness for our own office suite (ADR 0016). It
uses **ONLYOFFICE's engine as a rendering/round-trip oracle** -- "how an open
document should render" -- for QA comparison only.

**Hard rule:** the ONLYOFFICE binary is a third-party AGPL tool. It is **never**
installed system-wide, **never** committed to any repo, and **never** placed in
the OS or ISO. `fetch-oracle.sh` (and `make oracle`) download it into the
git-ignored `oracle/` path. Only the harness code + a small tracked corpus are
version-controlled.

## Quick start

    make test        # fetch oracle if needed, round-trip the corpus, gate vs baseline
    make baseline    # (re)write baseline.json from the current engine
    make corpus      # regenerate the independent corpus (needs the venv libs)

`make test` opens `corpus/src.{docx,xlsx,pptx}` in the engine, saves each back
to the same OOXML format, and checks a fixed feature set survived. Exit 0 =
gate pass; exit 1 = a feature the baseline recorded as preserved was lost.

Current score: **23/23 = 100.0/100** on the Phase 1 corpus (one file per format).

## The oracle

- Package: `onlyoffice-documentbuilder_amd64.deb`, version pinned **8.2.0-143**
- URL: https://download.onlyoffice.com/install/desktop/docbuilder/linux/onlyoffice-documentbuilder_amd64.deb
- SHA-256 (2026-09-29): `5dd570200cb72db9f59a4e31dc7ad8af5d2de979c194f45f4fc2a7785cf67d70`
- Runs **headless, no root, no X**: `dpkg-deb -x` extract, then
  `LD_LIBRARY_PATH=<dir> ./docbuilder script.docbuilder`. Ships `docbuilder`,
  `x2t` (OOXML/ODF/PDF converter), `sdkjs/` and `libdoctrenderer.so`.

## Two findings that shape the plan (measured 2026-09-29)

1. **Spreadsheets need an explicit recalc on open.** A passive open->save keeps
   the formula but writes no cached value; `Api.RecalculateAllFormulas()` (which
   an interactive open triggers) makes the engine compute -- e.g. `=SUM(B2:B3)`
   -> `7`, `=TEXTJOIN("-",TRUE,B2,B3)` -> `3-4`. The harness calls it for .xlsx.
   The read path uses the saved file's cached `<v>` (the live
   `GetRange(...).GetValue()` throws `TypeError: 'Vd'` in this build).

2. **The prebuilt `documentbuilder` runs the engine from V8 snapshots shipped
   beside the JS** (`sdkjs/<editor>/sdk-all.bin` and `sdk-all.cache`), so
   editing `sdk-all.js` next to them changes nothing. Without those two files
   the host loads the JS and caches its own code -- which is how our own
   engine runs. The engine is built from source, patched and gated in the
   `sg-office` engine repo (ADR 0016 addendum): our host (Debian's V8) plus our
   sdkjs passes this round-trip gate at 23/23, and the Excel corpus at
   713/775, with a patch (PERCENTOF) proven by the corpus.

## Three-way scored metric (per ADR 0016)

Per corpus document, score = round-trip feature preservation (implemented here)
+, when we render, rendered-page image similarity (x2t -> PDF -> PNG, SSIM), for
three renderers: **ours** (our from-source engine, once built), **msref** (MS
Office reference, the expected values), **oo** (ONLYOFFICE oracle). The formula
corpus (sg-shell `office/parity`, 775 cases) keeps its match/differ/missing
verdicts and is engine-independent. Phase 1 implements the round-trip half as a
gate; image-SSIM and the from-source "ours" engine follow.

## Files

- `fetch-oracle.sh` -- fetch + sha-verify the oracle into `oracle/` (git-ignored)
- `gen_corpus.py`   -- write the independent corpus with python-docx/openpyxl/python-pptx
- `roundtrip.py`    -- open->save->check each file; score; gate vs baseline
- `corpus/`         -- the tracked source documents (regenerate with `make corpus`)
- `baseline.json`   -- the gate baseline (per pinned oracle version)
- `Makefile`        -- `test` (gate), `baseline`, `corpus`, `oracle`, `clean`
