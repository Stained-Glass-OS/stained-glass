# 0013. File access in the shared wineserver

- **Status:** proposed — awaiting David's decision
- **Date:** 2026-09-22
- **Deciders:** David (pending); analysis by Claude

## Context

Multi-user debt **D14**, found while gating Wine Mono in the image: every
ordinary user's file access is performed with the SYSTEM account's Unix rights.

Wine's server opens files, not the client: `NtCreateFile` sends a
`create_file` request, and the server calls `open()` (`server/fd.c`,
`open_fd`) and passes the descriptor back. In upstream Wine the server runs as
the same Unix user as its clients, so this is harmless. Stained Glass runs **one
machine-level wineserver for everyone, as `sgsystem`, which *is* SYSTEM**
(wine-sg patches 0004/0005) -- so the kernel's permission checks see SYSTEM for
every user's every open.

Measured in the booted image, as the ordinary user `sguser`, comparing Unix
with a Windows program (`sg-session/bin/sg-file-access-check`):

| Operation | Unix | Windows program |
|---|---|---|
| create a file in `C:\\windows\\system32` | denied | **allowed** |
| read a SYSTEM-only (0600) file | denied | **allowed** |
| write the user's own 0700 directory | allowed | **denied** |

The registry is not affected -- wineserver enforces security descriptors on
keys, and a non-admin cannot write `HKLM\\Software\\Policies` -- but file access
is the larger surface. A standard user who can write System32 can plant a DLL a
SYSTEM service will load: **privilege escalation, and weaker than Windows**,
where a standard user cannot. Every elevation design (ADR 0012) assumes this is
fixed first.

The same server also does path-based work besides `open()` -- renames, deletes
(including delete-on-close), directory creation -- so whatever fixes `open()`
must cover those too.

## Options

### A. Give users their own wineservers again

Each session runs a wineserver as its user; SYSTEM's services keep theirs.
Correct file semantics immediately -- this is upstream Wine's model.

Loses what S2 built: one HKLM shared live between users, one SCM visible to
all, services that outlive logins but are reachable from sessions. Those would
need cross-server plumbing Wine does not have. It is the safe fallback, not a
destination.

### B. The server checks Unix permissions itself, as the client

Before each open, the server evaluates owner/group/other bits for the client's
uid and groups on every path component, then opens as SYSTEM.

Keeps the architecture, but re-implements the kernel's access checks in
userspace: POSIX ACLs, sticky directories, capabilities, mount flags, symlinks
-- and a race between the check and the open. Security-critical code that is
wrong in subtle ways by construction. **Not recommended.**

### C. The server borrows the client's identity for each open

`setfsuid`/`setfsgid`/`setgroups` to the client around each file operation, so
the kernel checks the real user.

Correct semantics, small change -- but the server needs `CAP_SETUID` and
`CAP_SETGID`, which makes it root-equivalent: a flaw in the one process that
parses requests from every user would then be a full compromise. Patch 0005
removed root from this server on purpose.

### D. Clients open their own files (recommended)

The client -- running as the user -- performs the `open()` and passes the
descriptor to the server over the socket it already has (`SCM_RIGHTS`; Wine
already moves descriptors this way for other objects). The server keeps its
sharing checks and bookkeeping on a descriptor the kernel issued to the real
user, and stays unprivileged. Path-based operations (rename, delete,
directory creation) move to the client, or are performed on descriptors the
client supplies.

The most principled answer, and the most work: it changes Wine's file
architecture across `dlls/ntdll/unix/file.c` and `server/fd.c`, and wine-sg
carries it forever (ADR 0006). **This is the kind of change that decides
"patch set" versus "hard fork", which is David's call.**

## Decision

**Pending David.** Recommended: **D**, with **A** as the fallback if D proves
too invasive to carry. Until one lands, the shared machine-level wineserver
must be treated as lab-only: it is not safe with untrusted users, or with
untrusted software run by trusted ones.

## Evidence

- `server/fd.c:1933`: `fd->unix_fd = open( name, rw_mode | ..., *mode )`, in
  the server, reached from the `create_file` handler.
- `sg-file-access-check` in the booted image: 3 of 3 clauses fail, as tabled.
- A file created by `sguser`'s program in `C:\\windows\\system32` was owned by
  `sgsystem`; the same user's `touch` there was refused by Unix.

## Consequences

- `sg-file-access-check` is the gate for whichever option is chosen; it is
  expected red until then and stays out of CI.
- D12 (users' SIDs have no names) and D15 (new users' profiles point into
  SYSTEM's) are entangled with this: a correct profile needs per-user
  ownership, which only a fixed file path can give.
- Every feature that relies on a user's program being unable to reach system
  files is unsafe until this lands -- elevation (ADR 0012) above all.
