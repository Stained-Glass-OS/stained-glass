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
| B1 Theming | **Done (2026-09-24).** White flat title bars and light chrome, 30px captions, flat caption buttons (wine-sg 0013); the Light visual style's blue accents are now recoloured to the project purple (wine-sg 0031 -- SVGs recoloured, build.sh regenerates the theme BMPs). Verified in the image; the installed light.msstyles carries purple and no blue. |
| A1 PowerShell 7 | **Done.** 7.6.6 in `C:\Program Files\PowerShell\7`, on PATH, Start menu; `sg-apps-check` passes in the image. Open: fails with no console and redirected output (unattended use). |
| A2 Windows Python | **Done.** 3.14.7 with pip/venv, PEP 514, PATH, Start menu; gated in the image. |
| A3 winget | **WORKS, 2026-09-24 (wine-sg 10.0-11).** The real, user-supplied winget-cli searches both sources, shows manifests, installs MSI and NSIS packages, lists and uninstalls them. The acceptance gate `make test-winget` runs it end to end in a fresh prefix. Built in Wine: Windows.Web.Http (0028-0029), Uri (0030, 0033), MRT ResourceLoader + PRI reader (0032), appxpackaging.dll (0035), the AppX signature SIP (0037), the Compression API (0036), package name functions (0034), PackageCatalog (0043), PackageManager queries (0044), and the .msi verb fix (0045). Along the way two Authenticode trust holes were closed (0039, 0040), and administrator-added roots now persist (0042). Remaining: MSIX deployment (PackageManager.AddPackageAsync) and the bundle reader, for Store/MSIX packages. |
| E2 RDP out | **Done.** `sg-mstsc` (Remote Desktop Connection, mstsc command line and .rdp files, injection-hardened) starts `sdl-freerdp3`; gated in sg-shell, verified in the image. |
| A6 .NET Framework & HTML engine | **Done** (new item). Wine Mono 9.4.0 and Gecko 2.47.4 shipped unpacked and shared; the image compiles and runs a .NET Framework program. |
| F3 Staged updates | **Done.** PackageKit offline updates via `sg-update-prepare` (daily timer); `make update-test` proves download-now, install-on-reboot. The image now also carries Debian's apt sources, which it lacked. |
| F1/F2 Repository | **Live** at https://stained-glass-os.github.io/apt, signed, trusted by the image ([package-repository.md](package-repository.md)). Open: payloads as `.deb`s, rising versions per build. |
| C1 Principals / C2 Elevation | **Core implemented** (ADR 0012). Administrators = `sg-admins` (also sudo); the broker `sg-brokerd` starts a program as the SYSTEM account after consent; `sg-elevate` + wine-sg 0022 wire "Run as administrator"; standard users cannot self-elevate (0019). Gate `make elevate-test`. **Consent prompt landed 2026-09-24**: sg-compositor SECURE mode + `sg-consent.exe` driven by the broker (Yes/No for administrators, administrator credentials otherwise; gates `make test-secure`, `make test-consent`). Remaining: elevated-window input isolation (UIPI). |
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

  **Update 2026-09-24 (later):** install/list/uninstall of MSI and NSIS
  packages work (wine-sg 0043-0045), and **MSIX deployment** is in
  (0060-0063). PackageManager installs signed packages and bundles: the
  signature must be trusted, and the block map is checked. It registers them,
  gives them Start menu shortcuts, lists and removes them, and a packaged
  app gets its package identity. Open: dependency (framework) and resource
  packages, app execution aliases.
- **A4. Microsoft Edge (Wine-side).** ROADMAP **P4**. **Working, sandbox
  on (2026-09-24):** Edge, supplied by the user, installs silently from its
  MSI and shows, scripts and paints pages with its own sandbox. Its renderers
  run in an AppContainer at low integrity with restricted tokens (wine-sg
  0049-0055). Gate: wine-sg `make test-edge`.
- **A5. Proper Control Panel. First pass done, 2026-09-23.** `sg-control`
  (sg-shell) is a Control Panel window showing the machine's real state --
  edition, computer name, system type, the signed-in user and their session
  administrator status, Windows Update management, and the count of machine
  policies in force -- read from the live token, registry and system. `control`
  opens it (App Paths); the Start menu lists it. Gate: sg-shell `test/
  control-check.sh`. Open: navigable categories/applets, and settings the user
  can change (needs the elevation broker for machine settings).

- **B1. Proper theming (msstyles). Done, 2026-09-24.** A Windows-10-style
  visual style via `uxtheme` + the Light `.msstyles`, its blue accents recoloured
  to the project purple (wine-sg 0031: the theme's source SVGs recoloured, and
  build.sh regenerates the packed .bmp/.cur/.ico from them since a normal build
  ships pre-rendered images). Pairs with the taskbar (wine-sg 0012) and flat
  caption buttons (0013). Open: none for the accent recolour.

### C. Security & privilege model **[DAVID]**
- **C1. Principal model. Signed off by David 2026-09-24 as ADR 0012** (split token;
  administrators = `sg-admins`, elevation per program via the broker to the SYSTEM
  account; `sgsystem` has no sudo; root is reached by the human with `sudo`).
  Original proposal by David: regular users; administrators run
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
- **D1. Domain member.** ROADMAP **P2**. **Working (2026-09-24):**
  `sg-domain-join` (winbind, rid idmap, plain user names), domain sign-in at
  the login screen, a Kerberos ticket at sign-in that Windows programs use
  through Wine's SSPI (Kerberos and Negotiate: single sign-on), Domain Users
  as the Windows system's users and Domain Admins as its administrators.
  Gate: sg-image `make domain-test` (two VMs, the image's own DC role).
  **Also working (2026-09-24):** the home drive (homeDirectory/homeDrive),
  NETLOGON logon scripts, `NET USE` and WNetAddConnection2 (the Windows
  network provider), UNC paths, and a user's Group Policy (Preferences drive
  maps, GPO logon scripts, user Registry.pol). Every share is mounted with the
  user's own Kerberos ticket, so the file server decides what they may reach.
  Also the logon variables (USERDOMAIN, LOGONSERVER, HOMESHARE), and
  **machine Group Policy** from the domain (sg-gpo-machine/sg-gpupdate:
  the computer's GPOs' registry policy into HKLM, refreshed every 90
  minutes) -- and Group Policy **de-tattoos** on both machine (HKLM) and
  user (HKCU) sides, so a policy removed from a GPO stops applying at the
  next refresh/login. Open: machine startup scripts, the user's real domain
  SID inside Wine, and interoperation tested against a Windows DC and Windows
  clients.
- **D2. Host a domain / be a Domain Controller.** ROADMAP **P9**. **Working
  (2026-09-24)** as a role of the one image: `sg-dc-provision` makes a
  machine a Samba AD DC with internal DNS; every Samba service is off until a
  role asks. Gate: sg-image `make dc-test` (DNS SRV records, Kerberos, the
  directory, SMB, a reboot). Built inside the existing repos -- no new repo
  was created; whether the DC role deserves one stays **[DAVID]**.

### E. Remote access
- **E1. RDP in (server).** **Working (2026-09-24):** sign in over RDP and get
  a desktop, as with `mstsc` (ADR 0010 pattern B): a remote session of its own
  (headless sg-compositor at the client's size, its own lock screen),
  disconnect keeps it, the next login reconnects. `sg-rdpd.service`, off by
  default. Gates: sg-session `make test-rdp-stream` (lossless, pixel-exact) and
  sg-image `make rdp-test`. **E1b done (2026-09-24):** a login for a user
  signed in at the console takes that session over, as on Windows. The console
  goes dark and deaf; Ctrl+Alt+Del there, or disconnecting, gives it back
  locked. Open: a compressed codec, pattern A (console shadow).
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
- **F5. Live image + OS installer.** **Working (2026-09-24).** Every image is
  its own installation media: a "live" boot entry (root read-only under an
  overlay) whose login screen is Setup, a Windows-style wizard (`sg-setup.exe`)
  over a root service (`sg-installd`) and `sg-install` -- systemd-repart block
  copy, root grown to the disk, a machine identity of its own, the owner as
  administrator. Gate: sg-image `make install-test` (Setup driven through a
  VM's keyboard onto a blank disk, then the installed disk booted alone and
  signed in to). Open: install alongside another OS, and choosing partitions.

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
