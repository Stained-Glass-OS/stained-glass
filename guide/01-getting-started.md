# Getting started

Stained Glass OS is a Linux system that looks and works like a Windows
desktop and runs Windows programs. You do not need to know Linux to use it.
This page covers getting it onto a computer and keeping it up to date.

## What you need

- A 64-bit PC, with UEFI or legacy BIOS firmware. Secure Boot must be turned
  off in the firmware settings: the system is not signed for it.
- 4 GB of memory or more (8 GB is comfortable), and 40 GB of disk or more
  (Setup needs at least 11 GB).
- A USB stick of 4 GB or more for the installer.

The [FAQ](../../faq.html) has more on hardware, graphics cards and NVIDIA's
driver.

## Making the installer stick

Download the newest ISO from the [download section](../../index.html#download)
and check it against `SHA256SUMS` beside it. Write it to a USB stick with any
tool that writes disk images (balenaEtcher, Rufus in "DD image" mode, `dd` on
Linux), or copy it onto a Ventoy stick.

## Installing

1. Start the computer from the stick (usually F12, F11, Esc or F8 at power-on
   opens the boot menu).
2. The live system starts. It needs no password; if one is asked for (on a
   text console, say), the account is `live` and the password is empty, and
   `sudo` takes the same empty password. **Install** asks which disk to use,
   whether to keep another system beside it, and for the first account's
   name and password. Leave **Install third-party drivers** ticked for
   NVIDIA graphics and some Wi-Fi cards.
3. When it says so, remove the stick and restart.

If the screen stays black or the sign-in screen never appears, see
[the FAQ](../../faq.html#black-screen): a text screen says what failed and
saves a boot report to the stick.
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

Before each update the system takes a restore point. If an update goes
wrong, choose the restore point in the boot menu, or go back from
**Settings > Update & Security > Recovery**.

Updating does not end anyone's running programs. If an update brings a new
version of the Windows layer that cannot talk to the running one, it restarts
that layer -- programs started from Windows then need starting again.

## Where to get help

**Report a problem** (in Start, or on a program's taskbar button with a
right-click) collects what a developer needs. Report bugs on
[GitHub Issues](https://github.com/Stained-Glass-OS/stained-glass/issues) and
ask questions in
[GitHub Discussions](https://github.com/Stained-Glass-OS/stained-glass/discussions);
the [FAQ](../../faq.html) answers the common ones. The [Administration and remote support](04-administration.md)
page covers looking into a machine from another one.
