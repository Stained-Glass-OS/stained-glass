# Roadmap

Each phase ends in a scripted gate. A phase is not done because the work looks
done; it is done when the gate exits 0 headlessly, in CI.

Phases past P1 are sketches. Do not start them without David.

David's full wish-list (2026-09) is captured and ordered in
[`docs/vision-backlog.md`](docs/vision-backlog.md).

---

## Phase 0 — bring-up

**Target:** a Debian image that boots in QEMU straight into Wine's
`explorer /desktop` as the shell, from a system-level prefix.

- `stained-glass`: brief, README, roadmap, ADR template.
- `sg-image`: mkosi, Debian trixie + backports kernel/Mesa, `Format=disk`, UEFI.
  Packages: Wine, DXVK, VKD3D-Proton, greetd, cage, XWayland, Samba/winbind
  client bits (unused yet), openssh-server for test access.
- `sg-session`: greetd autologin → cage → `wine explorer /desktop=shell,<WxH>`.
  System prefix at `/var/lib/stained-glass/prefix`, initialized at first boot.
- ADRs: Wine build source (Debian vs WineHQ), WoW64 mode, X11 vs winewayland.
- `docs/multiuser-debt.md`: every single-user assumption, written down as it is made.

**Gate** — `make boot-test` in `sg-image`:

- Boots headless in QEMU under a timeout.
- Guest-side check: `explorer.exe` and `wineserver` alive, desktop window
  exists, `notepad` launches and appears in the window list.
- QMP `screendump` saved as a CI artifact.
- Exit code reflects pass/fail.

**Done when:** fresh clone → `make image && make boot-test` passes locally and
in CI, and the screenshot shows a taskbar with a running app.

---

## Phase 1 — the three spikes

These decide the project's fate. Run in order. Each has a kill criterion, and
the kill criterion is meant to be used.

### S1. `wdf-wine` — KMDF on Wine's ntoskrnl

Highest novelty, cleanest oracle. Port the `Wdf01000.sys` equivalent from
Microsoft's MIT WDF source so KMDF drivers load in `winedevice.exe`.

- **Gate 1:** Microsoft's KMDF **echo** sample driver loads; its user-mode test
  app passes identically on a Windows VM and on SG.
- **Gate 2:** a KMDF **USB** driver binds to a software-emulated device (Linux
  `raw-gadget` + `dummy_hcd`) through `wineusb.sys`; the test app round-trips data.
- **Kill if:** WDF's dependencies on undocumented kernel internals exceed what
  Wine's ntoskrnl can reasonably grow. Document exactly which ones.

### S2. Multi-user system Wine

The deepest architectural risk. One machine-level wineserver and hive; per-user
HKCU; SIDs mapped to Unix uids via winbind; NT security descriptors enforced at
least on the registry and on services.

- **Gate:** two Unix users on one boot. Both read the same `HKLM`. A non-admin
  cannot write `HKLM\Software\Policies`. Each has an isolated `HKCU`. A service
  started at boot as SYSTEM is visible to both via the SCM. Scripted, exit code.
- **Kill/rescope if:** this requires rewriting Wine's process model rather than
  patching it. The outcome decides "patch set" vs "permanent hard fork", and
  David needs that answer explicitly.

### S3. TWAIN/USB imaging under stock Wine

Validates the driver thesis on real hardware. Install the open-source TWAIN DSM
in the prefix, vendor driver and data source, udev rules for wineusb, and a
small CLI TWAIN acquire tool as the test app.

- The hardware gate is human-run (Ambir scanner). We prepare a one-command
  recipe and a checklist; David runs it and reports.
- Also determine how athenaOne Device Manager talks to the browser (believed: a
  local service plus a localhost channel). If so, the requirement is "Device
  Manager runs in Wine", not "Edge is special". **Verify, don't assume.**

---

## Later phases — sketch only

- **P2 Domain member.** winbind join, PAM login, Kerberos TGT flowing into Wine
  SSPI Negotiate, `net use`/drive maps → cifs + dosdevices, login scripts
  (`.bat`/`.cmd`, then PowerShell 7 in Wine; 5.1 is a stretch).
- **P3 `gpo-agent`.** `registry.pol` → system hive, security filtering, refresh
  interval, a `gpresult`-like report. Oracle: the same GPO applied to a Windows
  VM, resulting registry diffed.
- **P4 Edge in Wine.** Requires S2's security model for the Chromium sandbox
  (restricted tokens, job objects, integrity levels, AppContainer). Interim:
  `--no-sandbox` for testing only, never shipped.
- **P5 `prt-broker`.** Hybrid join (cert on the AD computer object → Entra
  Connect sync → DRS registration), PRT request and renewal per the documented
  protocol (ROADtools is the reference for protocol behavior), COM server for
  `IProofOfPossessionCookieInfoManager`. Dev tenant only. Known fragility:
  Microsoft could require TPM attestation.
- **P6 Manageability surface.** Remote SCM, remote registry, WMI/CIM, WinRM,
  machine-wide MSI. The long slog; prioritize by what RSAT/PDQ-style tools
  actually call, measured against the oracle.
- **P7 Shell decision (`sg-shell`).** A time-boxed bake-off. **A:** extend
  Wine's `explorer /desktop` (Start menu, tray, appbars, shell notifications).
  **B:** run ReactOS `explorer.exe` + `browseui` (plus its shell32 pieces as
  overrides) under Wine — it targets public Win32 and known undocumented shell
  ordinals and is tested on real Windows, so treat failures as ordinary Wine
  bugs. Pick by lowest-hanging fruit: log every failure for B with the missing
  API/ordinal, compare against the feature gap list for A, and ADR it. GPL
  (ReactOS) vs LGPL (Wine) is fine as separate binaries in separate packages.
- **P8 `sg-compositor`, `sg-greeter`.** Replace cage and autologin. Per-window
  Wayland surfaces; the taskbar gets layer-shell placement and a toplevel list.
  Credentials never pass through Wine.
- **P9 DC role.** Samba AD DC as an image role: same image, two roles
  (workstation, DC).

---

## The oracle harness (`sg-testlab`)

Starts during Phase 1, and is what lets the work grind unattended. Invest early.

- Drives a Windows VM and an SG VM with the same test binaries; normalizes and
  diffs the results (exit codes, registry exports, enumerated devices, stdout).
- Keeps a **winetest baseline** for the exact Wine build in the image. No
  `wine-sg` patch may regress it. Known-flaky tests are tracked explicitly
  rather than ignored.

---

## Human-provided inputs

Ask David; don't work around these.

- A Windows evaluation VM/ISO for the oracle.
- WDK-built sample driver binaries (echo, a USB sample). Needs a Windows build
  box once; commit the binaries, the exact source commit and the build steps to
  `wdf-wine/test/fixtures/`.
- Ambir scanner test runs (S3), and the athenaOne Device Manager facts from a
  real workstation.
- A developer Entra tenant for P5.
- All **[DAVID]** decisions: licenses for new-code repos, repo creation beyond
  Phase 0, anything that turns `wine-sg` into a hard fork.
