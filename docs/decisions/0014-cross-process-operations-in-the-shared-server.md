# 0014. Cross-process operations in the shared wineserver

- **Status:** accepted, 2026-09-23
- **Date:** 2026-09-23
- **Deciders:** David ("must be compatible with existing Windows software … the
  signal processing must be identical"); analysis by Claude

## Context

Multi-user debt **D16** and **D19**. Some Windows operations require the
kernel object server to reach *into another process*: `ReadProcessMemory` /
`WriteProcessMemory` across processes, `DebugActiveProcess` (which writes the
debuggee's PEB and reads its modules), hardware-breakpoint debug registers
(`Get/SetThreadContext`), and asynchronous procedure calls delivered to a
thread that is not currently waiting in the server (an alertable wait
interrupted, some overlapped-I/O completions).

Wine performs these in the server, with `ptrace` and `tgkill` on the target
(`server/ptrace.c`: `read_process_memory`, `write_process_memory`,
`get_thread_context`, `send_thread_signal`). Upstream this is fine — the server
is the same Unix user as its clients. Stained Glass runs **one machine-level
wineserver as `sgsystem`** (patches 0004/0005), so for an *ordinary user's*
process these are a cross-uid `ptrace`/`tgkill`, which the kernel refuses
(`EPERM`) for an unprivileged process. Measured 2026-09-23: `DebugActiveProcess`
on one's own child, and cross-process `ReadProcessMemory`, fail with
`ERROR_ACCESS_DENIED` for ordinary users; same-uid operations succeed (proved
with a standalone `PTRACE_ATTACH` and with `Get/SetThreadContext` working
inside a session).

David's constraint: the behaviour a Windows program sees must be **identical to
Windows**. So "leave it as debt" is not acceptable, and whatever we do must
reproduce Windows' rules exactly:

- A process may read/write/debug another process **of the same user** (with the
  right handle access). — must work.
- Debugging a process of **another user** needs `SeDebugPrivilege`, held only by
  administrators. On Stained Glass an administrator acts through elevation
  (ADR 0012), which runs the elevated program as `sgsystem` — the **same uid as
  the server** — so the server does it directly. — already works.

## Options

### A. A per-user delegation agent (recommended, chosen)

A small unprivileged helper, `sg-procagent`, runs **as each session user**. The
server delegates the four cross-process primitives to the agent for the uid
that owns the target; the agent, being that user, performs the `ptrace`/`kill`
itself (same uid → the kernel allows it) and returns the result.

- **Adds no privilege anywhere.** The agent has no capabilities; the kernel
  still refuses it any process outside its own uid. A compromised `sgsystem`
  gains nothing new: it could already ask, and the agent's `ptrace` of a
  third user would still fail. The property patch 0005 established — no
  privileged process on a socket every user can reach — is preserved.
- **Windows-identical semantics fall out of it.** Same-user operations succeed
  (the agent is that user); another user's process is refused unless the caller
  is elevated, i.e. `sgsystem`, which the server handles without an agent.
- Cost: a new daemon, a small server↔agent protocol, and session lifecycle.

### B. A privileged helper (`CAP_SYS_PTRACE` + `CAP_KILL`)

One helper with the capabilities, called by the server. Simpler, but a
compromised `sgsystem` could name any pid and the helper would ptrace it —
near-root. It cannot safely verify a pid "belongs to the prefix". Rejected: it
recreates the risk patch 0005 removed.

### C. Give the wineserver the capabilities directly

Worst: the one process that parses requests from every user becomes
root-equivalent. Rejected on sight (this is why patch 0005 exists).

### D. Accept as debt

Rejected by David's compatibility requirement.

## Decision

**A.** The server delegates cross-uid `read_process_memory`,
`write_process_memory`, `send_thread_signal`, and the debug-register
`get/set_thread_context` to a per-user `sg-procagent`. Same-uid operations are
still done directly by the server. No component gains a capability.

## Design

- **Rendezvous.** The agent binds a Unix socket at
  `<prefix>/.sg-procagent.<uid>` (0600, in the group-writable prefix dir) and
  listens. The server connects on demand, checks `SO_PEERCRED` shows the peer's
  uid equals the uid in the name, and caches the fd per uid. No dependency on
  the hashed server directory; both sides derive the path from the prefix.
- **Protocol.** Fixed-size request {op, unix_pid, unix_tid, addr, len, sig} then
  `len` bytes for a write; reply {status, len} then `len` bytes for a read.
  Synchronous, one in flight per uid. The server treats a dead/absent agent as
  "operation failed" — exactly today's behaviour, so no regression when the
  agent is missing.
- **Trust.** The agent performs only what the kernel would let that user do; it
  does not widen anything. The server names Unix pids/tids it already tracks.
- **Lifecycle.** `sg-session` starts one agent per session (as the user),
  alongside the session. It exits with the session.

## Consequences

- `wine-sg` carries the server-side delegation (a new `server/sg_procagent.c`
  and hooks in `ptrace.c`); `sg-session` ships and launches the agent. The
  wire protocol is a shared contract documented in both repos' CLAUDE.md.
- Gate: a second-user test that `DebugActiveProcess`, cross-process
  `ReadProcessMemory`/`WriteProcessMemory` and an async APC succeed for an
  ordinary user with the agent running, and still fail across *different*
  users without elevation (Windows-identical).
- Not covered here: `SeDebugPrivilege` for administrators to debug arbitrary
  users' processes is provided by elevation (ADR 0012) running as `sgsystem`,
  not by the agent.
