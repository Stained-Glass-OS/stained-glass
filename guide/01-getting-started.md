# Getting started

Stained Glass OS is a Linux system that looks and works like a Windows
desktop and runs Windows programs. You do not need to know Linux to use it.
This page covers getting it onto a computer and keeping it up to date.

## What you need

- A 64-bit PC that starts in UEFI mode. Secure Boot must be turned off in the
  firmware settings: the system is not signed for it.
- 4 GB of memory or more (8 GB is comfortable), and 40 GB of disk or more.
- A USB stick of 4 GB or more for the installer.

## Making the installer stick

Download the newest ISO from the [download section](../../index.html#download)
and check it against `SHA256SUMS` beside it. Write it to a USB stick with any
tool that writes disk images (balenaEtcher, Rufus in "DD image" mode, `dd` on
Linux), or copy it onto a Ventoy stick.

## Installing

1. Start the computer from the stick (usually F12, F11, Esc or F8 at power-on
   opens the boot menu).
2. The live system starts. **Install** asks which disk to use, whether to keep
   another system beside it, and for the first account's name and password.
3. When it says so, remove the stick and restart.
4. The first start asks a few questions -- region, time zone, privacy -- and
   prepares your account. "Getting things ready" appears only this first
   time.

The first account is an administrator. Make more accounts in **Settings >
Accounts**; each person's files and settings are their own.

## Signing in

The sign-in screen remembers the last person. Press **Other user** to sign in
as someone else. **Win+L** locks the screen; your programs keep running.

## Updates

Updates come from the project's package repository, like any Debian system's.
They download in the background and are installed at the next restart, as
Windows does it -- **Settings > Update & Security** shows what is waiting
and can install now.

An administrator can also update from a terminal at any time:

```
sudo apt update && sudo apt full-upgrade
```

Updating does not end anyone's running programs. If an update brings a new
version of the Windows layer that cannot talk to the running one, it restarts
that layer -- programs started from Windows then need starting again.

## Where to get help

**Report a problem** on a program's taskbar button (right-click) collects what
a developer needs. The [Administration and remote support](04-administration.md)
page covers looking into a machine from another one.
