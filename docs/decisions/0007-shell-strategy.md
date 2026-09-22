# 0007. The shell: extend Wine's explorer, add our own panels beside it

- **Status:** accepted (strategy only — no work started)
- **Date:** 2026-09-22
- **Deciders:** David Hamner
- **Relates to:** [P7 shell options](../p7-shell-options.md), [ADR 0004](0004-licensing.md), [ADR 0006](0006-wine-llm-contribution-policy.md)

## Context

The brief left P7 as a time-boxed bake-off between extending Wine's `explorer`
and running ReactOS's under Wine. Research ([`p7-shell-options.md`](../p7-shell-options.md))
turned up one fact that reframes the choice: **Wine's explorer implements the
real shell, not an imitation of one.** `systray.c`'s window class is literally
`Shell_TrayWnd`, and `appbar.c` answers `SHAppBarMessage`. Applications look for
those by name.

It also turned up that the appearance problem is smaller than it looks: Wine's
`uxtheme` is 8,511 lines including `msstyles.c`, so it can load Windows visual
style files. What looks old is the default theme.

## Decision

**Option A, with C's ambition layered on top.** In David's words:

> keep Wine's explorer as the shell process, because that is what makes
> applications behave, and treat the Windows 10 appearance as (i) a visual-styles
> theme and (ii) new panels we write ourselves and dock via the AppBar protocol
> Wine already implements.

So:

- **Wine's `explorer` stays the shell process.** It owns `Shell_TrayWnd`, the
  tray protocol, and AppBar registration — the surface applications actually
  talk to.
- **Appearance is a theme**, not a rewrite.
- **New UI is ours, docked as AppBars** rather than bolted into explorer. A
  Windows 10 Start panel, a notification centre, a search surface — each a
  program of its own that registers with the shell the way any third-party
  AppBar does.

ReactOS's explorer is not chosen, but nor is it dismissed: a measurement of what
it needs from Wine that Wine does not provide is still worth having, and its
file browser is the part most obviously missing from A.

## Why this shape and not the others

Writing a shell from scratch means reimplementing `Shell_TrayWnd`, the tray
protocol, AppBars, and the undocumented corners applications depend on — the
exact surface A already has working. That is the option that looks cheapest at
the start.

Running ReactOS's explorer buys a more complete shell and costs two things: it
is feature-incomplete alpha by its maintainers' own description, and it is
GPL-2.0-only.

## The licensing consequence, which is a good one

ADR 0004 left `sg-shell`'s licence open, pending this bake-off, because ReactOS
being GPL-2.0-only would have forced it away from AGPL. **This decision settles
it, and settles it well:**

- **Changes to Wine's `explorer` are LGPL-2.1+** and live in `wine-sg` as
  patches, like all our Wine work. Per [ADR 0006](0006-wine-llm-contribution-policy.md)
  they are not upstreamed.
- **Our panels are separate programs** communicating through a documented
  protocol, so they carry no Wine code and are **AGPL-3.0-or-later** like the
  rest of the project.

The AppBar boundary is therefore a licence boundary as well as an architectural
one. That is a reason to keep new UI on the far side of it even when bolting
something into explorer would be quicker.

## Consequences

- The first visible milestone is reachable early: a left-aligned, Windows
  10-looking taskbar with a working tray, from theming plus small patches.
- **Taskbar alignment is a setting, not a decision.** `systray.c` already lays
  buttons out from a `pos` variable using `start_button_width`. Left by default,
  centred as an option, per David.
- We take on a themed appearance to maintain, and Wine's `uxtheme` is not a
  complete implementation of visual styles — expect gaps where a `.msstyles`
  element is not drawn.
- The file browser stays missing. That is the clearest thing ReactOS would have
  given us, and the most likely reason to revisit B for one component rather
  than for the shell.

## Not yet

**No work starts here until the image is finished and logs in properly.** The
image currently autologs in — `greetd` with a hardcoded user and no
authentication, debt item `D2`. A shell with no user to belong to is a demo, so
`sg-greeter` comes first.
