# 0002. WoW64 mode and the image's architecture

- **Status:** accepted
- **Date:** 2026-09-21
- **Deciders:** Claude Code (Phase 0), pending David's review

## Context

The brief asks us to evaluate Wine's new WoW64 mode with a specific goal: keep
the image pure amd64 and avoid i386 multiarch. Multiarch roughly doubles the
library surface of the image, complicates every future dependency decision, and
is exactly the kind of thing an immutable fleet image should not carry if it can
avoid it.

Wine's "new WoW64" makes this possible in principle. Built with
`--enable-archs=i386,x86_64`, a single 64-bit Wine ships the i386 Windows PE
DLLs alongside the x86_64 ones and thunks between them, so 32-bit Windows
applications run with no 32-bit *Linux* libraries present at all.

The question is whether any *packaged* Wine is built that way.

## Options

### A. Pure amd64, packaged Wine, 64-bit Windows apps only
### B. Pure amd64 via new WoW64, from a packaged Wine built with both archs
### C. amd64 + i386 multiarch, classic WoW64
### D. Build Wine ourselves with `--enable-archs=i386,x86_64`

## Decision

**A for Phase 0: a pure amd64 image, 64-bit Windows applications only.**

B is what we wanted and it is not available. C is the fallback whenever a
32-bit Windows application actually matters, and D is the real answer but is
Phase 1 work, not Phase 0 work.

## Evidence

**B does not exist in either packaged Wine.** Both Debian and WineHQ ship the
WoW64 *thunk* DLLs in their amd64 packages, which looks at first glance like a
new-WoW64 build. It is not: the i386 PE DLL set the thunks need is in the
separate i386 package.

Debian trixie, `libwine:amd64`:

```
$ dpkg -L libwine:amd64 | grep -c '/wine/x86_64-windows/'
750
$ dpkg -L libwine:amd64 | grep -c '/wine/i386-windows/'
0
$ dpkg -L libwine:amd64 | grep -i wow64
/usr/lib/x86_64-linux-gnu/wine/x86_64-windows/wow64.dll
/usr/lib/x86_64-linux-gnu/wine/x86_64-windows/wow64cpu.dll
/usr/lib/x86_64-linux-gnu/wine/x86_64-windows/wow64win.dll
```

The thunks are present; the 750 PE DLLs are all x86_64 and there are zero i386
ones. The i386 PEs live in `libwine:i386`, under `/usr/lib/i386-linux-gnu/`.

WineHQ 11.18 for trixie is built the same way. `wine-devel-amd64` was
downloaded and unpacked to check rather than inferred from its dependencies:

```
$ dpkg-deb -c wine-devel-amd64_11.18~trixie-1_amd64.deb \
    | grep -oE '/wine/[a-z0-9_]+-(windows|unix)/' | sort | uniq -c
    287 /wine/x86_64-unix/
   1008 /wine/x86_64-windows/
```

Again: no `i386-windows` tree. And the thunks are there too
(`./opt/wine-devel/lib/wine/x86_64-windows/wow64.dll`), which is precisely the
trap — their presence does not imply a dual-arch build.

Note that `wine-devel-amd64` declares no dependency on any i386 package, so
"it installs cleanly on a pure amd64 system" is *also* not evidence of new
WoW64. It installs, and then cannot run 32-bit Windows binaries.

**A is sufficient for Phase 0.** The gate's workload — Wine's `explorer` and
`notepad` — is 64-bit, and the whole session gate passes in a `WINEARCH=win64`
prefix with no i386 anything:

```
PASS  wineserver is running
PASS  explorer.exe is running as the shell desktop
PASS  desktop window exists: "shell - Wine Desktop"
PASS  notepad window appeared: "Untitled - Notepad"
PASS  notepad.exe process is alive
RESULT: PASS
```

## Consequences

- The image is plain amd64. No multiarch, no duplicated library stack.
- **32-bit Windows applications do not run on this image.** For a Windows
  replacement aimed at real fleets this is a serious limitation, not a detail —
  plenty of line-of-business software is still 32-bit. It is acceptable only
  because Phase 0 is a bring-up target.
- Buying 32-bit support later costs one of two things, and we should choose
  deliberately rather than by drift:
  - **C**, enabling i386 multiarch — cheap to do, permanently doubles the
    library surface of an image whose whole point is to be small and immutable.
  - **D**, building Wine with `--enable-archs=i386,x86_64` — more work up front,
    keeps the image pure, and is very likely something we end up doing anyway
    for S2.
- **Recommendation:** go to D, not C, and fold it into the Wine build work that
  S2 will force. Taking C first would be the kind of expedient that never gets
  undone.

**This needs David's decision** before any work that assumes 32-bit support.

**Revisit trigger:** the first 32-bit Windows application we actually need —
which S3's TWAIN work may well produce, since scanner vendor drivers and data
sources are frequently 32-bit.
