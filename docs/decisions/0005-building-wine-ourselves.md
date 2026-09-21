# 0005. Build Wine ourselves, for 32-bit support on a pure amd64 image

- **Status:** accepted
- **Date:** 2026-09-21
- **Deciders:** David Hamner ("whatever we need to do to get max completeness")
- **Relates to:** [0001](0001-wine-build-source.md) (revisits it),
  [0002](0002-wow64-and-image-architecture.md) (resolves the open question)

## Context

[ADR 0002](0002-wow64-and-image-architecture.md) established that no packaged
Wine — Debian's or WineHQ's — is built for new WoW64, and left the Phase 0 image
running 64-bit Windows applications only. It named two ways out and recommended
one:

- **C.** Enable i386 multiarch. Cheap, permanently doubles the image's library
  surface.
- **D.** Build Wine with `--enable-archs=i386,x86_64`. More work, keeps the
  image pure, and is probably needed for S2 anyway.

David's answer was "whatever we need to do to get max completeness", which
selects D — and D is what we would have wanted regardless, since S2 is going to
require building Wine.

## Decision

**Build Wine ourselves, with `--enable-archs=i386,x86_64`, in a new repo
`wine-sg`.** Installs to `/opt/wine-sg`, packaged as a `.deb`, alongside rather
than over a distribution Wine.

This also creates `wine-sg` earlier than rule 4 anticipated. That is
deliberate — see *On rule 4* below.

## Evidence

**It works, and the claim was measured rather than inferred.**

The build produces the new-WoW64 layout: both PE trees, one Unix tree, and
crucially **no `i386-unix`** — no 32-bit Linux side at all.

```
i386-windows     1056 files
x86_64-windows    996 files
x86_64-unix       282 files
i386-unix         (absent)
```

Compare Debian's amd64 `libwine`: 750 `x86_64-windows` PEs and **zero**
`i386-windows`.

A prefix bootstraps with a populated `syswow64` (834 files), and a genuine
32-bit binary runs:

```
$ file .../syswow64/cmd.exe
PE32 executable for WINE (console), Intel i386, 16 sections

$ wine 'C:\windows\syswow64\cmd.exe' /c "echo HELLO_FROM_32BIT_WINDOWS && ver"
HELLO_FROM_32BIT_WINDOWS
Microsoft Windows 10.0.19043
```

And — the part that actually matters — it does so with no 32-bit Linux code
involved. Read from `/proc/<pid>/maps` of the live 32-bit process:

```
ld-linux-x86-64.so.2   ELF 64-bit LSB shared object, x86-64
libc.so.6              ELF 64-bit LSB shared object, x86-64
libtinfo.so.6.5        ELF 64-bit LSB shared object, x86-64

i386 ELF count: 0
```

This is now `wine-sg`'s gate, so it is checked on every build rather than
recorded once in a document.

### What went wrong on the way, because it will recur

The first build compiled cleanly and produced a Wine that **could not start any
process at all** — not even 64-bit `cmd`. Every attempt died with a page fault
on *write* to an address inside `ntdll`'s `.text`, followed by
`could not load kernel32.dll, status c0000135`.

The cause is not ours and not new: **binutils-mingw-w64 2.44**, which Debian
trixie ships, changed section handling such that `winebuild` emits import
address tables into read-only sections. Writing the IAT during module load then
faults. WineHQ bug 57819; Debian bug 1101977.

Debian carries a patch for it. Upstream Wine 10.0 tarballs do not. So:

> **Upstream Wine 10.0, built on Debian trixie with the distribution's own
> toolchain, does not produce a usable Wine.** It builds without error and fails
> at runtime.

`wine-sg` carries that patch, plus three more from Debian's `fixes/` series
(`virtual-protect`, `ntdll-398da925`, `fstype`), each with its DEP-3 header and
original author attribution intact.

This is worth remembering for a reason beyond this bug: it is the first concrete
demonstration that "packaged Wine" and "upstream Wine" are meaningfully
different artifacts, which ADR 0001 treated as a mostly-theoretical distinction.

## Consequences

- **32-bit Windows applications now run on a pure amd64 image.** The most
  serious limitation recorded in ADR 0002 is lifted, and i386 multiarch is
  permanently off the table.
- `sg-image` gains a choice of Wine. Integrating `wine-sg` into the image is
  follow-up work; the Phase 0 gate still passes on Debian's Wine, and switching
  is a deliberate step with its own gate, not a silent swap.
- **We now own a Wine build**, with what that implies: tracking upstream
  releases, re-checking patches on each bump, and a winetest baseline in
  `sg-testlab` tied to the exact build.
- The `--with-sane` divergence is deliberate. Debian builds `--without-sane`;
  S3 needs scanner support, so we keep it. Worth knowing that Debian's Wine
  **cannot** do TWAIN/SANE imaging at all, which would have been a confusing
  discovery in the middle of S3.
- `libnetapi` remains unavailable — it is not packaged in Debian. Relevant to
  P2's domain work; noted now rather than found later.

## On rule 4

> Don't fork until a patch forces it. Create `wine-sg` only when the first real
> patch exists.

The trigger has fired, if slightly sideways: the patches that forced it are
*carried third-party fixes* rather than ours. Without `binutils2.44.patch` there
is no working Wine to build on at all, so the repo is not speculative.

The spirit of the rule is preserved deliberately:

- `wine-sg` is **not a fork**. It is upstream Wine plus a patch series, rebased
  on upstream releases.
- Carried patches live in `patches/fixes/` with their original authorship.
  Patches of ours will live in `patches/sg/`, kept separate so that what we owe
  upstream stays obvious.
- Nothing here diverges from upstream's design. One configure flag and four bug
  fixes.

**This is not the hard-fork decision.** That question belongs to S2, and
[the S2 analysis](../s2-wineserver-analysis.md) answers it separately: patch
series, not fork.
