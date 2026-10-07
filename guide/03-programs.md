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

### AppImages

Some Linux programs are published as an **AppImage**: one file, such as
`Foo-x86_64.AppImage`, that holds the whole program. To install one you
downloaded:

1. Open it -- double-click it in File Explorer, or open it from your
   browser's downloads (right-click > **Install** works too).
2. The **Install an AppImage** window shows the program's name, version and
   the file it came from. Tick **Remove the downloaded file** if you do not
   want to keep a copy in Downloads, then press **Install**.

The AppImage is copied into the **Applications** folder in your home folder
(`~/Applications`, shown in File Explorer) and the program appears in Start
with your other Linux apps, with its own icon. It is installed for you only,
and needs no administrator. Installing it does not run it: like any download,
an AppImage is a program from whoever made it, so install only ones you
trust. SG Defender scans it in Downloads and again in Applications.

- **A newer version:** install the new file the same way. It replaces the old
  one -- Start keeps one entry.
- **Uninstall:** **Settings > Apps** (or right-click it in Start >
  **Uninstall**, which opens the list of programs), select it and press
  **Uninstall**. The file, its Start entry and its icon are removed; its
  settings in your home folder are kept.
- Older AppImages (the "type 1" format from before 2017) cannot be installed;
  the window says so. Ask the maker for a current AppImage.

## Starting programs at sign-in

**Settings > Apps > Startup** and **Task Manager > Startup** list what starts
when you sign in, and turn items on and off. Items installed for everyone need
an administrator to change; you are asked. To add a program -- any app in
Start, Windows or Linux, including ones from the SG Store -- either
right-click it in Start and choose **Start at sign-in**, or press **Add an
app** on the Startup page and pick it. Both put its shortcut in your Startup
folder (`shell:startup`), where you can also drop shortcuts yourself; the
Startup page's **Remove** takes one away again.

For a device that should run one app and nothing else, see
[A kiosk: a tablet that runs one app](04-administration.md#a-kiosk-a-tablet-that-runs-one-app).
