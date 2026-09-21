# 0003. Display path: cage + XWayland + winex11, or winewayland

- **Status:** accepted
- **Date:** 2026-09-21
- **Deciders:** Claude Code (Phase 0), pending David's review

## Context

Phase 0's target is Wine's `explorer /desktop` running as the shell. The brief
asks us to try both display paths and pick whichever gives a working taskbar
and window management *today*:

- **(a)** cage + XWayland, with Wine's `winex11` driver in virtual-desktop mode.
- **(b)** cage, with Wine's `winewayland` driver.

This is a Phase 0 decision with a short shelf life — P8 replaces cage with
`sg-compositor` and the question reopens — but it decides what the boot gate
can even observe, so it has to be settled now.

## Options

### A. cage + XWayland + `winex11` virtual desktop

Wine's `/desktop=shell,WxH` is a `winex11` feature. It creates one X top-level
window and draws the Wine desktop, including the taskbar, inside it. Every
Windows window is then managed by Wine itself, which is exactly the shape we
want: the shell lives inside the Wine system, and the Linux side only supplies
a surface to put it on.

### B. cage + `winewayland`

The architecturally cleaner destination — no X server in the stack at all — and
where Wine is heading. But `winewayland` has no virtual-desktop mode, so there
is no single desktop surface to host a shell and taskbar; each Windows window
becomes its own `xdg_toplevel`.

## Decision

**A — cage + XWayland + `winex11` virtual desktop — for Phase 0.**

## Evidence

Both paths were run headlessly on Debian trixie with Wine 10.0, under
`cage` 0.2.0 with the wlroots headless backend (`WLR_BACKENDS=headless`,
`WLR_RENDERER=pixman`), in a `WINEARCH=win64` prefix.

**A works, and produces exactly the structure Phase 0 wants.** After starting
`wine explorer /desktop=shell,1280x800`, the X window list contains a single
Wine desktop window, and a subsequently launched `notepad` appears alongside it:

```
0xe00007 "shell - Wine Desktop": ("explorer.exe" "explorer.exe")  1280x720+0+0
0x1400001 "Untitled - Notepad":  ("notepad.exe"  "notepad.exe")   1280x720+0+0
```

(The desktop is 1280x720 rather than the requested 1280x800 because Wine clamps
it to the compositor's output, which is cage's headless default. Worth knowing:
the requested geometry is an upper bound, not a promise.)

**B runs, but cannot be gated.** Under `winewayland`, `explorer` and `notepad`
both start and stay alive — `wine notepad` under a 20s timeout returned 124,
i.e. it was still running when the timeout fired, not crashing:

```
=== notepad exit status under winewayland ===
notepad_rc=124
```

So B is not broken. It fails on two other counts:

1. **No virtual desktop.** `/desktop=shell,WxH` is a `winex11` feature. Under
   `winewayland` there is no desktop surface and therefore no taskbar, which is
   the specific thing Phase 0's "done when" criterion asks for.
2. **Nothing can enumerate the windows.** cage implements no
   `wlr-foreign-toplevel-management`, so there is no way for a script to ask
   what windows exist. The gate's requirement — "a test Win32 app launches and
   appears in the window list" — is not merely failing under B, it is
   *unobservable*. Under A, XWayland makes `xwininfo -root -children` a
   complete and cheap answer.

Point 2 is what actually settles it. A gate that cannot see the thing it is
gating is not a gate.

## Consequences

- `sg-session` defaults to `SG_DISPLAY_PATH=x11` and pins Wine's graphics
  driver to `x11` in the prefix registry. The pin is necessary: Wine prefers
  the Wayland driver when a Wayland socket is present, and cage always provides
  one, so without the pin the x11 path silently becomes the wayland path.
- XWayland is in the image and in `sg-session`'s dependencies. That is a real
  cost — an X server inside a project whose long-term story is Wayland-native.
- `sg-session-check` implements window checks for the x11 path only, and fails
  loudly rather than silently skipping if pointed at the wayland path. The
  `wayland` value is kept as a supported setting so the comparison can be
  re-run cheaply later.
- Nothing here is a verdict on `winewayland` itself. It started both processes
  without complaint; it simply does not offer the two features the Phase 0 gate
  is built on.

**Revisit trigger:** P8, when `sg-compositor` replaces cage. A compositor we
write ourselves can implement toplevel enumeration and can host per-window
Wayland surfaces, which removes both objections at once. The taskbar question
then becomes part of the P7 shell decision rather than a display-driver
question.
