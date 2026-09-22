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

## The gate exists, and it is red

`sg-multiuser-check` (in `sg-session`) encodes the five clauses of the S2 gate
verbatim and reports each separately. `make multiuser-test` in `sg-image` drives
it against a real booted image. Today:

```
S2 gate: 0 of 5 clauses passing
RESULT: FAIL -- expected until S2 lands
```

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
