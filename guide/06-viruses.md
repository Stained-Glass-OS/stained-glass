# How viruses are handled

Stained Glass protects you in three layers, matched to where software
comes from.

## Where software comes from

| Where it comes from | How it is trusted |
|---|---|
| **The SG Store**, Windows apps | Each installer is downloaded from its maker's own site and checked against a fingerprint (its SHA-256) recorded when the app was added to the Store. A file that differs by one byte -- tampered with, or swapped on the way -- is refused before it runs. |
| **The SG Store**, Linux apps, and system updates | They come from Debian's and the project's package repositories. Every package list is signed, and `apt` refuses anything whose signature or checksum does not match. |
| **Everything else** -- downloads from the web, saved mail attachments, programs copied from a USB stick | Scanned by **SG Defender** before you run them (below). |

Known-good software is therefore checked by what it *is*, not by guessing,
and the scanner only has to look at what arrives from elsewhere.

## SG Defender

SG Defender is the **ClamAV** open-source antivirus engine, built in and on
by default. Stained Glass runs Windows programs, so Windows malware can run
here too; SG Defender works the way Windows' own antivirus does:

- **Real-time protection.** Every Windows program, DLL and installer package
  is scanned before it starts, and so are batch files and scripts (cmd,
  wscript, cscript) before they run. PowerShell and other programs that use
  the antimalware scan interface (AMSI) have their script text scanned too.
  A program that holds malware is not started: the program that tried gets
  the error "Operation did not complete successfully because the file
  contains a virus or potentially unwanted software", the file goes to
  quarantine, and you are told. A program that was already checked and has
  not changed starts at once; new definitions check it again.
- **Downloads.** Every person's **Downloads**, **Desktop** and
  **Applications** (where AppImages are installed) folders are watched. A
  program, installer, script, archive or macro-capable document is scanned
  when it finishes arriving there.
- **Scans.** A quick scan runs every day: the programs set to start
  automatically (Run and RunOnce keys, Startup folders, scheduled tasks, services),
  the system folders, Program Files, Downloads, the Desktop and temporary
  files. You can start a **Quick scan**, a **Full scan** (all your files and
  drive C:) or a **Custom scan** (one folder) in Settings, or from a terminal
  with `sg-defender-scan quick|full|custom FOLDER`. Scans run in the
  background, at low priority.
- If something is found, the file is moved to a **quarantine** that only an
  administrator can reach, so it cannot be run by accident, and you are told
  what was found and where.
- Virus definitions update on their own, several times a day.

**Settings > Update & Security > Virus & threat protection** shows whether it
is on, the scans and their results, **Protection history** (what was found in
your files), the definitions in use, and the settings below.

### Your files stay yours

SG Defender runs as the system, but it reads for you only what you could
read yourself: a program asks about a file by handing over the file it has
open, never by naming a path for the system to open. Your scans run with
your own rights, and what they find is shown to you alone. The system's own
folders are scanned with the system account's rights.

## Turning it off

**Real-time protection** can be turned off by an administrator for a while,
for example to install something SG Defender wrongly stops. It comes back on
by itself within four hours, or at the next restart. Scheduled scans still
run.

**SG Defender** itself can be turned off by an administrator, for example on a
machine with little memory. That stops ClamAV and gives its memory back
(about a gigabyte). Store apps and packages are still checked as above.

**Exclusions** (an administrator's): folders and files SG Defender does not
scan, at start or in a scan. Only administrators can see them. Add only what
you trust.

From a terminal: `/etc/stained-glass/defender.conf` holds `enabled=1` or
`enabled=0`, `/etc/stained-glass/defender-exclusions` the exclusions, and
`journalctl -u sg-defender` shows what it scanned and found.

## If something was quarantined

A notice pops up above the tray: which file, in which folder, and what
was found. **Review** opens **Settings > Virus & threat protection**, which
lists everything quarantined from your files, each with two buttons:

- **Delete** removes it for good.
- **Restore** puts it back where it was, after a warning. Use it only for a
  file you know is safe, such as a false alarm in a tool you trust. The
  restored file is not stopped again (SG Defender remembers that exact file
  by its fingerprint, so a changed copy is still checked).

Both need an administrator. Quarantined files are kept in
`/var/lib/stained-glass/defender/quarantine/`, which only root can open.

## What else protects you

- **Separate accounts.** Each person's files belong to them. A program you run
  cannot change the system or other people's files without an administrator's
  approval.
- **Administrator prompts** come from the compositor, which no program can
  fake or click through.
- **Updates** arrive from the signed repositories every day and install at the
  next restart.
