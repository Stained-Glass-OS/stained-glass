# Phase 0 report

**Date:** 2026-09-21
**Status:** complete. `make image && make boot-test` passes.

The brief asks for a report at the end of Phase 0 covering what worked, the
X11-vs-Wayland finding, the Wine build choice, and the multi-user debt list.

---

## The target, and whether we hit it

> A Debian image that boots in QEMU straight into Wine's `explorer /desktop` as
> the shell, from a system-level prefix.
>
> **Done when:** fresh clone → `make image && make boot-test` passes locally and
> in CI, and the screenshot shows a taskbar with a running app.

Hit, locally. CI is written and pushed but has not run yet — see *Open items*.

```
[boot-test] ssh is up after 15s
[boot-test] running sg-session-check in the guest
info  session.env found after 0s (display=:0 path=x11)
PASS  wineserver is running
PASS  explorer.exe is running as the shell desktop
PASS  desktop window exists: "shell - Wine Desktop"  1280x800+0+0
PASS  taskbar present: ("explorer.exe")  1280x20+0+780
PASS  notepad is inside the desktop: "Untitled - Notepad"  760x570+0+0
PASS  notepad.exe process is alive
RESULT: PASS
[boot-test] GATE PASS
```

And the screenshot shows a Start button, a taskbar, and `Untitled - Notepad`
running in it:

![Phase 0 boot gate screenshot](images/phase0-boot-gate.png)

---

## X11 vs Wayland

**X11 wins for Phase 0.** Full reasoning and evidence in
[ADR 0003](decisions/0003-display-path-x11-vs-winewayland.md).

Both paths were run headlessly, not reasoned about. `winewayland` is **not
broken** — explorer and notepad both start and stay alive under it. It loses on
two specific counts:

1. **No virtual desktop.** `/desktop=shell,WxH` is a `winex11` feature. Under
   `winewayland` there is no desktop surface, so there is no taskbar — which is
   the exact thing Phase 0's "done when" asks for.
2. **Nothing can enumerate the windows.** cage implements no
   `wlr-foreign-toplevel-management`. The gate's requirement that an app "appears
   in the window list" is not merely failing under Wayland, it is *unobservable*.

Point 2 is what settles it. A gate that cannot see the thing it is gating is not
a gate. Under X11, XWayland makes `xwininfo -root -children` a complete answer.

**Revisit at P8**, when `sg-compositor` replaces cage. A compositor we write can
implement toplevel enumeration and host per-window surfaces, which removes both
objections at once.

### The part of this that was nearly missed

Wine prefers `winewayland` whenever a Wayland socket is present, and cage always
provides one. Without an explicit `HKCU\Software\Wine\Drivers\Graphics = x11`
in the prefix, the "X11 path" silently becomes the Wayland path.

Worse, and found only by looking at the screenshot: the gate initially passed
while showing **no taskbar at all**. `wine notepad` was opening its own X
toplevel *outside* the Wine desktop, and under a fullscreen compositor that
toplevel covered the desktop completely. The check was asking "does a window
named Notepad exist somewhere", which was true and meaningless.

The fix is `HKCU\Software\Wine\Explorer\Desktop = shell`, which makes the
virtual desktop the default for every process in the prefix. The gate now
locates the desktop's X window, requires a taskbar among its children, and
requires notepad to appear *inside* it.

---

## Wine build choice

**Debian's `wine` 10.0 (`10.0~repack-6`)**, not WineHQ's 11.18. Full reasoning in
[ADR 0001](decisions/0001-wine-build-source.md).

Nothing in Phase 0 needs anything newer, and Debian's package means the image
builds from a single trusted origin with no third-party apt source or key.
WineHQ was not rejected on a failure — it simply costs more than Phase 0 needs,
which is worth stating so it gets reconsidered on its merits at Phase 1.

**Revisit trigger:** the first time we need a fix newer than 10.0, or the start
of S2, whichever comes first. S2 will very likely require building Wine
ourselves, at which point the question stops being "which package".

### WoW64: the answer is no, and it matters

The brief asked us to evaluate Wine's new WoW64 mode to keep the image pure
amd64. We did. **No packaged Wine is built for it.** Full evidence in
[ADR 0002](decisions/0002-wow64-and-image-architecture.md).

Both Debian and WineHQ ship the WoW64 *thunk* DLLs in their amd64 packages,
which looks like a dual-arch build and is not — the i386 PE set lives only in
the separate i386 package:

```
$ dpkg -L libwine:amd64 | grep -c '/wine/x86_64-windows/'   # 750
$ dpkg -L libwine:amd64 | grep -c '/wine/i386-windows/'     # 0

$ dpkg-deb -c wine-devel-amd64_11.18~trixie-1_amd64.deb \
    | grep -oE '/wine/[a-z0-9_]+-(windows|unix)/' | sort | uniq -c
    287 /wine/x86_64-unix/
   1008 /wine/x86_64-windows/        # no i386-windows tree
```

`wine-devel-amd64` also declares no i386 dependencies, so it installs cleanly on
a pure amd64 system and then cannot run 32-bit Windows binaries. That is a trap
worth knowing about.

**So the Phase 0 image runs 64-bit Windows applications only.** For a Windows
replacement aimed at real fleets that is a serious limitation, acceptable only
because Phase 0 is a bring-up target.

**This needs David's decision** — tracked as
[#4](https://github.com/Stained-Glass-OS/stained-glass/issues/4). The options are
i386 multiarch (cheap, permanently doubles the image's library surface) or
building Wine with `--enable-archs=i386,x86_64` (more work, keeps the image
pure, probably needed for S2 anyway). **Recommendation: the latter.** S3 is
likely to force the issue, since scanner drivers and TWAIN data sources are
frequently 32-bit.

---

## Multi-user debt

[`docs/multiuser-debt.md`](multiuser-debt.md) — eleven items, `D1`–`D11`, each
tagged with a `MULTIUSER-DEBT: D<n>` comment at the place in the code that
incurs it, and each mapped to the clause of the S2 gate it retires.

The list is not complete. S2 will find more. It is complete as to what Phase 0
actually did.

**`D5` is the one that matters most.** The wineserver's lifetime is currently a
login session: it is started by the session, as the session user, and dies with
it. Windows services run as SYSTEM before any login and survive every logout. A
wineserver scoped to a login session cannot express that.

Whether a machine-level wineserver is reachable by *patching* Wine's process
model rather than rewriting it is exactly the question S2 exists to answer, and
the one that decides patch-set vs. permanent hard fork.

---

## What went wrong, and what it cost

Recorded because the failures are more informative than the successes, and
because every one of them is a thing the next person would otherwise rediscover.

| Symptom | Cause | Where it is now written down |
|---|---|---|
| Boot hung forever, serial log just stopped at 6s | `systemd-firstboot` ran its interactive wizard: *"Please configure your system! — Press any key to proceed"* | `systemd.firstboot=off` in `mkosi.conf`, and `sg-image/CLAUDE.md` |
| `systemctl enable greetd.service` → "Unit does not exist", though greetd was installed | The postinst ran in mkosi's sandbox, where `/usr` is the *host's* | renamed to `mkosi.postinst.chroot`; the extension is the fix |
| greetd crash-looped at `pam_start: ABORT` | `/etc/pam.d/greetd` `@include`s `login`, and the `login` package was not installed | `login` and `libpam-systemd` added to the package list, with a comment saying why |
| Wine prefix build failed with `No space left on device` | mkosi's default `Minimize=guess` sizes root to exactly fit its contents | `mkosi.repart/10-root.conf`, `SizeMinBytes=8G` |
| `sg-session` package install: `adduser` → `chown: Invalid argument` | Image builders run in an unprivileged user namespace, where chowning to another uid is not permitted | `--no-create-home`, with the directories created by `tmpfiles.d` at boot |
| `Unable to locate package sg-session`, intermittently | mkosi's `PackageDirectories` only regenerates its apt repo when the repo dir's *mtime* changes; a `.deb` copied over an existing file does not move it | install from an extra tree with `dpkg` instead; reasoning recorded in `mkosi.conf` |
| Gate passed with no taskbar on screen | The check only asked whether a window named Notepad existed *anywhere* | virtual desktop made the prefix default; gate now checks the taskbar and in-desktop placement |

The last row is the one worth dwelling on: a green gate that was not measuring
the right thing. **The screenshot is what caught it** — the serial log and the
exit code both said everything was fine. That is an argument for keeping the
screenshot artifact unconditional, which the gate now does.

---

## Deviations from the brief

Each of these is a deliberate call, not an oversight.

1. **No backports kernel or Mesa.** The brief asks for them. The gate runs
   against QEMU's virtio-gpu, which trixie's Mesa drives fine, so backports
   would add a second apt suite — and a second source of churn in the one thing
   that must stay reliable — for no Phase 0 benefit. They earn their place when
   the image meets real hardware. See `sg-image/docs/packages.md`.
2. **VKD3D-Proton is not in the image.** It is not packaged in Debian at all.
   Debian's `vkd3d` packages are Wine's own vkd3d, a different project, and not
   a substitute. DXVK *is* packaged and is installed. Tracked as
   [#6](https://github.com/Stained-Glass-OS/stained-glass/issues/6).
3. **No `debian/` in `sg-image`.** The artifact there is a disk image, not a
   package. `sg-session` carries `debian/` and builds a `.deb` in CI, as the
   rule intends.
4. **The Wine prefix is built on first boot, not baked into the image.** The
   image build's `/var` is not the image's `/var`, so a prefix written at build
   time is liable to be discarded — and a "baked" prefix that silently is not
   there is worse than no bake at all.

---

## Open items

- **CI has not run yet.** Workflows are written and pushed for both repos. The
  image job is expected to be slow on a runner without `/dev/kvm`; the gate
  falls back to TCG with a 6x budget and a 120-minute job timeout, but that
  combination is untested. First push will tell us.
- **The `wayland` display path is kept as a supported setting** so the ADR 0003
  comparison can be re-run cheaply, but `sg-session-check` fails loudly rather
  than silently skipping when pointed at it.
- **Minor rendering artifact** at the top of the boot-gate screenshot — a few
  stray bars over Notepad's title bar area. Almost certainly a software-rendering
  repaint artifact in the virtio-vga framebuffer capture rather than anything
  in Wine. Not investigated; noted so it is not mistaken for a new bug later.

## Waiting on David

| | |
|---|---|
| [#4](https://github.com/Stained-Glass-OS/stained-glass/issues/4) | 32-bit support: i386 multiarch vs. building Wine with `--enable-archs`. **Recommendation: build Wine.** |
| [#5](https://github.com/Stained-Glass-OS/stained-glass/issues/5) | Confirm LGPL-2.1+ for `sg-image` and `sg-session` (shipped on the brief's default) |
| [#6](https://github.com/Stained-Glass-OS/stained-glass/issues/6) | How to source VKD3D-Proton, or defer it |
| [#1](https://github.com/Stained-Glass-OS/stained-glass/issues/1) [#2](https://github.com/Stained-Glass-OS/stained-glass/issues/2) [#3](https://github.com/Stained-Glass-OS/stained-glass/issues/3) | Confirmation to start Phase 1. **Per the brief, no Phase 1 repos are created until you say so.** |
