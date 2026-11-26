# Frequently asked questions

The questions people ask most, answered from how the system actually works today. Something
missing? Ask in [Discussions](https://github.com/Stained-Glass-OS/stained-glass/discussions).

<div class="notice" markdown="1">

**Early development.** Stained Glass OS is not yet ready for everyday use. Try it in a virtual
machine or the live session first.

</div>

**Trying it:** [Live login and password](#live-login) &middot; [sudo on the live system](#live-sudo) &middot;
[Hardware](#hardware) &middot; [Secure Boot](#secure-boot) &middot; [Legacy BIOS](#legacy-bios) &middot;
[Black screen](#black-screen) &middot; [NVIDIA drivers](#nvidia) &middot; [Dual boot](#dual-boot) &middot;
[I already run Debian](#existing-debian)<br>
**What it is:** [Is it Windows?](#is-it-windows) &middot; [Microsoft code](#microsoft-code) &middot;
[Free and open source](#license) &middot; [Is it vibe coded?](#vibe-coded) &middot; [Privacy](#privacy)<br>
**Using it:** [Which programs run](#programs) &middot; [Games and anti-cheat](#games) &middot;
[Updates](#updates) &middot; [SG Defender](#defender)<br>
**Help:** [Report a bug or ask a question](#help)

## Trying it

### What is the live session's login and password? {#live-login}

The live system signs in by itself when you choose **Try Stained Glass OS**. If you are ever asked,
the account is **`live`** and it has **no password**: leave the password empty and press Enter. That
works on the sign-in screen and on a text console (**Ctrl+Alt+F2**) too.

The `live` account exists only for that boot. It is made fresh each time the stick starts, and it is
never copied onto a computer you install to: Setup asks you to create your own account.

### How do I use sudo on the live system? {#live-sudo}

The `live` account is an administrator (it is in the `sg-admins` group), so `sudo` works. When sudo
asks for a password, just press Enter: the password is empty. Anything you change on the live system
is gone when you restart.

### What hardware do I need? {#hardware}

- A 64-bit PC (x86-64, the kind Windows 10 runs on). UEFI and older legacy BIOS PCs both work.
- 4 GB of memory or more; 8 GB is comfortable. SG Defender's virus definitions alone take about 1 GB.
- At least 11 GB of disk for the system (Setup refuses less); 40 GB or more is sensible once you
  install programs.
- A USB stick of 4 GB or more (the ISO is about 3.3 GB), or a virtual machine with the ISO in its
  CD drive.
- Any graphics card. Intel and AMD work out of the box. NVIDIA works best with NVIDIA's own driver
  ([below](#nvidia)). With no working graphics driver at all, the system still starts and draws in
  software (the "Basic Display Adapter"), just more slowly.

### Do I need to turn off Secure Boot? {#secure-boot}

Yes. Stained Glass OS is not signed for Secure Boot, so a PC with Secure Boot on will refuse to start
the stick. Turn Secure Boot off in the firmware settings (often F2, F10, Del or Esc at power-on),
under a Security or Boot tab. Windows on the same PC keeps working with Secure Boot off.

### Does it work on an older PC with legacy BIOS? {#legacy-bios}

Yes, since mid-November 2026. The ISO starts on legacy BIOS (and on UEFI with the Compatibility
Support Module), whether it is written to a USB stick or burned to a DVD, and Setup installs a system
that a BIOS starts with GRUB. Beside Windows on a BIOS PC's MBR disk, Setup uses unallocated space,
leaves Windows' partitions alone, and puts Windows in the boot menu. Each of these is checked by an
automatic test on every ISO before it is published. If you used an ISO from before that and it would
not start, download the current one.

### The screen stays black, or the sign-in screen never appears. What now? {#black-screen}

Current ISOs handle the common causes on their own: when no graphics driver can run, the system draws
in software instead (Basic Display Adapter), and on NVIDIA laptops whose open driver cannot start, it
no longer loads that driver and blanks the screen. If it still fails:

1. **Wait a minute.** When the sign-in screen cannot start, Stained Glass shows a text screen on the
   first console that says what failed and which graphics hardware it found.
2. On that screen, press **S** to **save a boot report**. It is written to the boot stick when it can
   be (on a Ventoy stick, next to the `.iso` file), or else to any FAT, exFAT or NTFS USB stick you
   plug in. The screen shows where it went. **U** sends a summary to the project's server instead,
   after showing you exactly what would be sent and asking you first. **R** tries the sign-in screen
   again.
3. If there is no text screen either, press **Ctrl+Alt+F2** for a text console, sign in as `live`
   with an empty password, and run `sudo sg-boot-report save`.
4. **Send it:** open an [issue on GitHub](https://github.com/Stained-Glass-OS/stained-glass/issues)
   with your PC's model and graphics card, and attach the saved `.tar.gz` (or give the report's
   number if you used **U**). Reports sent with **U** are public at [/reports/](reports/), with
   account and computer names replaced.

If the stick itself is not found while starting, a screen says what was looked for, and **S** saves a
report there too.

### How do I install NVIDIA's driver? {#nvidia}

Setup's **Install third-party drivers for graphics and Wi-Fi (recommended)** box is ticked by
default. With it, the first start of the installed system installs what the PC needs. For an NVIDIA
card from the RTX 20 / GTX 16 series (Turing) onwards, that is NVIDIA's own current driver
(`nvidia-open`), from NVIDIA's Debian 13 repository. The driver Debian ships is too old for the
desktop to draw cleanly, so the newer one is needed; NVIDIA's repository is added on such PCs only and
is limited to NVIDIA's driver packages. Older cards get the right Debian driver, or keep the open
`nouveau` driver if no current driver supports them.

If you unticked the box, or added a card later, an administrator can run:

```
sudo sg-drivers --install-recommended
```

and restart. `sudo sg-drivers --list` shows what it would install, device by device. **Device
Manager** also marks devices that have no driver.

### Can I install it beside Windows (dual boot)? {#dual-boot}

Yes. Setup's **Custom** install shows each disk's partitions and unallocated space, like Windows
Setup. Make room first: in Windows, shrink a partition in **Disk Management** so that there is
unallocated space (Setup does not shrink Windows for you). Then pick that space in Setup. Windows'
partitions and boot loader are left as they are, and the boot menu shows both systems for five
seconds at each start. If BitLocker is on, have the recovery key ready before changing partitions,
as you would for any change to the disk.

As always with partitions: back up first.

### I already run Debian 13. Do I have to reinstall? {#existing-debian}

No. Add the [package repository](index.html#package-repository) and install one package:

```
sudo apt install stained-glass-desktop
```

then restart. Your files stay where they are and your Linux apps appear in Start. To go back,
`sudo apt purge stained-glass-desktop` restores your previous login screen; `sudo apt autoremove`
then removes the rest.

## What it is

### Is this Windows? Is it made by Microsoft? {#is-it-windows}

No. Stained Glass OS is an independent, free and open-source operating system built on Debian Linux.
It looks and works like Windows 10 and runs Windows programs, but it is not a Microsoft product and
is not affiliated with, endorsed by or sponsored by Microsoft in any way. Windows is a trademark of
Microsoft Corporation.

### Does it contain Microsoft code? {#microsoft-code}

No. No Microsoft code or artwork is included, and the project never disassembles or decompiles
Microsoft's programs. Compatibility comes from Wine, which re-implements the documented Windows
programming interfaces, plus the project's own patches to it, and a shell and apps written from
scratch. Testing against real Windows from the outside is how behaviour gets matched.

Microsoft programs you install yourself (Office, Edge, OneDrive, the .NET runtimes) bring their own
files, under their own licences, exactly as on a Windows PC. The project does not redistribute them.

### Is it free and open source? {#license}

Yes, and free of charge. The project's own code is under the **AGPL-3.0-or-later**; Wine, Debian and
the other parts keep their own open-source licences. Everything is on
[GitHub](https://github.com/Stained-Glass-OS). There is no paid edition and no account to make.

### Is it vibe coded? {#vibe-coded}

AI agents, mostly Claude, write most of the code. That is stated openly: the project's working notes
are published as the [AI architectural notes](docs/ai-notes.html). David designed the architecture
(how Debian, Wine, the compositor and the shell fit together) and makes the decisions that matter.

What keeps it honest is the rule that nothing counts as working until a test says so: every fix comes
with an automatic test that fails without it, and releases go out only after the test gates pass,
including installing the ISO in virtual machines. Clean-room rules apply to the agents as to anyone:
no leaked Microsoft source, no disassembling Microsoft binaries.

Because [Wine does not accept LLM-generated code](docs/decisions/0006-wine-llm-contribution-policy.html),
the project does not send its Wine patches upstream. They stay in its own Wine build, `wine-sg`,
which is published with its source.

### What does it collect about me? {#privacy}

Nothing on its own. The system sends no diagnostics or usage data. The one automatic request is the
time zone lookup, and only while **Set time zone automatically** is on (or the zone is still UTC).
Updates come from apt like on any Debian system.

The project's server keeps no access logs for the website, the package repository or its API, and
the site sets no cookies and has no analytics or tracking scripts. The video players on the front
page and the [Videos](videos.html) page are YouTube's, embedded in its privacy-enhanced
(youtube-nocookie.com) mode. ISO downloads are added up into a daily count
and the log is emptied every hour. A problem report you choose to send is kept with your address,
for abuse limits, and published without it. The full statement is
[server/PRIVACY.md](https://github.com/Stained-Glass-OS/sg-image/blob/main/server/PRIVACY.md).

## Using it

### Which Windows programs run? {#programs}

Many everyday Windows programs install from their own installers and run: 32- and 64-bit Win32
programs (Notepad++, 7-Zip, PuTTY), .NET Framework programs (WinForms and WPF, on the project's own
Wine Mono build) and newer .NET apps, Chromium-based browsers, Microsoft Office with OneDrive, and
installers of every common kind (MSI, NSIS, Inno Setup, winget). The **SG Store** lists hundreds of
Windows and Linux apps that have been installed and tried.

What cannot work is anything that has to run inside the Windows kernel: hardware drivers, some VPNs
and kernel anti-cheat. Wine runs programs, not Windows kernel drivers. Where a program has a good
Linux version, the Linux version is usually the better choice; fall back to the Windows one where you
need it.

If a program does not work, please [report it](#help): that is how the list grows.

### What about games and anti-cheat? {#games}

Games are good. DirectX is translated to Vulkan by DXVK and VKD3D-Proton, the same pieces Steam's
Proton uses, so Windows games run outside Steam too. For Steam itself, the **Linux version of
Steam** (in the SG Store) is the recommendation: you get all of its Proton versions, and native
Linux games run directly. GOG GALAXY installs as well.

Online games with **kernel anti-cheat generally do not work**, and that is by design of the
anti-cheat, not a limit of the games. Some developers switch their anti-cheat on for Proton; those
games work through Linux Steam.

### How do updates work? {#updates}

Every part of the system is a Debian package in the project's signed repository. Updates download in
the background and install at the next restart, before anyone signs in, as Windows does;
**Settings > Update & Security** shows what is waiting and can install now. An administrator can
also run `sudo apt update && sudo apt full-upgrade` at any time.

Before every update, the system takes a **restore point** (a btrfs snapshot). If an update goes
wrong, start the system from the restore point in the boot menu, or go back from **Settings >
Update & Security > Recovery**. Systems installed on ext4 by older versions of Setup get "Undo the
last update" instead, and the Control Panel's Recovery page can convert them.

### Why does SG Defender exist? {#defender}

Because Stained Glass OS runs Windows programs, and that includes Windows malware. The usual Linux
answer, "Windows viruses can't run here", stops being true once Windows software runs well. SG
Defender (the ClamAV engine) is a first step at covering the moment that matters most for most
people: downloading an installer and running it. It scans programs, installers, scripts, archives
and macro documents as they land in Downloads, Desktop and Applications.

ClamAV should not be the only line of defence, and scanning only those folders is narrow. The aim is
what Windows Defender does: scanning a program when it starts, scheduled quick scans of the places
malware hides, and a smaller memory footprint. Beside that, the permission model limits what a
malicious program can do: standard users cannot write the machine's registry or system folders, and
changes that need an administrator ask first. An administrator can turn SG Defender off in
**Settings > Update & Security > Virus & threat protection** (it gives back about 1 GB of memory).
More in [How viruses are handled](docs/guide/06-viruses.html).

## Help {#getting-help}

### How do I report a bug, or ask a question? {#help}

- **Something does not work:** open an
  [issue on GitHub](https://github.com/Stained-Glass-OS/stained-glass/issues). Say what you did, what
  you expected and what happened, and your hardware if it is a start-up or display problem.
- **Report a problem**, in Start or on a program's taskbar button (right-click), collects what a
  developer needs: the program, its version, the machine and the relevant log. It shows you all of it
  first; **Send report** publishes it at [/reports/](reports/) without your account or computer name,
  and you can paste its link into the issue. For a program that misbehaves, right-click it in Start
  and choose **Run with debugging** first.
- **Questions, ideas and show-and-tell:** [GitHub Discussions](https://github.com/Stained-Glass-OS/stained-glass/discussions),
  with Q&amp;A, Ideas, Polls and Show and tell sections. You need a free GitHub account to post.
- **Security problems:** report them privately through
  [GitHub's security advisories](https://github.com/Stained-Glass-OS/stained-glass/security/advisories/new),
  not in a public issue.
