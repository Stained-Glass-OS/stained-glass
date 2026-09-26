# What's left (as of 2026-09-26)

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

## Done 2026-09-26

- Compatibility tab: right-click a program (or its shortcut) > Properties >
  Compatibility -- run as if on an older version, as administrator, in a
  window of its own, DXVK or WineD3D, environment variables and launch
  arguments (the tweaks ProtonDB reports suggest), recommended settings per
  program. Applied however the program starts, Steam included (wine-sg 0420,
  10.0-81; sg-shell 0.1.0-53). Open: the recommended-settings list itself.
- Elevated programs get a display of their own (B56); printing works for
  users; domain identity and machine GPO startup scripts.
- Communication round landed: Zoom's and Teams' start-up failures
  (0425-0426), Thunderbird's GetCurrentApplicationUserModelId (0423),
  downloads no longer leave `file:Zone.Identifier` files (0422), ucrtbase
  intmax functions (0421), IDXGIKeyedMutex on WineD3D (0424); msvcp140's
  mutex/condition-variable layout for programs built with Visual Studio
  2022 17.10+ (0428, from the games round; upstream Wine's fix backported).
- Direct2D geometries answer area/length/containment/outline, arcs are arcs,
  and command lists have real bounds (0427). Paint.NET 5 still hangs
  (busy, ~half a core) at the first paintbrush drag: not the bounds alone.
- The ISO boots from a Ventoy stick as well as dd/DVD; the live boot no
  longer hangs on the splash; the server keeps only the newest ISO.

## Open, by area

### App compatibility
- Firefox shutdown, emoji in GDI text and the dynamic time zone APIs are
  done (wine-sg 0170-0173, 10.0-57); the compat suite's first 24
  applications all launch.
- Round 2 (wine-sg 0235-0239): Chrome, Edge, Slack, Node.js, Java and two
  DXVK games work (Chrome needed a COM service fix, typelib [string]
  marshalling and key DACLs; Node.js an internet-shortcut fix). Open:
  Discord (updater loops), Spotify and Zoom (crash at start), Teams
  (`LimitedAccessFeatures`, then WebView2), Acrobat Reader (installer exits
  67), Microsoft 365 (Click-to-Run hangs), VS Build Tools (bootstrapper
  crashes). See default-apps.md.
- Developer tools (wine-sg 0320-0324, 10.0-74): .NET SDK, Go, CMake, Rust,
  pip/npm native packages, Git + Credential Manager, VS Code's terminal
  work. Open: VS Build Tools (Wine Mono's X509Chain: needs AIA fetch and
  CRLs in a Wine Mono build), PowerShell for VS Code's default terminal;
  not yet run: GitHub Desktop, Postman, Insomnia, MSYS2, JetBrains IDEs,
  Android Studio.
- Paint.NET 5 starts (wine-sg 0223-0234: Direct2D effects and command
  lists drawn, a first Windows.UI.Composition -- compositor, visuals,
  brushes, drawing surfaces, desktop window targets). Its main window, tool
  and history/layers panels and canvas come up, but it is not usable yet:
  the canvas shows the transparency checkerboard instead of the image, the
  colour swatches and wheel are not drawn, Direct2D layers are a stub.
- Communication round (wine-sg 0380-0399, stopped early for usage): root
  causes found -- Zoom crashes on the `SetThreadpoolTimerEx` stub, Teams
  exits on missing `Windows.ApplicationModel.LimitedAccessFeatures` (fixes
  drafted, not gated); Skype is discontinued. Discord, Spotify, Telegram,
  Signal, Thunderbird mail flows and browser daily use (video, downloads,
  printing, pickers, notifications) are mid-investigation; the Zoom, Teams
  and Thunderbird fixes landed 2026-09-26 (above) -- each app to be re-run.
- Creative/media round (wine-sg 0340-0342, 10.0-77): Direct2D layers,
  blend/composite modes and effect-graph fixes -- Paint.NET 5's canvas,
  colour wheel and swatches now draw; a paintbrush drag still hangs it
  (command-list bounds are unbounded; WIP noted in wine-sg CLAUDE.md).
  Survey on the dev build: Blender 4.2, Audacity, foobar2000 work; GIMP
  2.10/3.0, Krita, Inkscape, OBS, VLC, HandBrake partly. Causes found, not
  yet fixed: `C:\windows\Fonts` is empty (Krita crash, Inkscape text, VLC
  subtitles); the host's `XDG_DATA_DIRS` leaks into programs (GIMP 3
  aborts); no `kbdus.dll`/keyboard-layout keys (GTK Ctrl shortcuts); OBS
  needs `icuuc.dll` and `D3DKMTSetProcessSchedulingPriorityClass`; VLC's
  DXVA2/D3D11VA decoding and NV12 output; WPF text shaping FailFast
  (HandBrake GUI). Not yet tried: Shotcut, Kdenlive, IrfanView, XnView MP,
  darktable, RawTherapee, MusicBee, Resolve, Affinity, Clip Studio.
- GTK 4 programs (Pinta) draw text misshapen (glyph parts missing).
- Colour emoji: GDI draws them in one colour (as on Windows); DirectWrite
  colour glyphs not checked. No CJK Extension B font in the image.
- Setting the time zone from Windows programs (`SetDynamicTimeZoneInformation`
  through sg-admind) is not wired.

### File Explorer
- Round 2 landed (wine-sg 0150-0157, sg-session 0.1.0-28, sg-shell
  0.1.0-41): thumbnails, icon sizes, Tiles/Content, Group by (comctl32 list
  view groups and tiles), Quick access, details/preview panes, drops on the
  navigation pane, type names, Send to. Round 3 (wine-sg 0244-0246,
  10.0-59; sg-session 0.1.0-30): video and PDF thumbnails, an on-disk
  thumbnail cache, picture dimensions and video length in the details pane,
  "Remove from Quick access", pins reordered by dragging. Left: editable
  properties, reordering pins on the Quick access page itself, a film-strip
  overlay, Office/audio-art thumbnails.

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
- Terminal: split panes and search done (sg-shell 0.1.0-32); settings.json
  as Windows Terminal keeps it, user profiles and dragging pane dividers
  (sg-shell 0.1.0-45). Left: tabs in the title bar, bracketed paste, mouse
  reporting.
- Dark mode: done (wine-sg 10.0-54 0160-0163, sg-shell 0.1.0-42/-43) --
  a generated Dark scheme of our msstyles switched live for every program,
  dark title bars (DWMWA_USE_IMMERSIVE_DARK_MODE), the taskbar/Start/flyout
  by the Windows mode, Settings and ten of our apps by the app mode. Not
  yet: Terminal/WordPad/Magnifier/OSK/voice bar palettes; programs that
  hard-code black text on COLOR_WINDOW backgrounds stay unreadable in dark
  (as on Windows with system colours forced).
- OOBE (first-run setup) landed (sg-session 0.1.0-24..29). Open: the region only sets the format and country (the display language is English only); locales are not generated on the Linux side; installing a browser is Firefox or Firefox ESR, from Mozilla or through a user-installed winget; no Wi-Fi in the VM gate.

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
   Fonts folder (sg-shell 0.1.0-37, wine-sg 0183, 10.0-49). WordPad tables
   (RTF/.docx/.odt, Insert > Table; wine-sg 0240, 10.0-60), page numbers,
   header and footer in print, and reading Word 97-2003 .doc with our own
   reader (sg-shell 0.1.0-47). On-Screen Keyboard labels follow the keyboard
   layout (sg-shell 0.1.0-46, wine-sg 0250-0251, 10.0-58). Left: WordPad
   OLE objects, writing .doc, merged/nested tables; Magnifier lens resizing
   and GL/Vulkan windows in lens/full screen; OSK dead keys composing and a
   Windows-side layout switch; hiding fonts by language.

### Voice typing
- Done 2026-09-25 (sg-session 0.1.0-27, sg-shell 0.1.0-36): partial text
  in the bar while speaking, final text typed at the pause; spoken
  punctuation, filler words and commands (delete/undo that, stop listening)
  in English, German, French and Spanish, or detected per utterance; the
  model as a package (sg-session 0.1.0-21). Left: a live microphone test in
  a VM.

### Platform
- MSIX deployment (Store apps) in progress in wine-sg.
- winex11 BadWindow under Xvfb; desktop surface flush clipping.
- Out of scope (David, 2026-09-25): a signed boot chain (Secure Boot) and
  legacy BIOS boot. UEFI, unsigned, is the target.
- apt and ISOs are on https://freesoft.page (apt/, iso/); the speech model
  ships as a package there too.
