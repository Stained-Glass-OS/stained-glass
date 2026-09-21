# 0001. Wine build source for the image

- **Status:** accepted
- **Date:** 2026-09-21
- **Deciders:** Claude Code (Phase 0), pending David's review

## Context

The image needs Wine. Rule 4 of the brief says to start on packaged upstream
Wine and not to fork until a real patch forces it. That still leaves a choice
of *which* packaged Wine: Debian's, or WineHQ's own repository for trixie.

The choice matters beyond convenience. Whatever we pick becomes the baseline
that `sg-testlab` keeps a winetest baseline against, and the thing every future
`wine-sg` patch has to apply cleanly to.

## Options

### A. Debian trixie's `wine` (10.0~repack-6)

In the base repository, so no third-party apt source, no key to manage, and
the image builds from a single trusted origin. Debian's Wine is a repack with
Debian patches, and it lags upstream — 10.0 is the stable branch.

### B. WineHQ's `wine-devel` / `wine-staging` (11.18~trixie-1)

Much closer to upstream, and `wine-staging` is explicitly named in the brief as
acceptable. Costs a third-party apt source and signing key in the image build,
and moves fast enough that the winetest baseline will churn.

## Decision

**Debian's `wine` for Phase 0.** Revisit at Phase 1, when S2 (multi-user
wineserver) will almost certainly require building Wine ourselves anyway, and
the question changes from "which package" to "which upstream tag do we build".

## Evidence

Both repositories were inspected directly rather than trusted from memory.

Debian trixie:

```
$ apt-cache policy wine
wine:
  Installed: 10.0~repack-6
  Candidate: 10.0~repack-6

$ ls -l /usr/bin/wine
lrwxrwxrwx 1 root root 22 /usr/bin/wine -> /etc/alternatives/wine
$ dpkg -S /usr/bin/wine-stable
wine: /usr/bin/wine-stable
```

So `/usr/bin/wine` comes from the `wine` package via Debian's alternatives
system, and on amd64 `wine` is satisfiable by `wine64` alone
(`Depends: wine64 (>= …) | wine32 (>= …)`).

WineHQ for trixie exists and is current:

```
$ curl -sS -o /dev/null -w '%{http_code}\n' https://dl.winehq.org/wine-builds/debian/dists/trixie/Release
200
$ # from dists/trixie/main/binary-amd64/Packages
Package: wine-devel    Version: 11.18~trixie-1
Package: wine-staging  Version: 11.18~trixie-1
Package: wine-stable   Version: 11.0.0.0~trixie-1
```

The functional gate ran against Debian's 10.0 and passed: Wine's
`explorer /desktop=shell,1280x800` produced a desktop window, and `notepad`
launched into it. Nothing in Phase 0 needs anything newer.

```
PASS  wineserver is running
PASS  explorer.exe is running as the shell desktop
PASS  desktop window exists: "shell - Wine Desktop" 1280x720+0+0
PASS  notepad window appeared: "Untitled - Notepad"
```

Neither option was rejected for a failure — B simply costs more than Phase 0
needs. That is worth stating plainly, because it means B is not disqualified
and should be reconsidered on its merits at Phase 1.

## Consequences

- The image builds from Debian alone. No third-party key, no extra apt source.
- We are on Wine 10.0, roughly a release behind. Any upstream fix newer than
  10.0 is unavailable until we move, which will bite the first time we chase a
  bug that is already fixed upstream.
- Debian's repack carries Debian patches. When we start submitting patches
  upstream, we must diff against upstream, not against Debian's tree.
- `sg-testlab`'s winetest baseline will be taken against Debian 10.0, and will
  have to be retaken when this decision is revisited.

**Revisit trigger:** the first time we need a fix newer than 10.0, or the start
of S2 — whichever comes first.
