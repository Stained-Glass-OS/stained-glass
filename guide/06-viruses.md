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
by default.

- It watches every person's **Downloads** and **Desktop** folders. When a
  program, installer, script, archive or macro-capable document finishes
  arriving there, it is scanned. A browser's half-finished download is
  scanned once it is complete.
- If something is found, the file is moved to a **quarantine** that only an
  administrator can reach, so it cannot be run by accident, and you are told
  what was found and where.
- Virus definitions update on their own, several times a day.
- Ordinary files (photos, music, text) and the programs you run every day
  are not scanned again, so it does not slow the machine down. ClamAV keeps
  its definitions in memory, which costs about a gigabyte of RAM.

**Settings > Update & Security > Virus & threat protection** shows whether it
is on, how many files it has checked, the definitions in use, and what it
has quarantined from your files.

## Turning it off

An administrator can turn SG Defender off on that page, for example on a
machine with little memory. That stops ClamAV and gives its memory back.
Store apps and packages are still checked as above; only downloads go
unscanned. Turn it back on the same way.

From a terminal: `/etc/stained-glass/defender.conf` holds `enabled=1` or
`enabled=0`, and `journalctl -u sg-defender` shows what it scanned and found.

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
