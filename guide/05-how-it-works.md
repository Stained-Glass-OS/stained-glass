# How it works

This page explains, in plain terms, what happens between pressing the power
button and using a Windows program on Stained Glass -- the parts, what each
is for, and how they fit. The engineering detail lives in each repository's
`CLAUDE.md` and the architecture decisions listed on the [documentation page](../index.html).

## The two halves

A Stained Glass machine is a Debian Linux system with a Windows layer built
in. The Linux half owns the hardware, the accounts, the files, networking and
updates. The Windows half -- **Wine**, an open-source reimplementation of the
Windows programming interfaces, in the project's own build (*wine-sg*) --
runs Windows programs on top of it. No Microsoft code is included; programs
you install bring their own.

The desktop you see -- Start, the taskbar, File Explorer, Settings, Task
Manager -- is the project's own software running in that Windows layer, so
Windows programs find the shell they expect, and Linux programs are given
the same frames and taskbar buttons.

## From power-on to the desktop

1. **Firmware and kernel.** The machine starts the Linux kernel; a splash
   screen in the project's colours shows while it starts.
2. **The machine's Windows side.** Before anyone signs in, two services set
   up the Windows layer for the whole machine:
   - `sg-prefix-init` keeps the machine's Windows installation (its `C:`
     drive, under `/var/lib/stained-glass/prefix`) up to date with the
     installed version and its settings.
   - `sg-wineserver` then starts the **machine's wineserver** -- think of it
     as the Windows kernel's bookkeeping: processes, windows, the registry,
     locks. Everyone's Windows programs, and the Windows services that run
     without anyone signed in, share this one server, as programs on Windows
     share one system. It runs as a dedicated account that the Windows side
     sees as **SYSTEM**.
3. **The sign-in screen.** A small compositor shows the sign-in screen.
4. **Your session.** After you sign in, the **compositor** (*sg-compositor*)
   takes over the screen for you. It is the only program that draws to the
   display and the only one that sees the keyboard first, which is why it,
   and not any program, handles Ctrl+Alt+Del, Win+L, the lock screen and the
   administrator prompts: no program can fake or intercept them.
5. **The desktop.** Inside the compositor runs an X server (*Xwayland*) and,
   in it, the shell: `explorer.exe` drawing the desktop, Start and the
   taskbar as one Windows "virtual desktop" filling the screen. A small
   **keeper** watches it: if the shell crashes, it starts again within
   seconds, and so do its helpers (Start, the tray icons, the visual
   effects).

## Where things live

| On the Windows side | On the Linux side |
|---|---|
| `C:\` | `/var/lib/stained-glass/prefix/drive_c` |
| `C:\users\jane` | `/home/jane` -- the same folders |
| `Z:\` | `/` -- the whole Linux file system |
| `HKLM` (the machine's registry) | kept by the machine's wineserver |
| `HKCU` (Jane's registry) | Jane's own, loaded when she signs in |

Files are protected by Linux permissions underneath, and Windows permissions
are mapped onto them: what Jane may not touch on one side, she may not touch
on the other.

## Accounts and administrators

Each person is a Linux account and, on the Windows side, a Windows user with
their own profile and registry. Administrators are the members of the
`sg-admins` group. A Windows program that asks for an administrator goes
through the **elevation broker**: the compositor puts up the prompt where no
program can reach it, and the approved program runs as SYSTEM on a display of
its own, composited into your screen -- so nothing you run unprivileged can
send it keys or read it.

## Linux programs on the desktop

A Linux program opens its own window in the X server. The taskbar notices it,
gives it a button, and wraps it in the same frame as a Windows window, so it
moves, snaps, minimizes and switches like one. Task Manager lists it and can
end it.

## Updates

Every part -- Wine, the shell, the session, the compositor, the apps the
project makes -- is a Debian package in the project's repository. An update
replaces packages, refreshes the machine's Windows installation in place,
and leaves running programs running.
