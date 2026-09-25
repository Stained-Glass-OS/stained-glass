# What's left (as of 2026-09-25)

A snapshot taken when the first test ISO was built (`sg-image: make iso`),
so work can pick up here. Each repo's `CLAUDE.md` has the detail and the
next steps for its items. The long-range wish-list is `vision-backlog.md`;
the app inventory is `default-apps.md`.

## Done in this round (2026-09-24/25)

- Shell polish: fonts (ClearType wins over fontconfig), scroll bars, purple
  theme, virtual desktops + Task View, snap, Win-key shortcuts, wallpaper,
  desktop icons, Start menu.
- Control Panel, networking (Wi-Fi, static/DHCP, netsh/ipconfig), installer
  with partitioner and live "Try", NVIDIA/non-free drivers, CI green.
- Voice typing (Win+H, Parakeet, model baked into the image).
- Notepad: our own Kate-class editor as `notepad.exe` (wine-sg 0100-0101).
- File Explorer: command bar, breadcrumb, search, nav pane, This PC,
  progress and conflict dialogs (wine-sg 0110-0112).
- Apps: Calculator, Paint, Snipping Tool, Photos, Media Player, Task Manager,
  Sticky Notes, Character Map, Zip folders, Settings (Win+I, ms-settings:),
  Windows Terminal (wt.exe, pseudo consoles), Alarms & Clock.
- Admin tools: Services, Event Viewer (real event log), Device Manager,
  Disk Management, Computer Management, System Information, Disk Cleanup,
  Resource Monitor; SCM access checks; pipe impersonation.
- Compatibility: Git for Windows' terminal works (0081-0083); CJK fonts.
- A bootable hybrid ISO (DVD / VM CD drive / USB stick), installs from it.

## Open, by area

### App compatibility
- **Firefox never finishes shutting down** -- an upstream Wine bug (stock
  Debian Wine hangs the same way): a synchronous IPC to the GPU process is
  never woken. Next: a small overlapped-pipe + IOCP + cross-thread
  PostMessage probe (wine-sg CLAUDE.md, "Firefox").
- Emoji and other characters beyond the BMP draw as boxes (Wine GDI).
- `SystemTimeToTzSpecificLocalTimeEx` is a stub.

### File Explorer
- Round 2 landed (wine-sg 0150-0157, sg-session 0.1.0-28, sg-shell
  0.1.0-41): thumbnails, icon sizes, Tiles/Content, Group by (comctl32 list
  view groups and tiles), Quick access, details/preview panes, drops on the
  navigation pane, type names, Send to. Left: video/PDF thumbnails, a disk
  thumbnail cache, image dimensions in the details pane, removing frequent
  folders from Quick access, reordering pins.

### Notepad
- Done 2026-09-25 (wine-sg 10.0-51): the menu bar follows the dark theme
  (0100 + 0188), Page Setup's Header/Footer boxes with &l/&c/&r (printed
  pages checked as EMF). Left: popup menus stay light unless the system
  scheme is dark; printing to a real printer untested; new strings English
  only.

### Settings / shell
- Taskbar and Start honour Settings: done (wine-sg 10.0-54 0164, sg-shell
  0.1.0-42) -- edge, auto-hide, small buttons, combining, centring, search,
  Task View; Start's most used, suggestions, app list, more tiles, full
  screen, placement by the taskbar's edge. Not yet: dragging/resizing the
  bar, jump lists, badges, peek, per-monitor bars.
- Lock screen picture: done (sg-session 0.1.0-23, sg-shell 0.1.0-34) --
  the chosen picture with the clock, lifted to a blurred sign-in pane. Not
  yet: the curtain coming back after a minute idle, Spotlight, and
  publishing a picture chosen before this existed.
- Screen off on idle and Sleep/Hibernate in Start: done (sg-compositor
  0.2.0+sg5, sg-session 0.1.0-22, sg-shell 0.1.0-31). Windows programs
  cannot yet keep the screen on (`SetThreadExecutionState` does not reach
  the compositor); not yet tested on real hardware/VM suspend.
- Terminal: split panes and search done (sg-shell 0.1.0-32). Left: a
  settings.json of its own, user profiles, tabs in the title bar, bracketed
  paste, mouse reporting, dragging the divider with the mouse.
- Dark mode: done (wine-sg 10.0-54 0160-0163, sg-shell 0.1.0-42/-43) --
  a generated Dark scheme of our msstyles switched live for every program,
  dark title bars (DWMWA_USE_IMMERSIVE_DARK_MODE), the taskbar/Start/flyout
  by the Windows mode, Settings and ten of our apps by the app mode. Not
  yet: Terminal/WordPad/Magnifier/OSK/voice bar palettes; programs that
  hard-code black text on COLOR_WINDOW backgrounds stay unreadable in dark
  (as on Windows with system colours forced).
- OOBE (first-run setup): see sg-session.

### Admin tools
- Done 2026-09-25 (wine-sg 10.0-45, sg-session 0.1.0-26, sg-shell 0.1.0-39):
  partitioning (new/delete/extend/shrink), SMART, device disable/enable,
  per-service security, lusrmgr/fsmgmt.msc, Security log (logon, logoff,
  elevation) with 0700/0600 files, msinfo32 /report.
- Left: failed passwords at the login screen are not logged (pam_exec runs
  only on success); no FAT/exFAT resize; device disable covers PCI and USB
  only; the Services Security tab is read-only (use `sc sdset`); SMART
  untested against real smartctl output.

### Missing apps (ranked)
1. ~~A web browser and PDF viewer out of the box~~ -- done (PDF Viewer on
   poppler, sg-shell 0.1.0-33 / sg-session 0.1.0-25; Get a web browser,
   sg-shell 0.1.0-38; WebView2 apps draw, wine-sg 10.0-52). Still open:
   Wine's HKCR does not merge the user's `Software\Classes` (Default apps
   choices for file types, and per-user installs' ProgIDs and protocol
   handlers, are not seen; a wine-sg fix).
2. Done 2026-09-25: WordPad (sg-shell 0.1.0-40, wine-sg 0180/0184 --
   ribbon, ruler, RTF/.docx/.odt/text, pictures, printing and preview
   through RichEdit's new EM_FORMATRANGE); Magnifier and On-Screen Keyboard
   (sg-shell 0.1.0-35, wine-sg 0181-0182, 10.0-47); font viewer and the
   Fonts folder (sg-shell 0.1.0-37, wine-sg 0183, 10.0-49). Left: WordPad
   tables and OLE objects, .doc; Magnifier lens resizing and GL/Vulkan
   windows in lens/full screen; OSK non-US labels; hiding fonts by
   language.

### Voice typing
- Done 2026-09-25 (sg-session 0.1.0-27, sg-shell 0.1.0-36): partial text
  in the bar while speaking, final text typed at the pause; spoken
  punctuation, filler words and commands (delete/undo that, stop listening)
  in English, German, French and Spanish, or detected per utterance; the
  model as a package (sg-session 0.1.0-21). Left: a live microphone test in
  a VM.

### Platform
- Domain: real domain SID in Wine; machine GPOs from the domain.
- MSIX deployment (Store apps) in progress in wine-sg.
- winex11 BadWindow under Xvfb; desktop surface flush clipping.
- Out of scope (David, 2026-09-25): a signed boot chain (Secure Boot) and
  legacy BIOS boot. UEFI, unsigned, is the target.
- The apt site cannot carry files over 100 MB (GitHub), so the speech model
  ships only in the image/ISO.
