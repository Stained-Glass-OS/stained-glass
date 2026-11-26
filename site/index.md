<div class="hero" markdown="1">

# Stained Glass OS

<p class="lead">A free, open-source operating system that looks and works like Windows 10 &mdash;
and runs Windows programs. Debian underneath, Wine (with our own patch series) running the whole
Windows side, and a shell, Control Panel and apps written from scratch to behave like the real thing.</p>

<div class="buttons">
<a class="btn" href="iso/sg-live-latest.iso">Download the ISO</a>
<a class="btn secondary" href="faq.html">FAQ</a>
<a class="btn secondary" href="docs/index.html">Read the docs</a>
<a class="btn secondary" href="https://github.com/Stained-Glass-OS">Source on GitHub</a>
</div>

<div class="notice" markdown="1">

**Early development.** Stained Glass OS is not yet ready for everyday use. Try it in a virtual
machine or the live session first. Nothing on your computer changes until you run Setup's install.

</div>

</div>

## See it in action

<div class="videos" markdown="1">
<div markdown="1">

**Newest: Is Stained Glass OS just reskinned Linux?** Multi-monitor, accent colours, scaling, how
each kind of Windows app runs, gaming and anti-cheat.

<div class="video"><iframe src="https://www.youtube-nocookie.com/embed/2nwHxD833-8" title="Is Stained Glass OS Just Reskinned Linux?" loading="lazy" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>

<p><a href="https://youtu.be/2nwHxD833-8">Watch on YouTube</a> &middot; <a href="videos.html#update-1">Transcript</a></p>

</div>
<div markdown="1">

**The tour: Reverse-Engineered Windows.** Installing it, the desktop, the app store, Windows and
Linux apps side by side, Microsoft Word and OneDrive.

<div class="video"><iframe src="https://www.youtube-nocookie.com/embed/WEEd3b-GIPE" title="Reverse-Engineered Windows" loading="lazy" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>

<p><a href="https://youtu.be/WEEd3b-GIPE">Watch on YouTube</a> &middot; <a href="videos.html#tour">Transcript</a></p>

</div>
</div>

All the videos, with transcripts: [Videos](videos.html).

![The Stained Glass OS desktop with the Start menu open](img/desktop.png){: .shot}

## What it is

Stained Glass OS is a drop-in replacement for Windows on desktops and managed fleets: the
Start menu, taskbar, File Explorer, Control Panel and Settings a Windows user expects, running
Windows programs directly &mdash; 32- and 64-bit &mdash; with multiple users, a real lock screen,
domain join, Group Policy and Remote Desktop.

<div class="grid" markdown="1">
<div class="card" markdown="1">

### Feels like Windows 10

Start menu, taskbar, virtual desktops and Task View, snap, Win-key shortcuts, File Explorer
with search and progress dialogs, Settings (Win+I) and a full Control Panel.

</div>
<div class="card" markdown="1">

### Runs Windows programs

Our Wine build runs 32- and 64-bit programs from one install: Git for Windows, PowerShell 7,
Python, .NET Framework apps, installers (MSI, NSIS), winget, Microsoft Office when you
install it yourself, and DirectX games through DXVK and VKD3D-Proton.

</div>
<div class="card" markdown="1">

### The apps you expect

Notepad (a real code editor with tabs and highlighting), Calculator, Paint, Snipping Tool,
Photos, Media Player, Task Manager, Terminal, Alarms &amp; Clock, Sticky Notes, Character Map,
and the admin tools: Services, Event Viewer, Device Manager, Disk Management.

</div>
<div class="card" markdown="1">

### Voice typing, offline

Win+H dictates into any program, like Windows 10 &mdash; using NVIDIA's open Parakeet model,
installed with the system and running entirely on your computer. Nothing you say leaves it.

</div>
<div class="card" markdown="1">

### Built for fleets

Multiple users with Windows-style accounts and administrators, UAC-style elevation, joining an
Active Directory domain (or being its domain controller), Group Policy, drive maps and logon
scripts, and Remote Desktop in.

</div>
<div class="card" markdown="1">

### Open, top to bottom

Everything is free software (AGPL-3.0 for our code). No Microsoft code or artwork is included;
compatibility comes from re-implementing the documented Windows APIs ourselves.

</div>
</div>

<div class="grid" markdown="1">
![File Explorer](img/explorer.png){: .shot}
![Notepad](img/notepad.png){: .shot}
![Stained Glass Settings](img/settings.png){: .shot}
</div>

<div class="grid" markdown="1">
![Firefox, installed with the system, showing this website](img/firefox.png){: .shot}
![Steam, installed with its own installer, signing in](img/steam.png){: .shot}
</div>

## Download {#download}

<div class="notice" markdown="1">

**Stained Glass OS is not Microsoft Windows.** It is an independent, free and open-source
operating system that is designed to be *compatible with* Windows programs. It is not a Microsoft
product, contains no Microsoft code, and is not affiliated with, endorsed by, or sponsored by
Microsoft Corporation in any way. Windows is a trademark of Microsoft Corporation.

</div>

<div class="notice" markdown="1">

**Early development.** Stained Glass OS is not yet ready for everyday use. Try it in a virtual
machine or the live session first. Nothing on your computer changes until you run Setup's install.

</div>

**[sg-live-latest.iso](iso/sg-live-latest.iso)** &mdash; about 3.3 GB, for 64-bit PCs with UEFI
or legacy BIOS firmware. Secure Boot must be turned off. The SHA-256 checksum is in
[/iso/](iso/).

1. Write it to a USB stick (any image writer, Rufus in "DD image" mode, `dd`, or copy it onto a
   Ventoy stick), or attach it to a virtual machine's CD drive. In a VM, give it at least 4 GB of
   memory and a 24 GB disk; UEFI (VirtualBox: *Enable EFI*; virt-manager/QEMU: OVMF) and BIOS
   firmware both work.
2. Boot it and choose **Stained Glass OS (live: try or install)**. The live session needs no
   password; if one is asked for, the account is `live` with an empty password.
3. Setup appears. Choose **Try Stained Glass OS** to use it without changing the computer, or
   **Install now** to install it: pick or create a partition (it can go beside Windows), then
   name the computer and create your account.

Nothing on the computer changes until you run Setup's install.

![Setup: choosing where to install](img/setup-disk.png){: .shot}

After the restart, first-run setup asks for your region, keyboard, network and privacy choices;
then you sign in. Firefox is already installed.

<div class="grid" markdown="1">
![First-run setup: privacy choices](img/oobe-privacy.png){: .shot}
![The lock screen](img/lock.png){: .shot}
</div>

Black screen, NVIDIA, dual boot, Secure Boot? See the [FAQ](faq.html).

## Community {#community}

Where to ask, where to report, and where to follow along:

<div class="grid" markdown="1">
<div class="card" markdown="1">

### Questions and ideas

[GitHub Discussions](https://github.com/Stained-Glass-OS/stained-glass/discussions): ask a
question, suggest an idea, vote in polls, or show what you got running. A free GitHub account is
all you need.

</div>
<div class="card" markdown="1">

### Bugs

[GitHub Issues](https://github.com/Stained-Glass-OS/stained-glass/issues) for anything that does not
work. **Report a problem** (in Start, or right-click a program's taskbar button) gathers the
details and logs for you. [How to report well](faq.html#help).

</div>
<div class="card" markdown="1">

### Videos

Updates and walkthroughs on the [YouTube channel](https://www.youtube.com/channel/UCIVaIdjtr6aNPdTm-JNbFAg).
Tell us in the comments what to test next. All of them, with transcripts:
[Videos](videos.html).

</div>
</div>

## Package repository

Installed systems update from our signed apt repository at
[freesoft.page/apt](apt/). To add it to a Debian 13 (trixie) machine by hand:

```
curl -fsSL https://freesoft.page/apt/stained-glass-archive-keyring.gpg \
  | sudo tee /usr/share/keyrings/stained-glass-archive-keyring.gpg >/dev/null
sudo tee /etc/apt/sources.list.d/stained-glass.sources <<EOF
Types: deb
URIs: https://freesoft.page/apt
Suites: trixie
Components: main
Signed-By: /usr/share/keyrings/stained-glass-archive-keyring.gpg
EOF
sudo apt update
```

## Status

Stained Glass OS is in active development and **not yet ready for everyday use**. The
[FAQ](faq.html) answers the common questions; the [guide](docs/index.html) covers getting started, everyday use, programs, administration and
[how it all fits together](docs/guide/05-how-it-works.html).

## Source

Every piece is on GitHub under [Stained-Glass-OS](https://github.com/Stained-Glass-OS):
`wine-sg` (Wine and our patches), `sg-shell` (Start menu, Control Panel, Settings, apps),
`sg-session` (sessions, sign-in, installer, system services), `sg-compositor` (the display
server), `sg-image` (the image, ISO and test gates) and `stained-glass` (docs and decisions).
