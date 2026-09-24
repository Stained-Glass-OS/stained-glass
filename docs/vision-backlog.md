# Vision backlog — David's wants

Captured 2026-09-22 from David, verbatim intent preserved, then organised and
ordered. This is the running list of desired end-state capabilities beyond the
Phase 0 image. Items map onto `ROADMAP.md` phases where one already exists, and
add new ones where none did. **Order is a recommendation; David set none.**

Each item has: what it is, where it stands, what it depends on, and whether it
is a **[DAVID]** decision (security model, repo creation/hard-fork, hosting
spend) that must not be decided unilaterally.

---

## The wants, as stated

> PowerShell included Wine-side. Microsoft Edge running within the Wine side.
> Windows Python installed. Potentially winget installed. Proper theming so all
> the windows aren't ugly gray bars. RDP both in and out. Proper control panel.
> Able to apply policies. Potentially even able to host a domain being a domain
> controller. Elevation — windows, or something needs to be installed as
> administrator or opened as administrator. I'm thinking we'll have regular
> users, administrators that run as the system user, and potentially the kernel
> level would be the Linux root. Not sure if it's a good security model but
> potentially the system user has sudo access to get to root. Even if that
> literally means running a `sudo su` from an elevated shell. We also need an
> upgrade path, where updates download and then install on a reboot. Similar to
> how Windows normally does it and how PureOS does it. The live image would also
> need an install path for the OS. A partitioner etc. We will set up a
> repository for the .debs, defaulting to Debian and a mirror plus our soon-to-be
> repo. And the upgrade command can literally just use apt. Plus if we get
> winget going, upgrades from that direction too. I'm considering using GitHub
> Pages for the repository, but only if our packages fit within their site
> maximum. If not, getting a VPS to host the repository.

---

## Status (2026-09-22)

| Item | State |
|---|---|
| B1 Theming | **Done, first pass.** White flat title bars and light chrome (Default User colour/metric drop-ins from sg-shell), 30px captions, flat caption buttons (wine-sg 0013); controls use Wine's own Light visual style. Verified in the image. Open: recolour Light's blue accents to our purple (an LGPL derivative, so wine-sg). |
| A1 PowerShell 7 | **Done.** 7.6.6 in `C:\Program Files\PowerShell\7`, on PATH, Start menu; `sg-apps-check` passes in the image. Open: fails with no console and redirected output (unattended use). |
| A2 Windows Python | **Done.** 3.14.7 with pip/venv, PEP 514, PATH, Start menu; gated in the image. |
| A3 winget | **`winget search` WORKS (2026-09-24).** Real winget-cli queries the Microsoft Store and returns real results under wine-sg (`winget search python` -> Store packages with product IDs). Path built: `Windows.Web.Http` implemented from scratch in Wine (0028-0029, ~4500 lines: filter/client/method/request/content/response/headers/async + winhttp), `iertutil` IUriEscapeStatics (0030), real winsqlite3/ICU DLLs, wine-sg 0026-0027. Remaining: MRT/resources.pri so UI strings (column headers) are readable not keys; the community/MSIX source (packaged-COM + AppxPackaging); install (OOP COM server + Windows.Management.Deployment). Each is a large Windows subsystem. |
| E2 RDP out | **Done.** `sg-mstsc` (Remote Desktop Connection, mstsc command line and .rdp files, injection-hardened) starts `sdl-freerdp3`; gated in sg-shell, verified in the image. |
| A6 .NET Framework & HTML engine | **Done** (new item). Wine Mono 9.4.0 and Gecko 2.47.4 shipped unpacked and shared; the image compiles and runs a .NET Framework program. |
| F3 Staged updates | **Done.** PackageKit offline updates via `sg-update-prepare` (daily timer); `make update-test` proves download-now, install-on-reboot. The image now also carries Debian's apt sources, which it lacked. |
| F1/F2 Repository | **Live** at https://stained-glass-os.github.io/apt, signed, trusted by the image ([package-repository.md](package-repository.md)). Open: payloads as `.deb`s, rising versions per build. |
| C1 Principals / C2 Elevation | **Core implemented** (ADR 0012). Administrators = `sg-admins` (also sudo); the broker `sg-brokerd` starts a program as the SYSTEM account after consent; `sg-elevate` + wine-sg 0022 wire "Run as administrator"; standard users cannot self-elevate (0019). Gate `make elevate-test`. Remaining: the graphical consent prompt on the secure surface (reuses the lock surface) and elevated-window input isolation. |
| Security blocker (D14) | **Fixed.** ADR 0013 option D implemented (wine-sg 0014-0016): a user's programs open, create, delete, rename, reopen and chmod files with the user's own Unix rights. `sg-file-access-check` 4/4 in the image. Follow-ons: user SIDs have names (D12, wine-sg 0017); new users get their own profile and TEMP (D15, wine-sg 0018 + a login-time profile step). Open: device nodes; the shared server cannot signal another user's threads (D16). C1/C2 are unblocked. |

Found along the way: the session disabled .NET system-wide (fixed); wine-sg's
build did not apply patches added after first unpack (fixed); sg-session CI
tested against the wrong Wine (fixed, pending a green run).

## Themes and items

### A. Windows software parity (Wine-side apps & runtimes)
- **A1. PowerShell (Wine-side).** PowerShell 7 in Wine is the realistic target
  (5.1 is a stretch — noted in ROADMAP P2). Self-contained: install into the
  system prefix, gate that a script runs and returns an exit code. *Depends on:*
  nothing hard. Good early win.
- **A2. Windows Python.** Install the Windows CPython into the prefix; gate
  `python --version` and a script. *Depends on:* nothing hard.
- **A3. winget. `winget search` WORKS, 2026-09-24.** Real Microsoft
  winget-cli v1.29.380 (not a shim) starts under wine-sg: `winget --version`,
  `winget --help` and `winget source list` (real msstore/winget CDN URLs) work.
  Path found and cleared: three system DLLs Wine lacks (real `winsqlite3.dll`
  from the SQLite amalgamation; real `icuuc.dll`/`icuin.dll` from ICU 74.2 with
  unversioned symbols); `SHGetKnownFolderPath` must accept
  `KF_FLAG_NO_APPCONTAINER_REDIRECTION` (wine-sg 0026); and
  `Windows.ApplicationModel.Core.CoreApplication` + a real `IPropertySet` must
  exist (wine-sg 0027). **Remaining before it is user-functional is a large,
  discrete WinRT investment** and a [DAVID] call on whether to fund it:
  `winget search`/`install` need `Windows.Web.Http` (the REST client),
  MRT/`resources.pri` string loading (today all UI strings print as resource
  keys), and for install the out-of-process COM server
  (`WindowsPackageManagerServer.exe`) + `Windows.Management.Deployment`. Feeds
  F4 (upgrades from the Windows side). *Depends on:* that WinRT work.

  **Update 2026-09-24:** the Windows.Web.Http stack is implemented (wine-sg
  0028-0029) and `iertutil` gained IUriEscapeStatics (0030); with these
  `winget search` returns real Microsoft Store results over the Store REST API.
  The three remaining pieces (MRT strings, community/MSIX source, install) are
  each a large Windows subsystem; search via the msstore REST source is fully
  working today.
- **A4. Microsoft Edge (Wine-side).** ROADMAP **P4**. Chromium's sandbox needs
  the S2 security model (restricted tokens, job objects, integrity levels,
  AppContainer). Interim `--no-sandbox` for testing only, never shipped.
  *Depends on:* C (security model), S2.
- **A5. Proper Control Panel. First pass done, 2026-09-23.** `sg-control`
  (sg-shell) is a Control Panel window showing the machine's real state --
  edition, computer name, system type, the signed-in user and their session
  administrator status, Windows Update management, and the count of machine
  policies in force -- read from the live token, registry and system. `control`
  opens it (App Paths); the Start menu lists it. Gate: sg-shell `test/
  control-check.sh`. Open: navigable categories/applets, and settings the user
  can change (needs the elevation broker for machine settings).

- **B1. Proper theming (msstyles).** "So all the windows aren't ugly gray
  bars." A Windows-10-style visual style: `uxtheme` active + a `.msstyles`, so
  app title bars and controls stop being classic gray. Pairs with the taskbar
  work just shipped (wine-sg patch 0012). *Depends on:* nothing hard. **Highest
  visible value, unblocked — do first.**

### C. Security & privilege model **[DAVID]**
- **C1. Principal model.** Proposed by David: regular users; administrators run
  as the *system* user (`sgsystem` → SYSTEM SID); kernel level = Linux root;
  possibly the system user has `sudo` to root (even literally `sudo su` from an
  elevated shell). **This is a [DAVID] security decision** and must be written
  as an ADR and signed off before building on it. It underpins C2, A4, A5, and
  policy enforcement.
- **C2. Elevation ("Run as administrator" / UAC-like).** A consent/elevation
  path so something can be installed or opened as administrator. Maps to the SG
  admin SID / `sgsystem` and, at the OS edge, to `sudo`/polkit. *Depends on:*
  C1.
- **C3. Apply policies. First pass done, 2026-09-23.** Machine Group Policy is
  applied and enforced: `SHRestricted` reads HKLM first (wine-sg 0025, machine
  policy wins over the user), the HKLM policy branch is administrator-owned
  (0024), `sg-session` applies `/etc/stained-glass/policy.d/*.reg` at boot as
  SYSTEM, and `sg-start` honours NoClose/StartMenuLogOff. `sg-gpresult`
  (sg-shell) reports the machine and user policy in force, like `gpresult /r`,
  gated by planting known policies (2026-09-23). Gate: `make policy-test`. Open:
  an ADMX/`registry.pol` importer beyond the current `sg-polimport` (ROADMAP
  P3), and domain-delivered policy (needs D3/winbind). *Depends on:* C1 for
  who-may-write.

### D. Domain
- **D1. Domain member.** ROADMAP **P2**: winbind join, PAM login, Kerberos TGT
  into Wine SSPI, drive maps, login scripts. *Depends on:* a test domain
  (SGTEST.LAN).
- **D2. Host a domain / be a Domain Controller.** ROADMAP **P9**: Samba AD DC
  as an image *role* (one image, two roles: workstation, DC). Most ambitious;
  latest. **Creating a DC role/repo is [DAVID].**

### E. Remote access
- **E1. RDP in (server).** Partly built: `sg-rdp-authd` (pre-auth login) and the
  console-shadow design (ADR 0010) exist and are gated, but streaming needs
  `sg-compositor`. *Depends on:* sg-compositor milestones.
- **E2. RDP out (client).** An `mstsc`-like client. Cheapest path: ship an RDP
  client (FreeRDP, or Windows `mstsc` under Wine) and a launcher. *Depends on:*
  nothing hard.

### F. Lifecycle & distribution
- **F1. .deb repository.** Debian default + a mirror, plus our own repo. The
  `apt` line is the upgrade transport. *Depends on:* F2 (hosting).
- **F2. Repo hosting **[DAVID]**.** GitHub Pages *if* our packages fit under its
  limits (soft ~1 GB/repo, 100 GB/mo bandwidth, 100 MB/file); else a VPS.
  **Measured:** ~195 MB per full release — fits Pages' 1 GB; bandwidth is the
  limit (~1,000 machines). See [package-repository.md](package-repository.md),
  which also flags the real blocker: ADR 0006's open question on distributing
  `wine-sg` binaries. Spend/hosting is [DAVID].
- **F3. Staged upgrades (download now, install on reboot).** Windows-/PureOS-
  style: fetch updates, apply on reboot into a maintenance step. Likely
  `apt` + an offline/`system-update.target` flow (systemd's `system-update`
  mechanism) or an A/B scheme. *Depends on:* F1.
- **F4. winget-driven upgrades.** If A3 lands, updates from the Windows side too.
  *Depends on:* A3.
- **F5. Live image + OS installer.** The image becomes a live medium with an
  install-to-disk path: a partitioner and installer (e.g. Calamares, or a
  scripted installer). *Depends on:* the image; a repo (F1) for a networked
  install is nice-to-have.

---

## Recommended order

**Unblocked now (no [DAVID] gate) — do in this order:**
1. **B1 Theming** — visible, continues the shell work just shipped.
2. **A1 PowerShell** and **A2 Windows Python** — self-contained prefix installs,
   each with a gate. High utility, low risk.
3. **F1/F2 Repo + hosting decision** — measure .deb sizes, stand up the repo
   tooling (works the same whichever host); bring David the size numbers so the
   GitHub-Pages-vs-VPS call is informed.
4. **E2 RDP out** — ship a client + launcher; small.

**Needs a [DAVID] decision first, then build:**
5. **C1 Principal/security model** — write the ADR (regular / admin=system /
   root=Linux, and whether system→root via sudo). Get sign-off.
6. **C2 Elevation** and **C3 policies (P3 gpo-agent)** — build on the signed-off
   model. **A5 Control Panel** rides on B1 + C.
7. **F3 Staged upgrades** — once the repo exists.
8. **A3 winget** — spike feasibility; then **F4**.

**Larger / later (existing roadmap phases, sequence as there):**
9. **F5 Live installer** — a milestone of its own; can proceed in parallel once
   the image is stable.
10. **D1 Domain member (P2)** → **E1 RDP-in streaming** (needs sg-compositor) →
    **A4 Edge (P4)** → **D2 DC role (P9)**.

## Decisions parked for David
- **F2:** GitHub Pages vs VPS for the repo (after size measurement).
- **C1:** the security/principal model (ADR + sign-off) before C2/C3/A4 build on it.
- **D2:** creating a Domain-Controller role/repo (repo creation & possible
  hard-fork territory).
