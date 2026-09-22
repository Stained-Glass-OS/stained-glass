# S2: can a machine-level wineserver be reached by patching Wine?

**Date:** 2026-09-21
**Wine version read:** 10.0 (upstream tarball, `sha256 c5e0b3f5…3601`)
**Status:** source analysis complete. No code written yet; no prefix has been
made multi-user. This answers the question the brief says David needs
explicitly, and nothing more.

> **Kill/rescope if:** this requires rewriting Wine's process model rather than
> patching it. Outcome decides "patch set" vs "permanent hard fork". David needs
> that answer explicitly.

## The answer

**Patch set, not a rewrite. Wine's process model does not need to change.**

That is the good news, and it is real. The bad news is that the patch set is
large, touches identity plumbing throughout the server, and is unlikely to be
accepted upstream in one piece — so plan for a **long-lived patch series** in
`wine-sg`, in the spirit of wine-staging, rather than either a quick upstream
merge or a hard fork.

The distinction matters: a hard fork means we own Wine forever and diverge. A
patch series means we rebase onto upstream releases and keep our changes
legible, small, and individually upstreamable where possible. The evidence says
we are in the second case.

## Why the process model survives

The thing that would have forced a rewrite — Wine modelling "one process tree
per user" somewhere structural — is not what the code does. Processes, threads,
handles and objects have no notion of a user at all. Identity lives in exactly
two places: the token attached to a process, and the SID used to name the
registry's per-user branch.

Two pieces of the Windows model are **already present**, which is the strongest
evidence for the patch verdict:

**Sessions already exist, and there are already two of them.**

```c
/* server/directory.c:470 */
create_session( 0 );                   /* the services session */
create_session( default_session_id );  /* the interactive session */
```

Wine already models Session 0 vs Session 1, the same split Windows uses to
separate services from the interactive desktop. The session object is not a
stub bolted on for one case; it takes an id. What is missing is not the concept
but its use — see below.

**The per-user registry path is already parameterised by SID.**

```c
/* server/registry.c:1832 */
static WCHAR *format_user_registry_path( const struct sid *sid, struct unicode_str *path )
```

The function that decides where `HKEY_CURRENT_USER` lives already takes a SID
argument. It is simply only ever called with one.

Wine's architecture anticipated multi-user. Its implementation hardcoded a
single user on top of it. That is the shape of a patchable problem.

## What actually has to change

Six changes, in dependency order. Each is bounded; none rewrites the object
model.

### 1. The transport is per-uid, with two hard assertions

```c
/* server/request.c:646 */
asprintf( &base_dir, "/tmp/.wine-%u", getuid() );
```

and, in `create_dir()`:

```c
/* server/request.c:591-592 */
if (st->st_uid != getuid()) fatal_error( "%s is not owned by you\n", name );
if (st->st_mode & 077) fatal_error( "%s must not be accessible by other users\n", name );
```

A second user cannot reach the first user's wineserver socket. Not by policy —
by construction, and with two `fatal_error` calls that exist specifically to
prevent it. The same check is applied to the prefix directory itself
(`request.c:637`).

**Change:** a machine-wide server directory, the ownership and mode assertions
replaced with something that permits a shared socket, and a deliberate access
policy in their place.

**Risk:** low, and localized to one file. But note that these assertions are a
*security control*, not an accident. Removing them without replacing them with
peer authentication (below) would be strictly worse than the status quo.

### 2. The server never learns who connected

```
$ grep -rn 'SO_PEERCRED\|ucred' server/*.c
(nothing)
```

wineserver does no peer credential checking anywhere. It has never needed to:
the 0700 directory guarantees the peer is the owner, so "who are you" has a
constant answer.

**Change:** authenticate connecting clients via `SO_PEERCRED`, and carry the
connecting uid into the process object so everything downstream can use it.

**Risk:** low in mechanism, high in consequence. This becomes the security
boundary for the entire machine. It is the single most security-sensitive patch
in the set and should be reviewed as such.

### 3. Identity is binary: you, or not-you

```c
/* server/token.c:201-208 */
const struct sid *security_unix_uid_to_sid( uid_t uid )
{
    /* very simple mapping: either the current user or not the current user */
    if (uid == getuid())
        return &local_user_sid;
    else
        return &anonymous_logon_sid;
}
```

This is Wine's entire identity model, and the comment is candid about it. There
is one real SID. Everyone else is Anonymous Logon.

**Change:** a genuine SID↔uid mapping, backed by winbind so that domain SIDs
resolve. This is the natural home for the `D3` debt item.

**Risk:** moderate. The function is small and its contract is clear, but every
caller was written knowing the answer was constant.

### 4. Every process is an administrator

```c
/* server/process.c:715 */
process->token = token_create_admin( TRUE, -1, TokenElevationTypeLimited, default_session_id );
```

There is exactly one token-creation path for new processes, and it is
`token_create_admin`. Wine has no non-admin process token.

**This is why the S2 gate clause "non-admin cannot write
`HKLM\Software\Policies`" cannot pass today, and it is not a matter of tuning a
security descriptor: there is currently no such thing as a non-admin.**

**Change:** build the process token from the authenticated uid's SID and group
memberships, with administrator status a property of the user rather than a
constant.

**Risk:** moderate-to-high, not in the patch but in the fallout. A great deal of
Wine works today *because* everything runs elevated. Expect this change to
surface a queue of latent permission bugs, in Wine and in applications. Budget
for that discovery rather than treating each one as a surprise.

### 5. One HKCU, mounted once, at startup

```c
/* server/registry.c:1948-1956 */
/* load user.reg into HKEY_CURRENT_USER */
current_user_path = format_user_registry_path( &local_user_sid, &current_user_str );
load_init_registry_from_file( "user.reg", hkcu );
```

`HKLM` (`system.reg`) is genuinely machine-wide already and needs no structural
change — good news for the "both users read the same HKLM" clause. But the user
hive is loaded once at server startup, for one SID, from one file.

**Change:** load and unload a per-user hive on login and logout, keyed by the
user's SID, with `user.reg` becoming per-user rather than per-prefix.

**Risk:** moderate. Bounded by the fact that the path function is already
SID-parameterised, but hive lifetime becomes tied to session lifetime, which is
new.

### 6. Access checks are bypassed in about twenty places

```
$ grep -rn 'alloc_handle_no_access_check' server/*.c | wc -l
20
```

Spread across 16 files, including `registry.c`. Each is a place where a handle
is allocated without evaluating the object's security descriptor — harmless when
every caller is the same all-powerful user, and load-bearing once that stops
being true.

**Change:** audit all twenty, and enforce checks where the object is
security-relevant. The brief scopes S2 to "at least registry and services",
which makes this tractable: fix those, document the rest.

**Risk:** broad but mechanical. This is the tedious part, not the hard part.

### And the one that is already nearly done

```c
/* server/process.h:145 */
static const unsigned int default_session_id = 1;
```

Every process is placed in session 1 via a compile-time constant. But the
session *objects* already exist for both 0 and 1. Making session assignment a
property of how a process was started — a service in session 0, a login session
in its own — is a small change sitting on an abstraction that is already there.

This is what a machine-level wineserver needs in order to run services as SYSTEM
before anyone logs in, which is debt item `D5` and the hardest clause of the S2
gate.

## What this means for the debt list

Mapping the six changes onto [`multiuser-debt.md`](multiuser-debt.md):

| Change | Retires |
|---|---|
| 1. machine-wide transport | `D5` (partly) |
| 2. peer authentication | `D3` (prerequisite) |
| 3. real SID↔uid mapping | `D3` |
| 4. per-user process tokens | `D1`, `D4` |
| 5. per-user hive load/unload | `D1`, `D9` |
| 6. access-check audit | `D1`, `D4` |
| session assignment | `D5`, `D6`, `D7` |
| machine-level wineserver (**done**) | `D5`, `D6` |

## Recommendation

1. **Proceed with S2 as a patch series**, not a fork. Target `wine-sg`, rebased
   on upstream releases.
2. **Write the gate first, and let it fail.** The S2 gate is scripted and
   specific; having it red and honest from day one is worth more than any amount
   of design up front.
3. **Sequence the patches by dependency**, in the order above. Changes 1 and 2
   must land together — change 1 alone removes a security control, and change 2
   is what replaces it.
4. **Expect change 4 to be the expensive one**, not because the patch is hard
   but because dropping universal administrator rights will surface latent bugs
   for a while.
5. **Upstream what is separable.** A real `security_unix_uid_to_sid` and the
   access-check audit are plausibly upstreamable on their own merits. The
   machine-wide socket almost certainly is not. Per the brief, check Wine's
   current policy on AI-assisted contributions *before* submitting anything, and
   record it in an ADR.

## Progress: 4 of 5 clauses

`sg-multiuser-check` (in `sg-session`) encodes the five clauses verbatim and
reports each separately. `make multiuser-test` in `sg-image` drives it against a
real booted image.

```
== clause 1: two Unix users can both use the system Wine
PASS    both users ran a Windows process against the system prefix
== clause 2: both users read the same HKLM
PASS    a value written to HKLM by sgtest1 is visible to sgtest2
== clause 3: a non-admin cannot write HKLM\Software\Policies
FAIL    sgtest2 wrote to HKLM\Software\Policies
== clause 4: each user has an isolated HKCU
PASS    sgtest1's HKCU value is not visible to sgtest2
== clause 5: SYSTEM service visible to both via SCM
PASS    both users see 'PlugPlay' via the SCM: STATE : 4  RUNNING
S2 gate: 4 of 5 clauses passing
```

Per-user hives are real and persist, one file per user beside `system.reg`:

```
-rw-r--r-- 1 sgtest1 sgwine 3134009 system.reg
-rw-r--r-- 1 sgtest1 sgwine   36223 user-1001.reg
-rw-r--r-- 1 sgtest1 sgwine   16870 user-1002.reg
```

Changes 1 and 2 are done, as
`wine-sg/patches/sg/0001-shared-system-prefix.patch`. Two users now run Windows
processes against one system prefix, served by **a single wineserver**:

```
$ pgrep -a wineserver
2022171 /opt/wine-sg/bin/wineserver     # started by sgtest1
$ ps -eo user,comm | grep cmd.exe
sgtest2  cmd.exe                        # sgtest2's process, on sgtest1's server
```

The remaining three failures are exactly the ones predicted below, and need
changes 4, 5 and the session work respectively.

### What the analysis underestimated

Worth recording, because all three were invisible from reading alone:

1. **The ownership assumption is four checks, not one** — prefix directory,
   server directory, socket, *and* lock file. Fixing three of them gives the
   second user `error creating .../lock: Permission denied` from a directory
   they can demonstrably write to, because it is the existing file's mode
   refusing them rather than the directory's.
2. **Group ownership has to be set explicitly** on everything created in shared
   mode. Left alone these carry the primary group of whoever started the server
   first, so the first login silently locks everyone else out.
3. **The rule is implemented twice.** `dlls/ntdll/unix/server.c` has its own
   copy of the server-directory logic, because the client must work out where
   the server lives on its own — it may be the process that starts it. The
   analysis below reads `server/` only and so missed this entirely. Patching one
   side alone fails with `chdir to /tmp/.wine-<uid>/server-<dev>-<ino>: No such
   file or directory`, which names neither the cause nor the file to fix.

Point 3 is the one to carry forward: **assume every server-side assumption in
this document has a client-side twin**, and check `dlls/ntdll/unix/` before
estimating any of the remaining changes.

### And a fourth, from doing changes 3 to 6

**Change 6 is much larger than "audit twenty call sites".** The call sites are
not the problem:

```c
/* server/token.c, check_object_access() */
if (!obj->sd)
{
    if (*access & MAXIMUM_ALLOWED) *access = mapping.all;
    return TRUE;
}
```

Objects are created **without** a security descriptor unless a caller supplies
one, and an object without one grants everything. So the registry is not
under-checked so much as *un-checkable*: no descriptor written to a key can
protect it while its neighbours have none and the check short-circuits. Change 6
therefore includes deciding a **default descriptor policy**, which is a design
decision rather than an audit.

**Changes 3 and 5 are one change, not two.** A SID per uid without per-user
hives leaves every user but the first with no `\Registry\User\<SID>` at all,
and every HKCU operation failing with `OBJECT_NAME_NOT_FOUND`. `MAX_SAVE_BRANCH_INFO`
was exactly 3 — `system.reg`, `userdef.reg`, `user.reg` — so there was not room
for even one extra hive.

**The default DACL has a wrong answer that looks right.** Naming the creating
user protects HKLM keys by making them invisible to everyone else, which breaks
HKLM as shared machine state. The gate caught it exactly: clause 3 began passing
and clause 2 began failing in the same run. What works is the arrangement
Windows uses — system and administrators write, everyone else reads — with
per-user privacy coming from HKCU being a separate hive.

## Clause 5 is done: a machine-level wineserver

`sg-wineserver.service` runs a persistent wineserver as root before `greetd`,
and `sg-services-start` starts `services.exe` inside it. Root maps to the SYSTEM
SID (`patches/sg/0004`), so the services it hosts are SYSTEM's.

```
$ ps -o user,pid,comm -C wineserver
root     2335882 wineserver          # one server, before any login

$ sudo ... wine sc query PlugPlay    # as SYSTEM
SERVICE_NAME: PlugPlay
        STATE              : 4  RUNNING

# and from both logged-in users, through the same SCM:
sgtest1: SERVICE_NAME: PlugPlay   STATE : 4  RUNNING
sgtest2: SERVICE_NAME: PlugPlay   STATE : 4  RUNNING
```

That retires **D5**, which this document called the deepest item on the debt list
and the one most likely to decide patch-set vs. hard fork. It did not require
rewriting Wine's process model — the session-scoped lifetime turned out to be a
property of *who starts the server*, not of the server itself. The patch-set
verdict holds.

**One caveat worth carrying, not burying.** It runs as root, which is the
Windows model — SYSTEM is privileged — but it is a root process serving a socket
every desktop user can reach, so a wineserver flaw becomes a root flaw. The
`SO_PEERCRED` check from patch 0001 guards that socket, which is precisely why
those two patches were inseparable. A dedicated unprivileged account mapped to
the SYSTEM SID would keep the NT semantics without the real privilege, and is
worth doing before this ships anywhere that matters.

## Clause 3: the mechanism works, and the state does not survive

The access control itself is done and demonstrably correct. Within a single
live server session:

```
admin:     reg add HKLM\Software\LiveTest /v A   -> success
non-admin: reg add HKLM\Software\LiveTest /v B   -> Unable to access or create
                                                     the specified registry key
```

Identity is right too — the server reports `uid=1002 prefix_owner=1001
is_admin=0`, with the Administrators group dropped from that token.

**The gate still fails because Wine stores no registry security at all.**
`save_subkeys()` in `server/registry.c` writes a key's name, timestamp, class,
symlink flag and values. There is no field for a security descriptor in the
`.reg` format, and none is written:

```c
fprintf( f, "] %u\n", ... );          /* name and modification time */
fprintf( f, "#time=%x%08x\n", ... );
if (key->class) ...                   /* class */
if (key->flags & KEY_SYMLINK) ...     /* symlink flag */
for (i = 0; i <= key->last_value; i++) dump_value( &key->values[i], f );
```

So every descriptor lives only as long as the wineserver. Protection applied by
`sg-prefix-init` is gone by the time a login session starts a new server, which
is exactly the gap between "the mechanism works" and "the gate passes".

This is a bigger deal than clause 3. **P3 (`gpo-agent`) depends on it**: applying
a GPO means writing policy into the registry and having it stay protected across
reboots. Registry security that evaporates on restart cannot support that.

Three ways out, and the choice is a design decision rather than a patch:

1. **Extend the `.reg` format** to carry descriptors. Most faithful to Windows,
   where the hive stores them. Changes the on-disk format, so prefixes written
   by a patched Wine are no longer readable by an unpatched one — worth weighing,
   since it is a one-way door for any prefix in the field.
2. **Store descriptors beside the hive**, in a file of our own keyed by key path.
   Keeps `.reg` compatible; adds a second source of truth that can drift from it.
3. **Reapply a policy at every server start**, from a declarative list of
   protected branches. No format change and no drift, but it only protects
   branches someone thought to list, and says nothing about descriptors an
   application sets for itself.

Option 3 is the cheapest and is enough for the S2 gate; options 1 and 2 are what
P3 will actually need. **Worth deciding deliberately before building any of it.**

**This is deliberate and should stay red until S2 lands.** It is not wired into
`make test` or CI, because a known-red gate sitting in CI would mask real
regressions. Run it on purpose.

Each clause names what blocks it rather than failing bare, and clauses that
cannot be attempted say so instead of reporting a misleading failure:

```
== clause 3: a non-admin cannot write HKLM\Software\Policies
BLOCKED cannot test: clause 1 must pass first
        note: even once it can run, Wine creates every process token with
        token_create_admin() (server/process.c:715). There is currently no
        such thing as a non-admin, so this clause cannot pass by tuning a
        security descriptor.
```

### Clause 1's failure is now demonstrated, not asserted

The first attempt fails with an ordinary Unix `Permission denied`, which invites
the conclusion that a `chmod` would fix it. So the gate goes further: it builds
a prefix owned by one test user, makes it accessible to everyone, and has the
other user try again.

```
diagnostic: is this just file permissions?
  no. With sgtest1's prefix chmod'ed a+rwX, sgtest2 still cannot use it:
    wine: '/tmp/sg-mu-test/shared-prefix/prefix' is not owned by you
```

That is Wine's own `fatal_error`, reached with the permission bits wide open.
The source analysis said no permission bits can satisfy `st_uid != getuid()`;
this is that claim, run.

## Caveat

The six changes above are a reading of the source, not a demonstration. That
reading is strong enough to answer the patch-vs-fork question, which is what the
brief asked for at this stage. The failure modes are now demonstrated by the
gate; the *estimates of risk* remain judgements and should be re-examined as the
patches land.
