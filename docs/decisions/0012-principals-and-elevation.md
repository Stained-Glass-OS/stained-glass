# 0012. Principals and elevation: who is an administrator, and how anything gets to root

- **Status:** accepted, 2026-09-22; core implemented 2026-09-23; **signed off by David as the C1 principal model, 2026-09-24**
- **Date:** 2026-09-22
- **Deciders:** David; analysis and recommendation by Claude

## Context

David's proposal (vision backlog item C1), in his words:

> We'll have regular users, administrators that run as the system user, and
> potentially the kernel level would be the Linux root. Not sure if it's a good
> security model but potentially the system user has sudo access to get to
> root. Even if that literally means running a `sudo su` from an elevated shell.

He flagged his own doubt, and the stakes are the brief's: security equivalent
to *or better than* Windows, on machines that remote-support tools and domain
administrators will manage. Elevation ("Run as administrator", installers that
demand it), Group Policy enforcement, the Control Panel and Edge's sandbox all
build on whatever is decided here, so it has to be settled before them.

### What the system does today

These are established by the code, not proposed:

- **A SID per Unix user** (wine-sg patch 0002). Ordinary users get a token
  *without* the Administrators group, without administrative privileges and at
  medium integrity. They cannot write `HKLM\Software\Policies` (S2 gate, clause
  3).
- **The only administrator is SYSTEM, and SYSTEM is the prefix owner**
  (patches 0004, 0005): the unprivileged account `sgsystem`, which owns the
  system prefix, runs the machine-level wineserver, and hosts every Windows
  service — including, eventually, third-party ones such as RMM agents.
- **No human has an administrative identity.** There is no "Run as
  administrator", no consent prompt, and no route from a user's session to
  anything privileged.
- **But file access is not separated at all.** The shared wineserver opens
  files with SYSTEM's Unix rights for every user, so an ordinary user's program
  can already write System32 and read SYSTEM-only files (debt D14,
  [ADR 0013](0013-file-access-in-the-shared-wineserver.md)). Nothing below
  means anything until that is fixed: elevating to an identity the user can
  already act as protects nothing.

So "administrators run as the system user" is already how the code decides
administrative rights. What is open is *how a human gets there*, and whether
that path continues to root.

### The fact that decides the architecture

**Wine is not a security boundary between processes of the same Unix user.**
Every Windows program a user runs is a Unix process with that user's uid. With
`kernel.yama.ptrace_scope` at 0 (see Evidence for what the image does), any of
them can attach to any other — read its memory, inject code into it — whatever
tokens and integrity labels wineserver has assigned. At 1, ptrace is limited to
descendants, but a same-uid program can still tamper with another's files, its
environment and the programs it starts. Either way, same uid means no boundary
the kernel will defend.

Windows' UAC keeps an unelevated program from driving an elevated one with
integrity levels and UIPI, enforced by the Windows kernel. Wine's integrity
labels are enforced only by wineserver, on wineserver objects; they do not stop
ptrace. **An "elevated" process under the user's own uid is not elevated in any
sense that holds.** Real elevation must run the elevated program as a
*different Unix account*, started by something privileged after consent, so the
kernel separates the two.

## Options

### A. Administrators' whole sessions run as the system user

An administrator logs in and their desktop runs as `sgsystem`.

- Simple, and matches the proposal most literally.
- **It is Windows XP's model, which UAC was built to end.** Every program an
  administrator runs — browser, email, an attachment — runs with machine-wide
  authority. One malicious document compromises the machine.
- Every administrator is the same identity, so nothing records which human did
  what.
- Shares an account with the Windows services, so a compromised service can
  tamper with an administrator's desktop and the other way round.

### B. Split token: sessions unprivileged, elevation per program (recommended)

Everyone's session — administrators included — runs as their own unprivileged
Unix user. "Run as administrator" (and an installer's manifest demanding
elevation) asks a small privileged **elevation broker**, which:

1. shows a consent prompt on the secure surface the lock screen already uses
   (ADR 0009) — out of reach of the user session's programs;
2. checks the requester is an administrator, and for consent requires their
   own password through PAM (Windows' "credential prompt" behaviour; a
   consent-only prompt can come later for fleets that want it);
3. starts *that one program* as the administrative identity (`sgsystem` at
   first — see below), outside the user's uid;
4. records who asked, for what, and the outcome in the journal.

This is UAC's shape. The kernel then separates the elevated program's
*process* from the session's. Its *display* is a second channel, and is
covered under Consequences: X11 lets any client inject input into, or read, any
other window on the same display, so an elevated program shown on the session's
own X server could still be driven by the programs it is meant to be protected
from.

**Which identity elevated programs run as.** At first, `sgsystem` — it is the
only administrative identity wine-sg recognises, and it is what installers need
(HKLM, Program Files, services). Later, per-administrator elevated accounts
(`alice` → `alice-admin`, with her SID plus Administrators) would make
attribution exact and stop elevated programs sharing an account with services.
That needs wine-sg to map an account to a user SID plus a group, which is the
same work as domain group mapping (P2), so it waits for that.

### C. The system user gets sudo to root

Separately from A or B: `sgsystem` may `sudo` to root.

- It *is* Windows-equivalent: SYSTEM on Windows can load kernel drivers, so
  SYSTEM ≈ kernel already.
- **It is not "better than Windows", and here it is worse.** `sgsystem` runs
  every Windows service, including third-party network-facing ones. Standing
  sudo turns any compromised service, and any elevated program, into Linux
  root with no further step. Today a compromised service is confined to one
  unprivileged account; with sudo, root is one command away and leaves no human
  in the loop.

### D. Root through a human, not through the service account (recommended)

- `sgsystem` has **no** sudo.
- Privileged *operations* the Windows side legitimately needs — installing
  updates, rebooting, adding a udev rule for a new device — become narrow
  root-owned helpers or polkit actions, each authorised on its own terms (the
  same pattern as `sg-lockd`'s root monitor).
- A **root shell** — "`sudo su` from an elevated shell" — is for administrators
  as themselves: `sudo` (or `run0`) asks for *their* password through PAM and
  logs it. That keeps David's workflow (an administrator can get to root from
  the desktop) while tying root to a human credential rather than to whatever
  happens to run as the service account.

## Decision

**B + D, decided by David on 2026-09-22.**

- Sessions run unprivileged, administrators included; elevation is per
  program, through a broker that prompts on the secure surface and starts the
  program as a different Unix account (`sgsystem` for now).
- `sgsystem` gets no sudo.
- Root is reached from a user's own account: `sudo su` as the administrator,
  with their own password.

Prompts, as on Windows (David, 2026-09-22):

- **An administrator** who elevates gets a **Yes/No consent** prompt.
- **A standard user** who needs elevation gets a **credential prompt**: an
  administrator's user name and password.

**Administrators are the members of a local group, `sg-admins`**, which is also
the group allowed to use `sudo`: one membership grants both. Domain groups map
onto it later (P2).

Nothing here is safe to build until ADR 0013 is decided and implemented.

## Evidence

Measured in the booted image (sg-image, 2026-09-22; kernel
`6.12.107+deb13-amd64`), over ssh:

- `kernel.yama.ptrace_scope` = **0**, in a fresh image with no local sysctl:
  same-uid processes may ptrace each other.
- `sudo` is **not installed**; `sgsystem` has no route to root today.
- What Windows programs see, from PowerShell 7 (`WindowsIdentity.GetCurrent()`
  and `IsInRole(Administrator)`), run as each account:

  | Unix account | Windows identity | Administrator |
  |---|---|---|
  | `sguser` (uid 102) | `S-1-5-21-0-0-0-1102`, name empty | False |
  | `sgsystem` (uid 101) | `NT AUTHORITY\SYSTEM`, `S-1-5-18` | True |

- S2 gate clause 3 (`sg-multiuser-check`): a non-admin cannot write
  `HKLM\Software\Policies`.

Also found: an ordinary user's identity has **no account name**
(`WindowsIdentity.Name` is empty — the SID has no name mapping), so programs
that show or log the signed-in user get nothing. Unrelated to elevation, but it
is the same identity layer; tracked in the multi-user debt list.

## Implementation (2026-09-23)

The security-blocker family (ADR 0013, debt D14/D16/D17/D18/D19) is fixed, so
this is unblocked, and the core landed:

- **`sg-admins`** is the administrators group and the sudo group (sg-session
  postinst + a sudoers drop-in). Root is reached as the human: `sudo su`.
- **`sg-brokerd`** (sg-session) is the broker -- a root PAM monitor, the main
  process dropped to the SYSTEM account. It checks whether the requester is an
  administrator, takes consent, and launches the program as the SYSTEM
  account, logging who authorised it. `sg-elevate` is the user's client;
  wine-sg 0022 routes ShellExecute `runas` ("Run as administrator") to it.
- **Standard users cannot self-elevate** (wine-sg 0019): the manifest/linked-
  token/NtCreateToken paths are closed, so the broker is the only way up.
- **Gate:** `sg-elevate-check` (image `make elevate-test`), mutant-proven -- an
  administrator's program runs as the SYSTEM account with consent, is refused
  without it.

**The consent prompt (landed 2026-09-24).** The first plan was to reuse the
lock surface as is. That did not work: while locked, `sg-lockd` puts a lock
screen up, and a lock screen over a consent prompt is wrong. sg-compositor
gained a **SECURE** mode instead. It isolates the session exactly as LOCK does,
showing and sending input to privileged clients only, but it tells watchers
`secure` rather than `locked`. RELEASE ends it and never undoes a real lock. A
LOCK during a prompt promotes it to a lock, and no prompt may start over a
locked machine. The broker finds the requester's own compositor (checked by
SO_PEERCRED), engages SECURE and runs `sg-consent.exe` on a private X server on
the privileged socket. Anything that goes wrong denies. Evidence:
sg-compositor `make test-secure` covers the keylogger, focus-steal and
lock-interplay cases, and fails against a SECURE that does not isolate.
sg-session `make test-consent` runs the broker and prompt end to end with PAM
under pam_wrapper. It fails against a broker that skips the administrator
check, and against one that skips SECURE.

**Also still open** (as ADR 0012 already noted): elevated programs share the
session's display, so input isolation for the elevated window (Windows' UIPI)
is not yet complete; and per-administrator elevated accounts wait for SID/group
mapping (P2).

## Consequences

- **B needs a broker and a secure prompt.** The broker is a small root helper
  in the style of `sg-lockd`'s monitor; the prompt reuses the lock screen's
  separate display and input isolation (ADR 0009), so programs in the session
  cannot read or click it.
- **Elevated programs need their own display, not just their own account.**
  Separate Unix accounts stop ptrace and memory access, but an elevated window
  on the session's X server can still receive synthetic input (XTEST) from the
  session's programs, which can also capture its contents — the gap UIPI closes
  on Windows. sg-compositor already runs the lock screen on its own X server
  behind a privileged socket; elevated programs need the same, one X server per
  elevated program, composited into the desktop. Without it, B's separation
  holds for processes and fails for input, and it should not be called
  complete.
- **wine-sg must let Windows ask for elevation.** `ShellExecute` with the
  `runas` verb and manifests with `requireAdministrator` need to reach the
  broker instead of failing or silently running unelevated.
- **Z: and `\\?\unix\` are a separate hardening item.** Windows programs can
  read the Linux filesystem through Z: and run Linux programs through
  `\\?\unix\`, with the user's Unix rights. That grants nothing the user lacks
  in Linux, so it is not an escalation, but it goes further than a Windows
  machine exposes, and it matters once elevated programs exist. Several
  components use both today (sg-mstsc's App Paths entry, patch 0010). Track as
  debt, and decide when the broker is designed.
- **Per-administrator elevated identities** wait for SID/group mapping (P2).

## Amendment (2026-09-24): SYSTEM may ask for a fixed list of root operations

**Decided by David: approved.**

The Control Panel (sg-shell's sg-control) changes machine settings the way
Windows' does: create and remove accounts, change an account's type or
password, rename the computer, join a domain, set the time zone and time
sync, check for updates. Those are root operations on Linux. They go through
**sg-admind** (sg-shell `admin/`), a root service started by a systemd
`.path` unit, which serves requests dropped in a spool only the SYSTEM
account (`sgsystem`) can write.

This changes "SYSTEM is unprivileged on Unix": SYSTEM may now *request*, not
perform, a **fixed, validated list** of root operations. That matches
Windows, where LocalSystem outranks an administrator, and it keeps the
principles of this ADR:

- A program reaches SYSTEM only through the elevation broker, after the
  consent prompt on the secure surface (administrators) or an
  administrator's credentials (everyone else).
- sg-admind trusts nothing but the request's owner (SYSTEM) and the request's
  content; every operation validates its arguments (account names, reserved
  accounts, the last administrator, zones that exist in zoneinfo) and refuses
  symlinks and requests not owned by SYSTEM. There is no generic "run this as
  root".
- Passwords travel in the request body, never on a command line or in logs.

Gate: sg-shell `test/admind-check.sh` (every operation and every refusal;
dropping the owner check or logging passwords turns it red).
