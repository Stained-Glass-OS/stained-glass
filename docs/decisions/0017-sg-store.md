# 0017. SG Store: an application store that installs Windows apps first

- **Status:** accepted (design; implementation staged in sg-shell `src/store/`)
- **Date:** 2026-09-29
- **Deciders:** David Hamner (intent), Stained Glass OS contributors
- **Relates to:** [ADR 0004](0004-licensing.md) (licensing), [ADR 0012](0012-principals-and-elevation.md) (elevation), sg-shell "Get a web browser" and "Get SG Office"

## Context

Stained Glass OS can already fetch and install specific programs on demand:
"Get a web browser" (`sg-shell/src/browser/`) downloads Firefox/Chrome/Brave
from the maker, checked against a pinned SHA-256 that comes from the winget
community repository, and "Get SG Office" (`sg-shell/office/setup/`) downloads
The Document Foundation's LibreOffice MSI, checked against a SHA-256 pinned in
`office.ini`, and installs it silently for all users, then lays our settings on
top. Both prove the pattern David wants generalised: **we never ship or
redistribute a third-party or Microsoft binary in the OS or ISO; we download it
from the vendor at the user's request and run it only if it is exactly the file
the vendor published.** Our own builds may be hosted on our apt repo /
freesoft.page.

David asked for a store "kinda like our Get-a-browser flow" that can point at
third-party sources/installers **and** at our own builds (SG Office, our
browser builds), with three hard steers:

1. **Windows apps are the ideal path.** For any app, the store should steer the
   user to the Windows (wine-sg) version by default.
2. **Native Linux apps are supported but a last resort.** They must be hidden /
   de-emphasised behind an "advanced/Linux" affordance, never the default
   suggestion.
3. **The store checks for and installs per-app updates** (the web browsers
   especially).

And one boundary: **OS updates keep their current path** (staged, install on
reboot; Control Panel > Windows Update / Settings > Update & Security over apt
history and `sg-settingsctl`/`sg-admind`). The store must **not** take over or
duplicate OS-update handling.

## Options

### A. A brand-new engine and catalog format

Design a fresh manifest/catalog schema (YAML/JSON) and a fresh downloader,
hasher, and silent-installer runner. Costs: re-implements exactly what
`browser/fetch.c` + `browser/manifest.c` already do and have a mutation-tested
gate for; two code paths to keep secure (SHA-256 enforcement, elevation,
argument quoting); more surface for a redistribution mistake.

### B. Reuse the browser engine; catalog in the registry, like browser Offers

Compile `src/browser/fetch.c` and `src/browser/manifest.c` into `sg-store` and
drive them from a catalog of app entries in `HKLM\Software\Stained Glass\Store`
(shipped as a `defaults/*.reg`, so it is importable per-prefix and
mirror-/policy-overridable exactly like the browser's `ListUrl`/`RawUrl` and
`Offers\NN`). Costs: the reg format is flat (one sub-key per app); rich install
recipes must fit into named values. Benefit: one proven, gated download/verify/
install path; the catalog is data, editable without a rebuild, and consistent
with everything else the shell keeps in the registry.

### C. Wrap the user's winget only

Shell out to winget for everything. Costs: winget is the user's own, optional
(we do not ship it — ADR 0004); with no winget there is no store. Rejected as
the sole path, but kept as an *acceleration*: when the user has winget, use it
(as the browser already does).

## Decision

**Option B**, reusing the browser engine, with winget as an opportunistic
accelerator (C) when the user has it.

### Where it lives

A new app, **`sg-store`**, in the sg-shell source tree at `src/store/`,
mirroring how `src/browser/` and `office/` sit in sg-shell (AGPL, no Wine code,
a PE program under `/usr/libexec/stained-glass/shell`, reached through `Z:`).
It is added to `debian/rules`' install list and to `make build`/`make test`. It
gets a Start-menu presence and an `sgstore.exe` App Path via
`defaults/85-sg-store.reg`.

`src/browser/fetch.c` and `src/browser/manifest.c` are compiled into `sg-store`
unchanged (the browser keeps using them too); `sg-store` adds `catalog.c` (read
the catalog, detect installed state and versions), `main.c` (the window and the
command line), and reuses `pkg_resolve`/`pkg_download`/`pkg_install`/
`winget_install` verbatim. This is the "reuse the proven approach" requirement
made literal: the SHA-256 enforcement and the silent-install runner are the same
lines the browser gate already mutation-tests.

### The catalog / manifest format

The catalog is a set of app entries under
`HKLM\Software\Stained Glass\Store\Apps\NN` (two-digit ordinals, as the browser's
`Offers\NN`). A mirror or Group Policy may replace the whole catalog by pointing
`HKLM\Software\Stained Glass\Store` `CatalogUrl` elsewhere in a later revision;
for now the catalog ships as data in `defaults/85-sg-store.reg`. Each entry:

| Value | Meaning |
|---|---|
| `Name` | display name ("Mozilla Firefox") |
| `Publisher` | maker ("Mozilla") |
| `Description` | one line, no marketing |
| `Category` | "Browsers", "Productivity", "Media", "Developer"… (groups the UI) |
| `Colour` | `dword` `0x00RRGGBB` for the letter badge — **no vendor logos** (as browser Offers) |
| `Tier` | `windows` (default/ideal), `ours` (our build), or `linux` (hidden last resort) |
| `Source` | how to install (below) |
| `DetectKey` / `DetectName` | how to tell it is installed, and read its version |

**`Source`** is `method:argument`, and the method decides the install path:

- **`winget:<PackageId>`** — resolve live through the winget community
  repository (`manifest.c`/`pkg_resolve`), download from the vendor,
  **enforce the manifest's SHA-256**, run the manifest's silent recipe (or the
  user's winget if present). This is the browser's exact path. Used for
  third-party Windows apps (the browsers, 7-Zip, VLC, VS Code…).
- **`pin:<Url>|<Sha256>|<Type>|<Silent>`** — a vendor download pinned in the
  catalog (as `office.ini` pins LibreOffice): download `Url`, enforce
  `Sha256`, run it silently by `Type` (`msi`/`nullsoft`/`inno`/`burn`/`exe`
  with `Silent` switches). Used when an app is not in winget-pkgs but has a
  stable published installer + hash.
- **`ours:setup:<AppPathExe>`** — invoke one of our own setup programs (e.g.
  `sg-office-setup64.exe /install`). This is how **SG Office** appears in the
  store: the entry runs the existing, already-gated Get-SG-Office flow, which
  itself downloads LibreOffice with its pinned SHA-256. The store adds no new
  download path for our own suites; it launches ours.
- **`ours:apt:<package>`** — one of our own packages on the apt repo /
  freesoft.page (e.g. a future SG-branded browser build). Installed through
  `sg-settingsctl`/an sg-session helper (apt), not by the store touching apt
  directly. (Wired when the first such package exists; see Consequences.)
- **`linux:apt:<package>`** — a native Debian desktop app (the **hidden
  tier**). Installed through the same sg-session apt helper.

**Update-check method** is implied by `Source`:

- `winget:` — `pkg_resolve` returns the newest published version; compare it to
  the installed version read from `DetectKey`/`DetectName`
  (`…\Uninstall\*` `DisplayVersion`, or `StartMenuInternet` for browsers). A
  newer available version offers **Update**, which re-runs the install path.
- `pin:` — the catalog carries the pinned version; installed version from
  `DetectKey`. A raised pinned version (a new sg-shell) offers Update.
- `ours:setup:` — delegate to the setup program's own `/status` (SG Office's
  `sg-office-setup64.exe /status` already reports whether the current payload
  is installed).
- `ours:apt:`/`linux:apt:` — apt's candidate vs installed version, via the
  helper.

### How the UI presents Windows-first and hides Linux

- The window lists entries as cards, grouped by `Category`, in catalog order.
- **Only `windows` and `ours` tiers are shown by default.** For any given app,
  the Windows/our build is the card the user sees; it is the default and only
  suggestion.
- The **`linux` tier is collapsed behind an "Advanced: Linux desktop apps"
  disclosure** at the bottom, closed by default, with a one-line caption that a
  Linux app is a last resort and the Windows version is preferred. Nothing in
  the default view links to it beyond that disclosure. (Mutation-tested: a build
  that shows the Linux tier by default fails the gate.)
- Each card shows **Install** (not installed), **Open** (installed, current),
  or **Update** (installed, older) — plus **Installed** state text, as the
  browser page already does.
- A **"Check for updates"** action refreshes every non-Linux entry's available
  version and marks the ones with updates; per-card **Update** installs it.

### What the store explicitly does NOT do

**OS updates stay where they are.** The store never runs `apt full-upgrade`,
never touches the staged/install-on-reboot OS-update mechanism, and never shows
OS updates as store items. A short line in the UI points OS updates to
Settings > Update & Security. The store's apt use is confined to *individual
application* packages through the sg-session helper, never the system upgrade.

### Elevation

Per-app installs need an administrator (all-users installs, MSI). `sg-store`
follows the browser/office precedent: `ShellExecuteEx` with `runas` (ADR 0012's
consent prompt) for the installer; the store process itself is unprivileged.

## Evidence

The pattern is already in production and gated:

- Browser: `sg-shell/src/browser/fetch.c` enforces the SHA-256 (`pkg_download`:
  a mismatch deletes the file and refuses to run it) and runs silent installers
  by type; `test/browser-check.sh` mutation-tests `-DSG_MUTANT_NOHASH` (no hash
  check) and `-DSG_MUTANT_NODEFAULT`, and `SG_BROWSER_ONLINE=1` installs the
  real Firefox.
- Office: `sg-shell/office/setup/setup.c` pins `Version`/`Url`/`Sha256`/
  `MsiProperties` in `office.ini`, verifies before install, and mutation-tests
  `-DSG_MUTANT_NOHASH`.

`sg-store` reuses `fetch.c`/`manifest.c` directly, so this evidence carries
over; the new gate (`test/store-check.sh`) drives the catalog against a
winget-pkgs-shaped mock source (reusing `test/sg-browser-fake.c`) plus a
stand-in installer, and mutation-tests: `-DSG_MUTANT_NOHASH` (installs an
unverified download), `-DSG_MUTANT_SHOWLINUX` (Linux tier shown by default) and
`-DSG_MUTANT_NOUPDATE` (a newer available version not detected).

## Consequences

- **Easy:** adding an app is a catalog reg entry — no code. The download/verify/
  install path is one shared, mutation-tested implementation. SG Office and the
  browsers appear in the store by pointing entries at flows that already exist.
- **Windows-first is structural**, not a UI habit: the Linux tier is a separate,
  collapsed disclosure and the gate fails if it leaks into the default view.
- **Hard / deferred:** the `ours:apt:` and `linux:apt:` install actions need an
  sg-session apt helper (a Windows program has no pipe to native apt, per the
  sg-netctl/sg-settingsctl bridge pattern). Phase 1 ships the catalog schema and
  the two apt tiers as *catalogued but install-deferred* (the card explains it
  installs through Settings) so the schema is complete and Windows/our-build
  installs work end-to-end; the apt bridge is a tracked follow-up.
- **Obliges us to revisit:** a `CatalogUrl` fetched catalog (so the store can
  grow without an sg-shell release) and Group-Policy locking of the catalog;
  both fit the existing `ListUrl`/policy precedent.
- **OS updates untouched:** no new debt against the update mechanism; the store
  stays out of it by construction.
