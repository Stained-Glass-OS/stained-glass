# 0016. Our own office suite: an editable engine, based on ONLYOFFICE

- **Status:** accepted, 2026-09-29
- **Date:** 2026-09-29
- **Deciders:** David (the mandate below, in his words where quoted; approved
  Option A and all four go/no-go items on 2026-09-29); Phase 0 analysis, oracle
  install and measurements by Claude.

> **Decision confirmed (2026-09-29).** David approved **Option A** (an
> attributed AGPL derivative of ONLYOFFICE's open engine, built natively on
> Linux); the suite is **AGPL-3.0 with ONLYOFFICE attribution**; named **"SG
> Office, based on ONLYOFFICE"**, distinct from the LibreOffice-based
> `sg-office`; **Phase 1** proceeds -- a buildable native engine + minimal
> SG-themed shell that opens/round-trips one .docx/.xlsx/.pptx, plus the
> fidelity harness as a `make test-*` gate, before any parity feature work.

## Context

ADR [0015](0015-sg-office-base.md) chose, for the *shipping* suite, LibreOffice
for Windows run under wine-sg and installed on request from The Document
Foundation's MSI. That decision's own recorded weakness is decisive here:

> A from-source Windows build is not feasible with an open toolchain, so engine
> patches (LAMBDA and friends, Excel's error values, spilling, the financial
> function bugs) **cannot be carried** [...] the rest is recorded in
> `office/parity/REPORT.md` as the honest list of gaps.

We ship an engine **we cannot edit.** LibreOffice's Windows build needs MSVC
with Microsoft's SDK/CRT; its MinGW cross-build was removed upstream years ago
(25.2's `configure` knows only MSC for Windows). Every engine-level Excel gap
in 0015 (dynamic-array spilling, the LAMBDA/MAP/REDUCE/SCAN family, Excel's
error values and date/ordering quirks) is therefore frozen until TDF fixes it.

David's mandate (2026-09-29), verbatim in intent: build **our own** office
suite for SG OS, an editable, buildable-from-source Documents / Spreadsheets /
Presentations that renders and round-trips .docx/.xlsx/.pptx (and ODF)
neck-and-neck with Microsoft Office, **using ONLYOFFICE as the key reference**.
0015's own consequences already point here:

> ONLYOFFICE's JavaScript engine is the one route to engine patches without a
> Windows toolchain. If its Wine problems are solved [...] this decision is
> worth revisiting with the same corpora.

0015 rejected ONLYOFFICE for *shipping* because it could not run VBA at all and,
run **as a Windows build under Wine**, gave a credentials prompt and an empty
sheet. Neither objection binds the new mandate: we are not shipping ONLYOFFICE's
Windows binary under Wine, we are building its **open engine from source,
natively on Linux**, editing it, and theming our own shell over it. The Wine
wall was a property of running someone else's Windows build, not of the engine.

The governing licensing rule ([[licensing-reimplementation-rule]], ADR 0004)
stands: our code is never Microsoft's; the core OS stays open source; we never
ship third-party or Microsoft binaries in the image. ONLYOFFICE is AGPL-3.0 --
*more* copyleft than SG OS's usual LGPL/MPL, not less open -- so building on it
keeps us open source. It is a third party's code, so any derivative must be a
properly attributed AGPL derivative, and the ONLYOFFICE binary we install as a
QA oracle stays in a dev/QA area, **never in the OS or ISO.**

## Options

### A. An attributed AGPL derivative of ONLYOFFICE's open engine

Fork ONLYOFFICE's `core` (C++ conversion + calc-adjacent code, `x2t`,
DocumentBuilder) and `sdkjs` (the JavaScript Word/Cell/Slide document engines),
build them from source on Linux with gcc + node, put our own native shell and
SG Office theming over the top, and patch the engine where Excel fidelity
demands it. Our suite becomes AGPL-3.0, which is consistent with an open-source
core and is what David proposed ("SG Office, based on ONLYOFFICE").

- **Cost/time:** editor rendering + round-trip for all three formats on **week
  one** (the engine already does it). The work is the shell, the theming, the
  sg-shell integration, and then the fidelity/feature grind. Order of a few
  weeks to a themed, integrated, round-tripping suite; parity work is open-ended
  but starts from a high base (see Evidence: 720/775 formula cases).
- **Obligations:** carry ONLYOFFICE's AGPL notices and "based on ONLYOFFICE /
  original developer Ascensio System SIA" attribution; no MS or ONLYOFFICE
  trademark misuse; track our fork against upstream so security fixes merge; the
  whole suite is AGPL (fine -- it is a separate package, not the LGPL core).

### B. A clean-room reimplementation, ONLYOFFICE only as reference

Read ONLYOFFICE (and the public OOXML/ODF specs) to *learn how* a feature
should behave, then write every line ourselves -- our own OOXML/ODF model, our
own layout/render, our own formula engine -- shipping under a licence of our
choosing, unencumbered by AGPL.

- **Cost/time:** a full-fidelity OOXML/ODF stack is a multi-year effort for a
  team; for this project it means **no round-tripping suite for a very long
  time.** OOXML alone is ~6000 pages; the Excel calc engine, the DrawingML
  renderer, and .pptx layout are each large subsystems. LibreOffice and
  ONLYOFFICE each represent hundreds of person-years.
- **Upside:** total licensing freedom; no AGPL; no upstream to track.

### C. (status quo, for reference) keep shipping LibreOffice-under-Wine only

Do nothing new. Rejected by the mandate: the engine stays uneditable and the
0015 gaps stay frozen. Retained *as the interim shipping suite* until ours is
proven -- this ADR does not touch `office/` (sg-office).

## Decision (recommended, pending go/no-go)

**Option A: an attributed AGPL derivative of ONLYOFFICE's open engine, built
from source natively on Linux, with our own SG-Office-themed shell.**

Rationale, honestly weighed:

- The mandate is fidelity **neck-and-neck with MS Office**. Option B cannot
  reach that this decade with this team; Option A starts at ~93% of the formula
  corpus and full three-format round-trip on day one (Evidence below).
- The one real reason to prefer B -- licence freedom -- does not apply: an
  open-source core *wants* copyleft, and AGPL for a separate application package
  is compatible with everything else we ship. We are not selling a proprietary
  fork.
- "Editable by us" is satisfied: the engine builds with gcc + node, and its
  document/calc logic is JavaScript in the install tree -- exactly the property
  0015 said was "the one route to engine patches without a Windows toolchain."
- The VBA objection from 0015 is deferred, not fatal: we run natively (no Wine
  credentials/empty-sheet wall), and macros are a later phase (the Excel-syntax
  layer and a VBA path are discussed under Architecture). Interim VBA users keep
  the LibreOffice suite until ours catches up.

Option A does **not** mean shipping ONLYOFFICE. It means our own repository, our
own build, our own shell and theme, our own patches, correctly attributed.

## Evidence (what actually ran, 2026-09-29)

Toolchain on the dev box: `gcc (Debian 14.2.0-19) 14.2.0`, `node v20.19.2`,
`python3 3.11.10`. ONLYOFFICE `build_tools`, `core`, `sdkjs`, `web-apps` and
`DesktopEditors` are **AGPL-3.0**; `build_tools` orchestrates the Linux build
with Python + node/grunt + gcc/qmake (no MSVC on Linux) -- confirmed from the
repos. This is the editable/open-toolchain property the mandate requires.

**Oracle installed and proven headless (no root, no X):** downloaded
`onlyoffice-documentbuilder_amd64.deb` **8.2.0-143** (81 MB) from
`download.onlyoffice.com`, extracted with `dpkg-deb -x` into the dev/QA area
`office-qa/oracle/` (never installed system-wide, never in the image). The tree
contains `docbuilder`, `x2t` (the OOXML/ODF converter), `sdkjs` (**the JS
engine, present as source-shipped script**), `libdoctrenderer.so`, and the ICU
data. A smoke script:

```
builder.CreateFile("docx");
Api.GetDocument().GetElement(0).AddText("Hello from the SG Office oracle");
builder.SaveFile("docx", "out.docx");  builder.CloseFile();
```

run as `LD_LIBRARY_PATH=. ./docbuilder smoke.docbuilder` produced a valid 25 KB
`.docx`, exit 0, on a headless host with no display. Creating an `.xlsx` with a
`=TEXTJOIN(...)` formula and saving it also succeeded. **Known quirk:** reading
a cell back with `GetRange("A3").GetValue()` after `OpenFile` on an `.xlsx`
throws `TypeError: Cannot read property 'Vd'` in this build -- so the fidelity
harness reads values via conversion (x2t / rendered output), not the live
GetValue API. Noted so it is not re-litigated.

**Formula baseline already high:** 0015 measured ONLYOFFICE's engine
(DocumentBuilder, the same sdkjs used by the editors) at **720/775** cases
matching Excel on our corpus -- ahead of LibreOffice 26.8's 714, and it has
Excel's error values, 1900-leap-year dates and TRUE>100 ordering, and it
*spills* dynamic arrays (LibreOffice does not). LAMBDA/MAP/REDUCE/SCAN/LET are
still missing upstream -- but now they are ours to add.

## Proposed architecture

```
  sg-office2  (new package, AGPL-3.0, "SG Office, based on ONLYOFFICE")
  =========================================================================
  Shell (native Linux; SG Office theming; our code)
    - three entry programs: Documents / Spreadsheets / Presentations
    - hosts the JS editors offline (CEF, as ONLYOFFICE's desktop does) OR a
      thinner host if we can avoid a full Chromium -- to be settled in Phase 1
    - Start-menu entries, window class, icons, ribbon = SG Office look
  Engine (our fork of ONLYOFFICE core + sdkjs; built with gcc + node)
    - sdkjs: Word/Cell/Slide document + layout + calc engines (JavaScript)
    - core: x2t converter (OOXML/ODF/PDF <-> internal "bin"), DocumentBuilder
    - OUR PATCHES land here: LAMBDA family, Excel error names, extra functions
  SG Office compatibility layer (carried/adapted from office/)
    - Excel-syntax + MS-format defaults: default to .docx/.xlsx/.pptx, Excel
      error-name display, number formats, ribbon arrangement
    - SG Office Functions: the add-in's 16-20 functions become native sdkjs
      functions (JS -> JS, no UNO bridge), so they move *into* the engine
    - VBA: later phase; native gives us room for a real VBA path vs the
      LibreOffice-under-Wine bridge that 0015 used
  sg-shell integration
    - file associations + Default apps: reuse office/defaults/*.reg pattern,
      but pointed at native launchers (a wine-side .exe shim exec'ing the
      native binary, matching how the shell launches things, OR native desktop
      entries -- Phase 1 decides which fits sg-shell's launcher model)
    - Open/Save go through the normal dialogs; mapped drives / UNC as today
```

Why native, not under Wine: 0015's ONLYOFFICE failure (credentials prompt +
empty sheet) was its **Windows build under Wine**. Building the Linux engine
natively removes that entire failure mode and gives us gcc/node editability.
The cost is that our shell is a native Linux app in a Windows-like shell; the
launcher-shim question (wine .exe stub vs native entry) is the one integration
detail Phase 1 must resolve, and sg-shell already launches a mix.

How the `office/` work carries over: the parity corpus (775 cases), the VBA
corpus, and the fidelity set are engine-independent and move verbatim into the
new harness. SG Office Functions' *logic* is already written and tested
(`office/functions/`); reimplementing those functions as native sdkjs functions
is a port, not a rewrite. The MS-format defaults and ribbon arrangement are
configuration we re-express against the new shell.

## QA rendering-fidelity oracle and harness (Phase 0 deliverable)

- **Oracle:** the extracted `documentbuilder` (above), driven headlessly, in
  `office-qa/`. Never shipped. It renders a document the way ONLYOFFICE's engine
  intends -- the reference for "how an open document *should* render" per the
  mandate ("for QA comparison only").
- **Three-way scored metric:** for each corpus file, compare (1) **ours**
  (once it exists), (2) an **MS Office reference** rendering (the expected
  values baked into the corpus, from Office's documented behaviour / reference
  renders), and (3) **ONLYOFFICE** (oracle). Score per document = fraction of
  checked features preserved on round-trip + rendered-page image similarity
  (rasterise via x2t->PDF->PNG, structural-similarity index), reported 0-100.
  The formula corpus keeps its existing match/differ/missing verdicts. The
  harness scaffold and its `make` gate are proposed for Phase 1; Phase 0 stands
  up the oracle and the directory (`office-qa/`) and this scoring definition.

## Consequences

- **Makes easy:** editing the engine at last (LAMBDA family, error values,
  spilling are ours); full three-format round-trip from day one; a fidelity
  score we can drive up and gate on.
- **Makes hard / obliges:** we take on an AGPL fork we must track against
  upstream for security; the native-shell-in-a-Windows-shell integration is new
  work; VBA parity is a real project deferred to a later phase; a full Chromium
  (CEF) host may be heavy for the image -- to be assessed in Phase 1.
- **Does not touch** the shipping `sg-office` (LibreOffice-under-Wine, ADR
  0015), which remains the interim suite until ours is proven. No regression to
  what ships today.
- **Debt / revisit:** if Phase 1 finds the native host unacceptably heavy, or
  the launcher-shim integration intractable, revisit with the same corpora.
- **Licence:** the new suite is AGPL-3.0 with ONLYOFFICE attribution; the OS
  core is unchanged; nothing third-party enters the ISO. The oracle is a dev
  tool only.

## The go/no-go this ADR asks for

1. **Base choice:** approve **Option A** (AGPL ONLYOFFICE derivative) over
   Option B (clean-room)? Recommended: **A.**
2. **Licence:** accept that our suite is **AGPL-3.0** with ONLYOFFICE
   attribution (kept notices, "based on ONLYOFFICE", original developer named)?
3. **Naming:** "SG Office, based on ONLYOFFICE" (as David proposed in 0015 for
   the ONLYOFFICE path), distinct from the interim LibreOffice-based sg-office?
4. **Scope of Phase 1:** stand up a buildable native engine + minimal themed
   shell that opens and round-trips one .docx/.xlsx/.pptx, plus the fidelity
   harness as a `make test-*` gate -- before any parity feature work?

## Addendum (2026-09-30): how the engine is built (M2)

Measured while building it; each point is a decision the build now depends on.

- **Sources, pinned.** ONLYOFFICE `sdkjs`, `core`, `web-apps` and `build_tools`
  at tag `v8.2.0.143`, each pinned by commit in the engine repo's
  `upstream.conf` (the version our dev/QA oracle is). The third-party sources
  core compiles in (gumbo, katana, harfbuzz, hunspell) come at the commits
  upstream's own fetch scripts pin; `hyphen`, which upstream clones unpinned,
  is pinned by us. Moving to ONLYOFFICE 9.x is a later, measured step (its
  core already carries a V8 12 path).
- **Our changes are a patch series** (`patches/sdkjs/`, `patches/core/`, each
  with a `series`), applied to the pinned upstream at build time -- the
  wine-sg model: every change we make is a reviewable, attributable file, and
  rebasing onto a new upstream is mechanical.
- **The JS engine** builds with node and Google Closure Compiler's native
  binary from npm (Apache-2.0; no Java, no Microsoft tools) in ~6 minutes.
  Built unpatched, it reproduces upstream's builder tree file for file (bar
  the V8 snapshots, code caches and per-machine font tables, which are
  generated at install).
- **The prebuilt host ignores on-disk JS.** Upstream ships `sdk-all.bin`
  (a V8 startup snapshot) and `sdk-all.cache` per editor, and the host runs
  those; editing `sdk-all.js` beside them changes nothing (the Phase 0 probe).
  Without them the host loads our `sdk-all-min.js`/`sdk-all.js` and caches
  its own code. `x2t -create-js-snapshots` regenerates snapshots from our JS.
- **The native core builds against Debian, not bundled libraries**, in an
  `sg_debian` qmake mode our core patches add:
  - **V8 is Debian's** -- the one in `libnode` (V8 11.3, nodejs 20), built
    without pointer compression or sandbox. Upstream builds V8 8.9 from
    Chromium's depot_tools with Google's bundled clang; libnode instead gives
    an open, distribution-maintained V8 that gets Debian's security updates,
    and it exports everything doctrenderer uses, `SnapshotCreator` included
    (a standalone embedder run on it, Intl included, before the port).
    doctrenderer's V8 layer is ~1,750 lines; the port replaces V8-internal
    `src/base` calls with sysconf/getrlimit and uses `DisposePlatform`.
  - ICU 76, OpenSSL 3.5, zlib, Boost 1.83 from Debian in place of the bundled
    ICU 58, OpenSSL, zlib 1.2.11 (which has known CVEs) and Boost 1.72.
  - GCC 14 turned several C diagnostics into errors; upstream's bundled C
    (cximage's codecs, minizip) keeps them warnings in `sg_debian`, as with
    the older GCC upstream uses. Missing standard headers (`<cfloat>`,
    `<array>`) are added.
  - **Debt:** cximage's bundled image codecs (jasper, libjpeg, libpng,
    libtiff...) should come from Debian too; tracked in the engine repo.
- **Builds run in a rootless trixie build root** (`mmdebstrap --mode=unshare`,
  run with `bwrap` as the user), niced at `-j3`, under `/var/tmp/sgoffice`.
- **The engine is gated by what it computes.** sg-shell's Excel corpus (775
  cases over 530 functions) runs through our engine: 711 match Excel on
  unpatched 8.2, 713 with our first patch (PERCENTOF). The corpus found real
  ONLYOFFICE bugs we can now fix -- `MDETERM({3,6,1;1,1,0;3,10,2})` gives -36
  (the determinant is 1), `"a"<"B"` is FALSE (Excel compares text without
  case), `FLOOR(-2.5,2)` is #NUM! (Excel 2010+: -4).
- **ONLYOFFICE's Section 7 terms bind the suite** (the engine repo's NOTICE):
  the ONLYOFFICE logo is retained when distributing (7(b)) -- SG Office shows
  it in its About box, matching "SG Office, based on ONLYOFFICE, logo kept";
  no trademark licence (7(e)); ONLYOFFICE's GUI art is CC BY-SA 4.0.
- **Editors' host (for M3):** the desktop editors need a browser engine;
  upstream's desktop app uses prebuilt CEF binaries, which we will not ship.
  The shell will host the editors in a browser engine Debian builds from
  source (QtWebEngine or WebKitGTK), in a frameless window that draws its own
  SG-styled title bar (sg-compositor gives native X11 windows taskbar entries
  but no frame).
