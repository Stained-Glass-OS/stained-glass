# P7: the shell — what we would actually be starting from

**Date:** 2026-09-22
**Status:** research only. Nothing started; P7 comes after the image is finished
and logging in properly. Written now because David asked what the options
really are, and two of them look worse from a distance than up close.

**The goal:** a Windows 10-like desktop, as compatible as we can make it. Start
bar left-aligned by default, with centering as a setting.

---

## The finding that reframes this

**Wine's explorer is not a mock-up of a shell. It implements the real one.**

```
programs/explorer/systray.c    1273 lines   class name: Shell_TrayWnd
programs/explorer/desktop.c    2580 lines   virtual desktop, desktop icons
programs/explorer/startmenu.c   525 lines   Start menu
programs/explorer/appbar.c      311 lines   SHAppBarMessage / AppBar protocol
programs/explorer/explorer.c    945 lines
```

`Shell_TrayWnd` is the actual window class Windows uses for the taskbar. Real
applications look for it by name — to find the tray, to dock an AppBar, to ask
where the taskbar is. Wine already answers all of that, and `appbar.c` already
reports the taskbar's edge and size to applications that ask.

It already has a Start button, task buttons, a system tray with tooltips and
balloon notifications, and layout parameterised rather than hardcoded:

```c
static BOOL enable_taskbar;   /* show full taskbar, with dedicated systray area */
static int start_button_width, taskbar_button_width;
```

**So "it looks old" is true and is not the same as "it is old".** What looks old
is the default theme, not the structure.

### And the appearance is a solved problem in Wine already

```
dlls/uxtheme/    8511 lines, including msstyles.c
```

Wine implements **visual styles**, including parsing Windows `.msstyles` theme
files. A Windows 10 appearance is a theming exercise on top of a shell that
already has the right bones — not a rewrite.

### The centered Start bar is a setting, not a decision

`systray.c` lays buttons out by walking a `pos` variable from the left, using
`start_button_width` and `taskbar_button_width`. Making alignment configurable
is a small patch against code that is already parameterised. It does not need to
influence which shell we build on, so it should not be allowed to.

---

## The three options

### A. Extend Wine's `explorer`

**For:** the window classes are already right, so application compatibility
comes for free rather than being reimplemented. Actively maintained upstream, so
we rebase rather than diverge. LGPL-2.1+, which fits the patch-series model
`wine-sg` already uses. `uxtheme` gives us the Windows 10 look without new
machinery.

**Against:** it is a *thin* shell. There is no file browser, the Start menu is
rudimentary, and there is no notification centre, no search, no pinning, no
jump lists. Everything beyond the taskbar is ours to write.

**Licensing:** LGPL-2.1+. Wine-bound, so it goes in `wine-sg` — and per
[ADR 0006](decisions/0006-wine-llm-contribution-policy.md) we do not upstream.

### B. Run ReactOS `explorer.exe` under Wine

**For:** a much more complete Win32 shell — real Start menu, file browser,
property sheets. It targets public Win32 plus known undocumented shell ordinals
and is tested against real Windows, so failures are ordinary Wine bugs with a
clear owner.

**Against:** ReactOS 0.4.16 (August 2026) is still **feature-incomplete alpha by
its own maintainers' description**, recommended for evaluation and testing
rather than use. Its shell also expects more of the system than Wine currently
provides, so "run it under Wine" is itself a body of work with an unknown floor.

**Licensing — and this is the part that is not negotiable:** ReactOS is
**GPL-2.0-only**, which is incompatible with AGPL-3.0 in both directions.
Choosing B means `sg-shell` cannot be AGPL. That is a licence decision made by a
technical choice, which is exactly the kind of thing worth noticing before
rather than after. Recorded in [ADR 0004](decisions/0004-licensing.md).

### C. Write one from scratch

**For:** total control over appearance and behaviour. No upstream to track.

**Against:** we would be reimplementing `Shell_TrayWnd`, the tray protocol,
AppBars, and the undocumented corners applications actually depend on — the
exact surface option A already has working. This is the option that looks
cheapest at the start and is not.

---

## Recommendation

**A, with C's ambition layered on top.** Concretely: keep Wine's `explorer` as
the shell *process*, because that is what makes applications behave, and treat
the Windows 10 appearance as (i) a visual-styles theme and (ii) new panels we
write ourselves and dock via the AppBar protocol Wine already implements.

That keeps the compatibility surface we would otherwise have to rebuild, and it
means the first visible result — a left-aligned, Windows 10-looking taskbar with
a working tray — is reachable early rather than after a shell rewrite.

**B stays worth a measurement, not a commitment.** The brief's instinct to
time-box a bake-off is right; what it should produce is a list of what
ReactOS's explorer needs from Wine that Wine does not yet give it. If that list
is short, B becomes interesting for the file browser alone. If it is long, we
have an answer and a licence we did not have to accept.

---

## What has to happen first

Nothing here should start yet. Ahead of it:

1. **The image, finished and tested end to end in a VM** — which is where this
   is now.
2. **A real GUI login.** The image currently *autologs in*: `greetd` is
   configured with a hardcoded user and no authentication, which is debt item
   `D2` and explicitly a placeholder. A desktop with no login is not a desktop
   anyone can ship, and it is also the thing that makes the shell work
   meaningful — a shell with no user to belong to is a demo.

Item 2 is `sg-greeter` (P8), and it is the honest next milestone after the
image.
