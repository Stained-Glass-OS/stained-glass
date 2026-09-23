# 0013. File access in the shared wineserver

- **Status:** accepted — option D, 2026-09-22; implemented 2026-09-23 (wine-sg 0014-0016)
- **Date:** 2026-09-22
- **Deciders:** David; analysis by Claude

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

**D, decided by David on 2026-09-22**: clients open their own files and pass
the descriptors to the server. A remains the fallback if D proves too invasive
to carry. Until D lands, the shared machine-level wineserver is lab-only: not
safe with untrusted users, or with untrusted software run by trusted ones.

## Evidence

- `server/fd.c:1933`: `fd->unix_fd = open( name, rw_mode | ..., *mode )`, in
  the server, reached from the `create_file` handler.
- `sg-file-access-check` in the booted image: 3 of 3 clauses fail, as tabled.
- A file created by `sguser`'s program in `C:\\windows\\system32` was owned by
  `sgsystem`; the same user's `touch` there was refused by Unix.

## Implementation (2026-09-23)

Landed in wine-sg as patches 0014-0016:

| Operation | Who performs it now, for a user other than the server's account |
|---|---|
| open, create (0014) | the client; the server adopts the fd and refuses to open by name |
| delete-on-close, disposition (0015) | the server decides when (last handle); the client whose close makes it due unlinks -- only if it is the user who asked, otherwise the file stays |
| rename, hard link (0015) | the server checks (stage 1), the client renames or links, the server commits (stage 2) |
| reopen / ReOpenFile (0015) | the client reopens through `/proc/self/fd`; the server checks it is the same inode |
| DACL → Unix mode (0016) | the server computes it, the client `fchmod`s |

**Gate:** `sg-file-access-check` in the booted image -- 4 of 4 (the delete
clause was added after the first measurement):

    PASS  an ordinary user's program cannot write into C:\windows\system32
    PASS  an ordinary user's program cannot read a SYSTEM-only file
    PASS  an ordinary user's program cannot delete a SYSTEM file
    PASS  an ordinary user's program can write the user's own private directory

**Conformance**, as the server's own user: kernel32 file, directory, path,
module and ntdll file, directory, om, info match the unpatched baseline (four
`todo_wine` STATUS_CANNOT_DELETE checks now pass); advapi32 security and lsa
pass. **As a second Unix user against a shared server** -- the only setting in
which the new code runs:

| Suite | Failures | Why |
|---|---|---|
| kernel32:directory, ntdll:directory, advapi32:lsa | 0 | |
| kernel32:file | 1 | SE_MANAGE_VOLUME_NAME: the user is not an administrator |
| kernel32:path | 2 | copying into a directory the user may not write -- correct |
| ntdll:file | 6 | two I/O completion tests: the server cannot signal another user's threads (debt D16) |
| advapi32:security | 4 | token details of a standard user (e.g. a non-admin is refused an HKLM key the test expects to create) |

Before 0015's fix of the deletion timing, ntdll:file also failed four
"file shouldn't have been deleted" checks: the first version unlinked when
the handle that *asked* closed, not when the *last* handle closed. The server
has to decide the time; that is why the close reply carries the deletion.

**Not covered:** device nodes (`server/device.c`) still open as the server.

## Consequences

- `sg-file-access-check` is the gate for whichever option is chosen; it is
  expected red until then and stays out of CI.
- D12 (users' SIDs have no names) and D15 (new users' profiles point into
  SYSTEM's) are entangled with this: a correct profile needs per-user
  ownership, which only a fixed file path can give.
- Every feature that relies on a user's program being unable to reach system
  files is unsafe until this lands -- elevation (ADR 0012) above all.
