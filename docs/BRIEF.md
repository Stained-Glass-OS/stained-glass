# Stained Glass OS — Claude Code Brief

Org: https://github.com/Stained-Glass-OS (you can create repos there via the GitHub tool)
Owner: David Hamner. Ask him when a decision is marked **[DAVID]**.

## 1. Mission

An open-source, drop-in Windows replacement for managed fleets:

- Linux kernel + Debian base for hardware (PCIe, GPU, storage, NIC).
- Wine as a **system-wide Windows personality**, not a per-user prefix.
- Joins an AD domain, can host one (Samba AD DC), applies GPOs, runs login scripts and PowerShell.
- Windows Edge running in Wine with working SSO (Kerberos on-prem, Entra PRT hybrid).
- Real Windows user-mode-hostable drivers (USB, HID, print, TWAIN/WIA, serial, smartcard) via Wine's ntoskrnl + a ported WDF.
- Shell lives inside the Wine system (shared hive). Linux side supplies only compositor, greeter, lock screen.

The full vision is built from independently useful subprojects, each shipping as Debian packages that the Stained Glass image consumes.

### Non-goals
- Reimplementing the NT kernel (ReactOS's path).
- Windows PCIe/GPU/storage kernel drivers. Linux drivers cover that hardware.
- Running Microsoft's closed identity stack (CloudAP, WAM, AAD BrokerPlugin). We implement the documented interfaces instead.
- Proton. We use upstream Wine (or wine-staging) plus DXVK and VKD3D-Proton as separate components.

## 2. Hard rules

1. **Clean room.** Never use leaked Microsoft source. Never disassemble or decompile Microsoft binaries. Black-box behavioral testing against real Windows is fine and encouraged. Microsoft-published open source (e.g. `microsoft/Windows-Driver-Frameworks`, MIT) is fine, but keep it in its own repo, never inside the Wine tree, so Wine patches stay upstreamable.
2. **Test domains only.** Use a lab realm (`SGTEST.LAN`) and a developer Entra tenant. Never point anything at a production domain, tenant, or real credentials. Never commit secrets.
3. **Every piece has a scripted gate.** A subproject is not "working" until `make test` (or equivalent) exits 0 headlessly. No gate, no merge. Prefer differential tests against a Windows VM oracle.
4. **Don't fork until a patch forces it.** Start on packaged upstream Wine. Create `wine-sg` only when the first real patch exists. Shape every Wine patch for upstream submission (small, tested, one concern). Before submitting anything upstream, check Wine's current contribution policy regarding AI-assisted code and record it in an ADR.
5. **Create repos lazily.** Only when the subproject starts. Empty placeholder repos are noise.
6. **Packaging from day one.** Each repo carries `debian/` and builds a `.deb` in CI.
7. **Record decisions.** `stained-glass/docs/decisions/NNNN-title.md` (ADR: context, options, decision, evidence). When you evaluate alternatives, write down what broke and why.
8. **Small PRs, conventional commits, CI green.** GitHub Actions per repo.

## 3. Repo map (create on demand)

| Repo | Purpose | License |
|---|---|---|
| `stained-glass` | Meta: this brief, README, ROADMAP, ADRs, cross-repo issues | CC-BY-SA docs |
| `sg-image` | mkosi config → bootable immutable Debian image; QEMU boot gate | **[DAVID]** default LGPL-2.1+ |
| `sg-session` | Session glue: compositor launch, system prefix init, explorer start | same |
| `sg-testlab` | Oracle harness: run the same test binaries on Windows VM and SG, diff results; winetest baselines | same |
| `wine-sg` | Wine fork (multi-user wineserver, NT security model, fixes). Only when needed | LGPL-2.1+ (Wine's) |
| `wdf-wine` | Port of Microsoft WDF (KMDF/UMDF) onto Wine's ntoskrnl | MIT (upstream's) |
| `sg-pnp` | udev hotplug → INF match (setupapi) → auto-load into winedevice | LGPL-2.1+ |
| `gpo-agent` | Fetch GPOs from SYSVOL, apply `registry.pol` into system hive, scripts | LGPL-2.1+ |
| `prt-broker` | Entra device registration + PRT lifecycle; COM server implementing `IProofOfPossessionCookieInfoManager` for Edge/Chromium | **[DAVID]** |
| `sg-shell` | The desktop shell (see §6) | depends on origin |
| `sg-compositor` | wlroots compositor with taskbar/toplevel integration (replaces cage later) | **[DAVID]** |
| `sg-greeter` | greetd greeter + lock screen, PAM/winbind auth | **[DAVID]** |

Local workspace: one directory, each repo cloned as a subdirectory. Every repo gets its own short `CLAUDE.md` (build, test, gate commands, pointers back to this brief).

## 4. Phase 0 — bring-up (start here)

**Target:** a Debian image that boots in QEMU straight into Wine's `explorer /desktop` as the shell, from a system-level prefix.

Steps:
1. Create `stained-glass` (meta). Commit this brief as `docs/BRIEF.md`, plus README, ROADMAP (phases below), ADR template.
2. Create `sg-image`:
   - mkosi, Debian stable (trixie) + backports kernel/Mesa, `Format=disk`, UEFI bootable.
   - Packages: Wine, DXVK, VKD3D-Proton, greetd, cage, XWayland, Samba/winbind client bits (unused yet), openssh-server for test access.
   - Wine source: evaluate Debian's package vs WineHQ devel/staging builds. Evaluate Wine's new WoW64 mode to keep the image pure amd64 (no i386 multiarch). Record in an ADR.
3. Create `sg-session`:
   - greetd autologin (placeholder for `sg-greeter`) → cage → `wine explorer /desktop=shell,<WxH>`.
   - System prefix at a fixed path (e.g. `/var/lib/stained-glass/prefix`), initialized at image build or first boot. Single user for now; note every place that assumes single-user in `docs/multiuser-debt.md`. That list seeds the wineserver work.
   - Try both display paths: (a) cage + XWayland + winex11 virtual desktop, (b) winewayland. Pick whichever gives a working taskbar and window management today; ADR the result.
4. Gate (`make boot-test` in `sg-image`):
   - Boot headless in QEMU with a timeout.
   - Guest-side check over ssh/serial: `explorer.exe` and `wineserver` alive, desktop window exists, a test Win32 app (`notepad`) launches and appears in the window list.
   - QMP `screendump` saved as a CI artifact.
   - Exit code reflects pass/fail.
5. CI: GitHub Actions builds the image and runs the gate (KVM if available, TCG fallback with longer timeout).

**Done when:** fresh clone → `make image && make boot-test` passes locally and in CI, and the screenshot shows a taskbar with a running app.

Report back at the end of Phase 0: what worked, X11 vs Wayland finding, Wine build choice, the multi-user debt list.

## 5. Phase 1 — the three spikes (decide the project's fate)

Run in this order. Each has a kill criterion.

### S1. `wdf-wine`: KMDF on Wine's ntoskrnl (highest novelty, cleanest oracle)
- Port `Wdf01000.sys` equivalent from Microsoft's MIT WDF source so KMDF drivers load in `winedevice.exe`.
- Gate 1: Microsoft's KMDF **echo** sample driver loads; its user-mode test app passes identically on Windows VM and on SG.
- Gate 2: a KMDF **USB** driver binds to a software-emulated device (Linux `raw-gadget` + `dummy_hcd`) through `wineusb.sys`; test app round-trips data.
- Sample driver binaries need the WDK to build: see §8.
- **Kill if:** WDF's dependencies on undocumented kernel internals exceed what Wine's ntoskrnl can reasonably grow. Document exactly which ones.

### S2. Multi-user system Wine (deepest architectural risk)
- One machine-level wineserver/hive; per-user HKCU; SIDs mapped to Unix uids (winbind); NT security descriptors enforced at least on registry and services.
- Gate: two Unix users on one boot. Both read the same `HKLM`. Non-admin cannot write `HKLM\Software\Policies`. Each has an isolated `HKCU`. A service started at boot as SYSTEM is visible to both via SCM. Scripted, exit code.
- **Kill/rescope if:** this requires rewriting Wine's process model rather than patching it. Outcome decides "patch set" vs "permanent hard fork". David needs that answer explicitly.

### S3. TWAIN/USB imaging under stock Wine (validates the driver thesis on real hardware)
- Install the open-source TWAIN DSM in the prefix, vendor driver + data source, udev rules for wineusb, a small CLI TWAIN acquire tool as the test app.
- Hardware gate is human-run (Ambir scanner). You prepare a one-command recipe and a checklist; David runs it and reports.
- Also determine how athenaOne Device Manager talks to the browser (believed: local service + localhost channel). If so, the requirement is "Device Manager runs in Wine", not "Edge is special". **Verify, don't assume.**

## 6. Later phases (sketch only; don't start without David)

- **P2 Domain member:** winbind join, PAM login, Kerberos TGT flowing into Wine SSPI Negotiate, `net use`/drive maps → cifs + dosdevices, login scripts (`.bat`/`.cmd`, then PowerShell 7 in Wine; 5.1 is stretch).
- **P3 `gpo-agent`:** `registry.pol` → system hive, security filtering, refresh interval, `gpresult`-like report. Oracle: same GPO applied to a Windows VM, diff resulting registry.
- **P4 Edge in Wine:** requires S2's security model for the Chromium sandbox (restricted tokens, job objects, integrity levels, AppContainer). Interim: `--no-sandbox` for testing only, never shipped.
- **P5 `prt-broker`:** hybrid join (cert on AD computer object → Entra Connect sync → DRS registration), PRT request/renewal per the documented protocol (ROADtools is the reference for protocol behavior), COM server for `IProofOfPossessionCookieInfoManager`. Dev tenant only. Known fragility: Microsoft could require TPM attestation.
- **P6 Manageability surface:** remote SCM, remote registry, WMI/CIM, WinRM, machine-wide MSI. This is the long slog; prioritize by what RSAT/PDQ-style tools actually call (measure against the oracle).
- **P7 Shell decision (`sg-shell`):** time-boxed bake-off.
  - A: extend Wine's `explorer /desktop` (Start menu, tray, appbars, shell notifications).
  - B: run ReactOS `explorer.exe` + `browseui` (+ its shell32 pieces as overrides) under Wine. It targets public Win32 + known undocumented shell ordinals and is tested on real Windows, so treat failures as ordinary Wine bugs.
  - Pick by lowest-hanging fruit: log every failure for B with the missing API/ordinal; compare against the feature gap list for A. ADR it. GPL (ReactOS) vs LGPL (Wine) is fine as separate binaries; keep them in separate packages.
- **P8 `sg-compositor`, `sg-greeter`:** replace cage/autologin. Per-window Wayland surfaces, taskbar gets layer-shell placement and a toplevel list. ~~Credentials never pass through Wine.~~ **Superseded by [ADR 0008](decisions/0008-wine-side-login-and-lock.md):** the login and lock screens run inside Wine, because RMM and RDP tools cannot see a Linux greeter and a fleet OS that cannot be remotely supported is not viable. PAM remains the only authority. Restoring the original rule is the goal for `sg-compositor`.
- **P9 DC role:** Samba AD DC as an image role; same image, two roles (workstation, DC).

## 7. Oracle harness (`sg-testlab`, start during Phase 1)

- Drives a Windows VM and an SG VM with the same test binaries; normalizes and diffs results (exit codes, registry exports, enumerated devices, stdout).
- Keeps a **winetest baseline** for the exact Wine build in the image. Any `wine-sg` patch must not regress it. Track known-flaky tests explicitly rather than ignoring failures.
- This harness is what lets work grind unattended. Invest in it early.

## 8. Human-provided inputs (ask David; don't work around)

- Windows evaluation VM/ISO for the oracle.
- WDK-built sample driver binaries (echo, a USB sample). Needs a Windows build box once; commit binaries + exact source commit + build steps to `wdf-wine/test/fixtures/`.
- Ambir scanner test runs (S3) and the athenaOne Device Manager facts from a real workstation.
- Developer Entra tenant for P5.
- All **[DAVID]** decisions: licenses for new-code repos, repo creation beyond Phase 0, anything that turns `wine-sg` into a hard fork.

## 9. First session checklist

1. Read this brief fully. Create `stained-glass`, commit brief/README/ROADMAP/ADR template.
2. Create `sg-image` and `sg-session`; get to a passing `make boot-test`.
3. Write ADRs: Wine build source, WoW64 mode, X11 vs winewayland.
4. Write `docs/multiuser-debt.md`.
5. Open issues in `stained-glass` for S1, S2, S3 with their gates copied verbatim from §5.
6. Stop and report. Do not start Phase 1 repos until David confirms.
