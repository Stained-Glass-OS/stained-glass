# Programs

Stained Glass runs two kinds of programs side by side: Windows programs, on
its Windows layer, and Linux programs, directly. Both show up in Start, on the
taskbar and in Task Manager, and both open your files.

## The SG Store

**SG Store** (in Start) installs both kinds.

- A card's **Install** installs that app. Apps made for both systems are one
  card with a choice of build.
- Check the box on several cards and press **Install selected**: they install
  one after another, and an administrator is asked only once for all of them.
- **Install from a file** takes a downloaded Windows installer or a Linux
  `.deb` package.

Windows programs come from their makers' own downloads, checked against a
known fingerprint before they run; the project never redistributes them.

## Windows programs

Download an installer and open it, as on Windows. Installers that need an
administrator ask for one (see below). Most programs install for everyone,
under `C:\Program Files`; some install only for you.

- **Right-click a program > Properties > Compatibility** holds per-program
  settings for programs that need a nudge.
- **Run with debugging** (right-click in Start) records what a developer
  needs when a program misbehaves, ready to send with **Report a problem**.

## Administrator prompts

When a program needs an administrator, a prompt asks for permission (an
administrator's account) or for an administrator's password (anyone else). The
program then runs as the machine's administrator account, separated from your
other programs: nothing you run unprivileged can type into it or read it.
Its windows still appear on your taskbar, and its tray icons in your tray.

## Linux programs

Linux programs install from the SG Store's Linux section or with `apt`. They
open in frames like every other window, take part in Alt+Tab and Task View,
and can be set as default apps (**Settings > Apps > Default apps**) -- Firefox
as the web browser, for example.

## Starting programs at sign-in

**Task Manager > Startup** lists what starts when you sign in, and turns items
on and off. Items installed for everyone need an administrator to change; you
are asked. Right-click a program in Start for **Start at sign-in** to add one.
