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

**Largely delivered, 2026-09-23 (owner reduced to SYSTEM).** One HKLM is shared,
admin-writable and enforced by security descriptors (wine-sg 0002; S2 clauses 2
and 3); each user has an isolated HKCU hive loaded on demand (clause 4). The
prefix is still owned by one Unix user -- but that user is now the SYSTEM
account, the machine's administrator, which is the intended arrangement, not the
single-user shortcut this item named. What remains is per-user profile
*directories* (tracked as D15) rather than prefix ownership.

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

**Retired, 2026-09-23.** explorer reads `HKLM\Software\Wine\Drivers\Graphics`
(wine-sg 0023), which `sg-prefix-init` writes as the SYSTEM account; a user's
HKCU may still override it. The session no longer writes the machine setting.

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

**Retired, 2026-09-23.** `sg-wineserver.service` runs a machine-level wineserver
at boot as the SYSTEM account (wine-sg 0004/0005), before greetd; sessions
attach to it. The S2 gate's clause 1 (two users, one system prefix) passes.

### D6. No SCM, so no services

Nothing starts Windows services at boot, because there is no boot-time Wine to
start them in. The S2 gate explicitly requires "a service started at boot as
SYSTEM is visible to both users via the SCM"; today there is no SYSTEM and no
SCM.

**Retired, 2026-09-23.** `sg-services-start` runs `services.exe` under the
machine wineserver at boot as SYSTEM; the S2 gate's clause 5 (a boot service
visible to both users via the SCM -- PlugPlay) passes.

*Incurred in:* the absence of any such code.

### D7. `explorer` is the session: when the shell dies, everything dies

`sg-session-start` exec's `cage`, whose single client is `explorer`. When
explorer exits, cage exits, and the session ends — taking the wineserver with
it. There is no shell-restart path.

*Incurred in:* `sg-session/bin/sg-session-start`, `sg-session/lib/sg-run-explorer`

*Why it matters:* on Windows the shell is a per-user process that can be killed
and restarted without ending the session. Ours cannot.

**Retired, 2026-09-23.** `sg-run-explorer` supervises the shell
(`sg_supervise_shell`): a clean exit ends the session (sign-out via
`wineboot --end-session`), an abnormal exit restarts it, and a crash loop gives
up -- Windows' AutoRestartShell. Unit-tested in `make lint`.

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

**Retired, 2026-09-23.** `sg_session_env` publishes the live session under
`/run/user/<uid>` (the user's own 0700 runtime dir), or a per-uid file where
there is none, so concurrent sessions do not collide.

### D10. The gate matches processes machine-wide

`sg-session-check` uses `pgrep -f` with no user filter, so it would match
another user's `wineserver` or `explorer.exe` and report a healthy session that
is not the one it was asked about.

*Incurred in:* `sg-session/bin/sg-session-check`

*Why it matters:* a test that can pass for the wrong reason is worse than no
test. This is cheap to fix (`pgrep -u`) and should be fixed as soon as a second
user exists.

**Retired, 2026-09-23.** `sg-session-check` matches this user's explorer and
notepad and the machine account's wineserver (`pgrep -u`), never another
user's.

---

## Filesystem

### D11. Shared state directories owned by one user

`/var/lib/stained-glass` and `/var/log/stained-glass` are `chown`ed to `sguser`.

*Incurred in:* `sg-session/debian/sg-session.postinst`, `sg-session/bin/sg-prefix-init`

*What S2 must produce:* a split between machine state (shared, admin-writable)
and per-user state, with per-user logs that one user cannot read from another.

**Retired, 2026-09-23.** Per-user program output goes to private temp files or
the journal (kept per user), not the shared log directory, which drops
group-write. Machine logs stay in `/var/log/stained-glass`, SYSTEM-written.

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

**Status, 2026-09-23: local users named** (wine-sg 0017: the server maps
RID <-> passwd name; `LookupAccountSid`/`LookupAccountName` use it). Domain
users wait for winbind.

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

### D14. CRITICAL — every user's file access runs with SYSTEM's Unix rights

Found 2026-09-22. **Wine's server, not the client, opens files**
(`server/fd.c`, `open_fd` → `open()`), then hands the descriptor to the client.
With one machine-level wineserver shared by every user and running as the
SYSTEM account (wine-sg patches 0004/0005), the kernel only ever checks
SYSTEM's rights. Measured in the image, as the ordinary user `sguser`:

| Operation | Unix, as `sguser` | A Windows program, as `sguser` |
|---|---|---|
| create a file in `C:\windows\system32` | denied | **allowed** (file owned by `sgsystem`) |
| read a SYSTEM-only (0600) file | denied | **allowed** |
| write the user's own 0700 directory | allowed | **denied** |

The registry is protected -- wineserver enforces security descriptors there
(S2 clause 3) -- but files are not. **An ordinary user can plant a DLL where a
SYSTEM service will load it: a privilege escalation, and worse than Windows,
where a standard user cannot write System32.**

*Incurred in:* the machine-level wineserver (patches 0004/0005, `sg-wineserver`).

*Gate:* `sg-session/bin/sg-file-access-check` -- expected red, 3 of 3 failing;
kept out of CI like the S2 gate. *Decision:* [ADR 0013](decisions/0013-file-access-in-the-shared-wineserver.md).

**Status, 2026-09-23: fixed for files** (wine-sg 0014-0016: clients open,
create, delete, rename, reopen and chmod with their own rights). The gate, now
four clauses, passes 4/4 in the booted image. Still open: device nodes
(`server/device.c`) open as the server.

### D15. New users' profiles point into the SYSTEM account's profile

Found 2026-09-22. sg-prefix-init makes the Default User template by copying the
freshly initialised hive of the prefix owner (SYSTEM). Wine writes absolute
paths into it -- 32 of them name `C:\users\sgsystem` -- so every new user
inherits `TEMP`, `TMP`, the Shell Folders (Favorites, Cookies, Start Menu…)
and `USERPROFILE` pointing at SYSTEM's profile. Their own profile gets only
`AppData` and `Desktop`; no Documents, Downloads or Pictures.

*Incurred in:* `sg-session/bin/sg-prefix-init` (the userdef copy) with wine-sg
patch 0006 (seeding new hives from it).

*Why it is not simply fixed in the template:* Wine computes `USERPROFILE` from
the account *name* (`LookupAccountSid`), which fails for ordinary users (D12).
Rewriting the template to `%USERPROFILE%` without D12 leaves users with no
profile path at all. And creating a user's profile folders *as the user* needs
D14 fixed, or the folders are created with SYSTEM's rights.

*What it needs:* D12 (names), then a template with `%USERPROFILE%`-relative
User Shell Folders and no cached absolute Shell Folders, and a first-logon step
that creates the profile owned by the user -- Windows' profile service, in
effect.

**Status, 2026-09-23: addressed, pending the image gate.** The premise above
was half wrong: Wine expands `%USERPROFILE%` from the user's *login name*
(`GetUserNameW`), not from `LookupAccountSid`, so D12 was not a prerequisite.
What was needed: `sg-prefix-init` writes the template with
`%USERPROFILE%`-relative TEMP/TMP and without the Shell Folders cache or
Volatile Environment; wine-sg 0018 defines `USERPROFILE` before
`HKCU\Environment` (Windows' order, which Wine had reversed); and
`sg-profile-create`, run as root by `pam_exec` at session open, creates
`C:\users\<name>` owned by the user, 0700 -- the profile service. Found by
the apps gate once D14 was fixed: csc could no longer write the SYSTEM-owned
TEMP every user had inherited.

### D16. The shared server cannot signal another user's threads

Found 2026-09-23 running Wine's conformance tests as a second Unix user
against a shared server: the server delivers system APCs (asynchronous I/O
completion among them) by sending SIGUSR1 to the target thread, and the kernel
refuses (`tgkill` → EPERM) when the thread belongs to another Unix user. Two
ntdll:file I/O completion tests fail as a result (`iosb.Status` 0x101); the
same family explains kernel32:loader's `ReadProcessMemory` failures
(cross-process memory access by the server into another user's process).

*Incurred in:* the machine-level wineserver running as SYSTEM for every user
(wine-sg 0004/0005).

*Why it matters:* anything that needs the server to interrupt a thread --
async I/O completions, thread suspension, `NtGetContextThread` on another
thread, debugger attach -- degrades to "happens at the thread's next server
call", or fails.

*What it needs:* a delivery path that does not need the server's rights over
the thread -- e.g. a per-user helper that signals on the server's behalf, or
waking the thread through its own server connection. To be designed; ptrace
or CAP_KILL would undo patch 0005's point.

**Status, 2026-09-23: fixed** by wine-sg 0021 + sg-session's sg-procagent
(ADR 0014). The server delegates the thread signal (and cross-process memory
and affinity) to a per-user agent running as that user; no capability is
added. ntdll:file's async I/O completion failures go to 0.

### D17. CRITICAL — a standard user could obtain SYSTEM's token

Found 2026-09-23, while reading how Wine elevates `requireAdministrator`
programs for the elevation broker's design. The server mints tokens for anyone
who asks. Measured as a standard user in a shared prefix, with a probe
program: a program with a `requireAdministrator` manifest started with
SYSTEM's token (S-1-5-18); the linked token, `NtCreateToken` and
`ProcessWineGrantAdminToken` each handed out an administrator's token too.

*Incurred in:* upstream Wine (fine for one user who administers their own
prefix), made an escalation by the shared prefix (wine-sg 0001-0005).

**Status, 2026-09-23: fixed** by wine-sg 0019 -- standard users get elevation
type Default and no linked token; minting or assigning another user's token is
for SYSTEM's processes only. *Gate:* `sg-session/bin/sg-token-check` (all four
attempts denied as the ordinary user, with and without the manifest; granted
as SYSTEM, which proves the probe can tell).

*Consequence:* `requireAdministrator` programs now run unelevated -- the
elevation broker (ADR 0012) is what gives them a legitimate path.

### D18. A standard user cannot open their own processes

Found 2026-09-23 (ntdll:info as a second Unix user: `DebugActiveProcess` on
the user's own child fails with ERROR_ACCESS_DENIED). A process object's
default security descriptor grants access to Administrators only -- upstream
never needed more, since everyone there is an administrator. On Windows the
process's owner (its token's user) has full access. So task managers, debuggers
and any program that opens its own children by id fail for standard users.

*Incurred in:* upstream's `process_get_sd`, exposed by wine-sg 0002's
non-administrator tokens.

*What it needs:* a per-process descriptor from the creating token -- the user
and SYSTEM full access, as Windows' default -- in wine-sg.

**Status, 2026-09-23: fixed** by wine-sg 0020 -- each process and thread in a
shared prefix gets a descriptor naming the owning token's user, Local System
and Administrators with full access. A standard user can now open, suspend,
read the context of and set the affinity of their own processes; a
SYSTEM-owned process stays denied. *Still open:* attaching a debugger to your
own process (`DebugActiveProcess`) fails for a non-server user -- a debug-object
gate, tracked as D19.

### D19. DebugActiveProcess fails in a shared prefix, for everyone

Found 2026-09-23. `DebugActiveProcess` on one's own child fails with
ERROR_ACCESS_DENIED in a system prefix -- and, narrowed with a probe, **for
the SYSTEM account too**, not only standard users. `OpenProcess` on the same
child with the full debug rights (`PROCESS_VM_READ | VM_WRITE |
SUSPEND_RESUME | QUERY_INFORMATION | CREATE_THREAD`) is granted, so this is
*not* the process-object permissions D18 fixed; the refusal is inside the
attach (`NtDebugActiveProcess` -> `debug_process` -> `debugger_attach`, or the
remote break-in thread). The same test passes in an ordinary (non-shared)
prefix, so it is specific to the shared-server / session-0 arrangement.

*Incurred in:* the shared machine-level wineserver (wine-sg 0004/0005), most
likely its session-0 / no-interactive-shell handling (patch 0007) crossing the
debugger's session assumptions.

*Why it matters:* JIT crash debuggers, IDEs and attach-to-process fail. Lower
priority than the privilege debts: it is a functional gap, not an escalation,
and most fleet tooling uses open/query/suspend (D18), not the debugger API.

*What it needs:* trace the exact refusal in `debug_process`/`debugger_attach`
under `sg_system_prefix`; it is not a DACL, since the process opens with full
debug rights.

**Status, 2026-09-23: root-caused and fixed** by wine-sg 0021 + sg-procagent
(ADR 0014). The refusal was `set_process_debug_flag` writing the debuggee PEB
via cross-uid ptrace (and, more broadly, `ReadProcessMemory` and thread
affinity). Delegated to the per-user agent, ntdll:info -- whose
`DebugActiveProcess`/`WaitForDebugEvent` and affinity tests are the ones that
failed -- goes to 0 failures.

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
