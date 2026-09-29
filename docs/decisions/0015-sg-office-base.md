# 0015. SG Office: LibreOffice for Windows under wine-sg, installed on request

- **Status:** accepted, 2026-09-29
- **Date:** 2026-09-29
- **Deciders:** David (the requirements below, in his words where quoted);
  analysis and measurements by Claude

## Context

Microsoft Office may never run fully under Wine, so Stained Glass OS needs an
office suite of its own -- "SG Office" -- that works and looks as close as
possible to Microsoft 365's Word, Excel and PowerPoint, with Microsoft's file
formats by default and Excel "very, very close, including the same formula
support". David's requirements, as they arrived:

1. A drop-in: "a user of one has nothing new to learn; exact syntax works,
   not a close syntax but the real syntax of Excel"; the missing Excel
   functions implemented, not just documented.
2. VBA macros must run as in Excel and Word.
3. It must run on the Wine (Windows) side, "so it plays nice with the
   Windows-like environment" (file dialogs, the shell, clipboard, printing,
   fonts, look) -- preferably built from source with an open toolchain,
   otherwise the upstream Windows installer fetched at the user's request
   (the way "Get a web browser" works), never redistributed by us.
4. Files must open from mapped drives and network shares through the normal
   Open dialog.
5. ONLYOFFICE was proposed as an alternative base; if chosen, we would present
   it as "SG Office, based on ONLYOFFICE" with their logo kept.

## Options and evidence

Measured on 2026-09-29 with the formula corpus in sg-shell `office/parity`
(775 cases over 530 Excel functions, each an Excel-written formula with
Excel's documented result), a VBA corpus (`office/vba`, 44 Excel and 8 Word macros as
people write them), and a fidelity set (three .docx, .xlsx and .pptx files each,
made with python-docx/openpyxl/python-pptx: styles, lists, tables, images,
headers and footers, sections, comments; formulas, number formats, merged
cells, conditional formats, data validation, a table (ListObject) with
structured references, charts, names, freeze panes, comments, hyperlinks,
tab colours; layouts, bullets, tables, charts, pictures, notes), round-tripped.

| | LibreOffice 26.8.0 (Windows, TDF's MSI) + SG Office's payload | ONLYOFFICE 9.4.0 |
|---|---|---|
| Formula corpus | 714/775 match Excel. 26.8 has TEXTSPLIT, TEXTBEFORE/AFTER, VSTACK/HSTACK, TAKE/DROP, CHOOSEROWS/COLS, TOROW/TOCOL, WRAPROWS/COLS, EXPAND, REGEXTEST itself; our add-in, SG Office Functions, supplies 16 more (BINOM.DIST.RANGE, DBCS, the IM* hyperbolic and reciprocal functions, PERCENTOF, PHONETIC, REGEXEXTRACT/REPLACE, TRIMRANGE, VALUETOTEXT: 20 cases, measured by removing it) | 720/775 (DocumentBuilder, same JS engine as the editors) |
| LAMBDA, MAP, REDUCE, SCAN, BYROW/BYCOL, MAKEARRAY, GROUPBY/PIVOTBY | missing | missing (LET missing too) |
| Excel error values, 1900 leap-year dates, TRUE>100 ordering | LibreOffice's own (Err:502 shown for #NUM!, DATE(1900,1,1)=2) | Excel's |
| Dynamic arrays | Excel files' spilled ranges load as fixed array formulas; typing does not spill | spills |
| VBA | runs (LibreOffice's VBA support): 35 of 44 Excel and 6 of 8 Word corpus macros give Excel's/Word's result (gaps: CreateObject("Scripting.Dictionary") under Wine, On Error Resume Next over a division by zero pauses in the Basic IDE, ListObjects, ChartObjects, comments, Evaluate, Worksheets.Add(After:=), AutoFilter counts; Word InsertAfter, Tables.Cell, Bookmark ranges) | **does not run** (JavaScript macros only) |
| Fidelity set | every checked feature kept (differences only in representation: ARGB alpha, escaped number formats) | conditional-format colour scale, data validation and charts lost in .xlsx; .pptx not comparable (the unlicensed DocumentBuilder stamps "Unregistered Version") |
| Under wine-sg | installs from the MSI in 34 s; Calc/Writer/Impress GUI work; one msvcp140 stub fixed (wine-sg 0508); an intermittent crash creating a visible document with winedbg disabled, under investigation | installs; the UI renders, but opening a file raised a credentials prompt and showed an empty sheet |
| From source, open toolchain (Windows) | no: Windows builds need MSVC/clang-cl with Microsoft's SDK and CRT; LibreOffice's MinGW port was removed long ago (25.2's configure knows only MSC for Windows) | no: the desktop shell and converter also need MSVC; only the JS editors/engine (sdkjs, web-apps) build with an open toolchain |
| Our engine patches in option 2 | impossible (compiled C++ from TDF's MSI) | possible in principle (the engine is JavaScript in the install directory) |
| Look out of the box | Tabbed ribbon; we rearrange Calc's Home tab as Excel's (Styles with Format as Table, Cells, Editing) | closest to Microsoft 365 |
| Format as Table | 26.8's tables: header row, filter buttons, banded TableStyleMedium2, `Table1[Units]` references, saved as an Excel ListObject; no auto-expansion when typing below | tables supported |
| Licence | MPL-2.0; renaming is TDF's policy's preference | AGPL-3.0 + additional terms: keep notices, identify ONLYOFFICE as the original developer, no trademark licence; a rebrand is allowed |
| Mapped drives / shares | through Wine's own file dialogs and paths: a mapped drive letter opened (tested); UNC paths go through wine-sg's network code | (David reports it needs the full UNC path typed) |

## Decision

**LibreOffice for Windows, running under wine-sg, installed on the user's
request by "Get SG Office" from The Document Foundation's signed MSI (pinned
SHA-256), with SG Office's settings, templates, ribbon and SG Office Functions
applied on top.** The deciding facts are VBA (ONLYOFFICE cannot run it at all,
and a VBA runtime for it would be months of work) and that LibreOffice already
works under wine-sg while ONLYOFFICE did not open a file. Their Excel formula
results are close (714 vs 720 of 775), each better in different places.

A from-source Windows build is not feasible with an open toolchain, so engine
patches (LAMBDA and friends, Excel's error values, spilling, the financial
function bugs) cannot be carried: SG Office Functions closes what an add-in can
(functions that take values and return values or arrays), and the rest is
recorded in `office/parity/REPORT.md` as the honest list of gaps.

## Consequences

- SG Office's Excel gaps that need the engine stay open until LibreOffice
  fixes them upstream or a Windows build of our own becomes possible; each is
  in the corpus, so an upgrade that fixes one shows as an improvement.
- ONLYOFFICE's JavaScript engine is the one route to engine patches without a
  Windows toolchain. If its Wine problems are solved and VBA stops mattering
  (or gets a translator), this decision is worth revisiting with the same
  corpora.
- Updating LibreOffice is an sg-office package update: office.ini's version,
  URL and SHA-256 together, the ribbon regenerated from that version's
  notebookbar.ui, and the corpora re-run.
