# Multi-user debt

Phase 0 builds a single-user machine. That is a deliberate shortcut, and this
file is the bill.

Every entry is a place where the Phase 0 code assumes there is exactly one
human, one session, or one security principal on the machine. The point is not
that these are bugs — they are correct for Phase 0 — but that **S2 (multi-user
system Wine) has to answer every one of them**, and discovering them one at a
time during S2 would be much worse than having the list up front.

Each item is tagged `D<n>`. The tags appear as `MULTIUSER-DEBT: D<n>` comments
at the exact places in the code that incur them, so the list and the code stay
in sync.

**Status of the list:** written during Phase 0 as the debt was incurred.
It is not yet complete — S2 will find more.

---

## The prefix and the registry

### D1. One system prefix, owned outright by one Unix user

`sg-session` initializes a single prefix at `/var/lib/stained-glass/prefix` and
`chown -R`s it to `sguser`. Everything in it — `system.reg` (HKLM),
`user.reg` (HKCU), `userdef.reg`, and all of `drive_c` — belongs to that one
user, read-write.

*Incurred in:* `sg-session/bin/sg-prefix-init`, `sg-session/debian/sg-session.postinst`

*Why it matters:* this is the single-user assumption, and everything else in
this file is downstream of it. The brief's target is one machine-level `HKLM`
shared by all users, with a per-user `HKCU` — which is not a file-ownership
question at all but a security-descriptor question.

*What S2 must produce:* `HKLM` readable by every user and writable only by
administrators; a distinct `HKCU` hive per user, loaded on login; and enforcement
by NT security descriptors rather than by Unix file modes.

### D2. No authentication: greetd autologs a hardcoded user in

`greetd` is configured with both `default_session` and `initial_session`
running as the literal user `sguser`, with no greeter and no credential check.

*Incurred in:* `sg-session/config/greetd-config.toml`,
`sg-image/mkosi.extra/etc/greetd/config.toml`

*Why it matters:* there is no notion of *who* is logged in, so there is nothing
for a SID to map to. It is a placeholder for `sg-greeter` (P8) and must never
reach a real fleet.

*What S2 must produce:* a real login, a Unix uid per user, and a SID per uid.

**Retired.** greetd now runs the Windows-style greeter as a dedicated `sggreet`
account and starts the session only after PAM accepts the credentials (ADR
0008); the autologin configuration is gone from both files above. The image
boot gate signs in by typing through QEMU's keyboard, so the real login path is
what is tested. The per-user SID half was already delivered by wine-sg patch
0002.

### D3. No SID-to-uid mapping

Wine assigns the prefix owner a default user SID. Nothing maps NT SIDs to Unix
uids in either direction, because with one user there is nothing to map.

*Incurred in:* the absence of any such code.

*What S2 must produce:* winbind-backed SID↔uid mapping, so that an NT security
descriptor naming a SID can be enforced against a Unix process.

### D4. Machine-wide settings are written to `HKCU`

`sg-run-explorer` pins Wine's graphics driver by writing
`HKCU\Software\Wine\Drivers\Graphics`. That is a machine-level fact about the
image being stored in a per-user location — correct only because the two are
the same thing today.

*Incurred in:* `sg-session/lib/sg-run-explorer`

*What S2 must produce:* this belongs in `HKLM`, writable by administrators only.

---

## Processes and sessions

### D5. One wineserver, owned by the login session

The wineserver is started implicitly by the session, as the session user, and
dies with it. There is no machine-level Wine instance that outlives a logout or
precedes a login.

*Incurred in:* `sg-session/bin/sg-session-start`, `sg-session/lib/sg-run-explorer`

*Why it matters:* this is the deepest item on the list and the one most likely
to decide "patch set vs. permanent hard fork". Windows services run as SYSTEM
before any user logs in and survive every logout. A wineserver whose lifetime is
a login session cannot express that.

*What S2 must produce:* a machine-level wineserver started at boot, independent
of any session, with per-user sessions attaching to it.

### D6. No SCM, so no services

Nothing starts Windows services at boot, because there is no boot-time Wine to
start them in. The S2 gate explicitly requires "a service started at boot as
SYSTEM is visible to both users via the SCM"; today there is no SYSTEM and no
SCM.

*Incurred in:* the absence of any such code.

### D7. `explorer` is the session: when the shell dies, everything dies

`sg-session-start` exec's `cage`, whose single client is `explorer`. When
explorer exits, cage exits, and the session ends — taking the wineserver with
it. There is no shell-restart path.

*Incurred in:* `sg-session/bin/sg-session-start`, `sg-session/lib/sg-run-explorer`

*Why it matters:* on Windows the shell is a per-user process that can be killed
and restarted without ending the session. Ours cannot.

### D8. Two explorers, and we tolerate it

`wineboot` autostarts a bare `explorer.exe /desktop` alongside the
`/desktop=shell,WxH` instance the session starts. Both are alive during a
normal session, which is visible in the gate's process list.

*Incurred in:* not suppressed anywhere.

*Why it matters:* harmless today because the gate matches on
`/desktop=shell`. Once the shell is a real thing with a taskbar and a tray,
two of them will not be harmless.

### D9. One session per machine, at a fixed path

`sg-run-explorer` publishes the live session's display at
`$SG_STATE/session.env`, a single fixed path. A second concurrent session would
overwrite the first's.

*Incurred in:* `sg-session/lib/sg-run-explorer`, read by `sg-session-check`

*What S2 must produce:* per-session state, keyed by user or by session id.

### D10. The gate matches processes machine-wide

`sg-session-check` uses `pgrep -f` with no user filter, so it would match
another user's `wineserver` or `explorer.exe` and report a healthy session that
is not the one it was asked about.

*Incurred in:* `sg-session/bin/sg-session-check`

*Why it matters:* a test that can pass for the wrong reason is worse than no
test. This is cheap to fix (`pgrep -u`) and should be fixed as soon as a second
user exists.

---

## Filesystem

### D11. Shared state directories owned by one user

`/var/lib/stained-glass` and `/var/log/stained-glass` are `chown`ed to `sguser`.

*Incurred in:* `sg-session/debian/sg-session.postinst`, `sg-session/bin/sg-prefix-init`

*What S2 must produce:* a split between machine state (shared, admin-writable)
and per-user state, with per-user logs that one user cannot read from another.

---

### D12. An ordinary user's Windows identity has no name

Found 2026-09-22 while gathering evidence for ADR 0012. Each Unix user gets its
own SID (wine-sg patch 0002), but nothing maps that SID back to an account
name: PowerShell's `[Security.Principal.WindowsIdentity]::GetCurrent().Name` is
empty for `sguser`, while SYSTEM resolves to `NT AUTHORITY\SYSTEM`.

*Incurred in:* wine-sg patch 0002 (SIDs without `LookupAccountSid` names).

*Why it matters:* programs that show, log or authorise by user name --
installers, audit logs, RMM agents -- see a blank user.

*What S2 must produce:* names for per-uid SIDs (`MACHINE\user` from the passwd
entry), and later winbind names for domain users.

### D13. Windows programs can reach the Linux side through Z: and `\\?\unix\`

Every Windows program can read the Linux filesystem through the Z: drive and
start Linux programs through `\\?\unix\` paths, with the user's Unix rights.
That grants nothing the user lacks in Linux, so it is not an escalation, but it
exposes far more than a Windows machine does, and it matters once elevated
programs exist (ADR 0012).

*Incurred in:* Wine's default prefix layout; relied on by wine-sg patch 0010
(sg-lockctl), sg-shell's `mstsc` App Paths entry and sg-mstsc, and
sg-install-apps' shortcut helper.

*What it needs:* a decision, with ADR 0012's broker, on removing Z: for users
and restricting `\\?\unix\` to named helpers -- and moving those users to
paths that survive it.

---

## How this list feeds S2

The S2 gate in the brief is:

> Two Unix users on one boot. Both read the same `HKLM`. Non-admin cannot write
> `HKLM\Software\Policies`. Each has an isolated `HKCU`. A service started at
> boot as SYSTEM is visible to both via SCM.

Mapped onto this list:

| S2 gate clause | Debt it retires |
|---|---|
| two users on one boot | D1, D2, D3, D9, D10, D11 |
| both read the same `HKLM` | D1, D4 |
| non-admin cannot write `HKLM\Software\Policies` | D1, D3, D4 |
| isolated `HKCU` per user | D1, D9 |
| SYSTEM service visible via SCM | D5, D6, D7 |

**D5 is the one to answer first.** Whether a machine-level wineserver can be
reached by patching Wine's process model, rather than rewriting it, is what
decides "patch set" vs. "permanent hard fork" — and David needs that answer
explicitly.
