# Default apps: what a Stained Glass OS user can reach

Inventory taken 2026-09-25 against wine-sg 10.0-34/35 and sg-shell main. Each
Wine program was launched on a shell desktop (`explorer /desktop=shell`,
1024x768, the Stained Glass Light colours) under Xvfb, its windows listed and
the screen captured. The sg-shell programs are covered by their own gates
(`sg-shell/test/*-check.sh`), whose screenshots were reviewed.

"Start" means what sg-start lists. sg-start shows every `.lnk` in the user's
and the all-users Start Menu (Wine's wineboot creates **none**), plus a fixed
list in `build_list()` (`sg-shell/src/sg-start.c`) and its settings entries.

## Windows programs Wine gives us (wine-sg builtins)

| Program | Windows name it stands in for | Works? / quality | Start |
|---|---|---|---|
| `notepad.exe` | Notepad | Works; Wine's plain editor. **Being rebuilt** (Kate-class) by another worker. | yes |
| `wordpad.exe`, `write.exe` | WordPad | Hands off to sg-wordpad via App Paths (wine-sg 0180, 10.0-51); Wine's own runs without it. | -- |
| `regedit.exe` | Registry Editor | Works; classic look, close to Windows'. | no |
| `taskmgr.exe` | Task Manager | Works; NT4-era (Applications/Processes/Performance). Hands off to sg-taskmgr when App Paths names it (wine-sg 0121). | yes (as "Task Manager") |
| `cmd.exe` (in `wineconsole`/conhost) | Command Prompt | Works. | yes |
| `control.exe` | Control Panel | Hands off to sg-control (wine-sg 0072); Wine's own shows 4 applets. | yes (sg-control) |
| `appwiz.cpl` | Programs and Features (old) | Works (Wine dialog); sg-control's Programs and Features is the one we route to. | via Control Panel |
| `desk.cpl` | Display settings | Wine dialog: a virtual-desktop picture only. | via Control Panel |
| `inetcpl.cpl` | Internet Options | Works (Wine dialog). | via Control Panel |
| `joy.cpl` | Game Controllers | Works (Wine dialog). | via Control Panel |
| `winecfg.exe` | (none -- Wine's own) | Works. A Wine-branded tool; not something a Windows user expects. | no |
| `winemine.exe` | Minesweeper | Works; small, Wine-branded. | no |
| `clock.exe` | (Windows 3.x Clock) | Works; analog/digital face only -- no alarms, timers, world clock. | no |
| `oleview.exe` | OLE/COM Object Viewer (SDK tool) | Works. Developer tool. | no |
| `winefile.exe` | File Manager (Windows 3.x) | Works; Wine-branded, dated. | no |
| `progman.exe` | Program Manager | Works; empty. Historical. | no |
| `winhlp32.exe` | WinHelp (.hlp) | Opens an Open dialog; reads .hlp. | no |
| `hh.exe` | HTML Help (.chm) | Works on a .chm (Gecko); no window without one. | no |
| `iexplore.exe` | Internet Explorer | Opens ("Wine Internet Explorer", Gecko 2.47 engine). Not a modern browser. | no |
| `msinfo32.exe` | System Information | Stub: shows an "About" box only. | no |
| `dxdiag.exe` | DirectX Diagnostic Tool | No window (Wine's dxdiag only writes `/t` reports). | no |
| `winver.exe` | About Windows | "About Wine 10.0" box. | no |
| `uninstaller.exe` | Add/Remove Programs | Same as appwiz.cpl. | no |
| `wmplayer.exe` | Windows Media Player | Stub (prints a FIXME, no window). Hands off to sg-media via App Paths (wine-sg 0121). | -- |
| `explorer.exe <dir>` | File Explorer | Works; Wine's basic browser. **Being overhauled** by another worker. | yes |
| `view.exe` | (metafile viewer) | No window without a file. | no |
| Console tools: `ipconfig`, `netsh`, `ping`, `tasklist`, `taskkill`, `sc`, `reg`, `xcopy`, `robocopy`, `where`, `whoami`, `systeminfo`, `schtasks`, `certutil`, `wmic`, `msiexec`, `cscript`/`wscript`, `mshta`, ... | same | Work in cmd. | -- |

## Our programs (sg-shell)

| Program | Windows name | State | Start |
|---|---|---|---|
| sg-start | Start menu | Windows 10-class; gate `start-check.sh`. | -- |
| sg-control | Control Panel (`control.exe`) | Capable; applets listed in sg-shell CLAUDE.md. | yes |
| sg-ncpa | Network Connections (`ncpa.cpl`) | Works; gate `net-ui-check.sh`. | via Control Panel |
| sg-netflyout | Taskbar network flyout | Works. | tray |
| sg-mstsc | Remote Desktop Connection (`mstsc`) | Works (FreeRDP `sdl-freerdp3` underneath). | yes |
| sg-dictate | Voice typing (Win+H) | Works (Parakeet). | -- |
| sg-gpresult | `gpresult` | Console tool. | -- |
| sg-calc | Calculator (`calc.exe`, `calculator:`) | NEW 0.1.0-12: Standard/Scientific/Programmer, memory, history. Gate 46 checks. | yes |
| sg-paint | Paint (`mspaint.exe`) | NEW 0.1.0-15: ribbon, pencil/brushes/fill/text/eraser/picker/magnifier, 16 shapes, select/crop/resize/skew/rotate, undo, clipboard, WIC PNG/JPEG/BMP/GIF/TIFF. Gate 52. | yes |
| sg-snip | Snipping Tool (`snippingtool.exe`, Win+Shift+S, PrtScn, `ms-screenclip:`) | NEW 0.1.0-17: rectangle/free-form/window/full-screen clip to clipboard, toast, editor (pen, highlighter, crop, save). Gate 38. | yes |
| sg-photos | Photos (`photos.exe`, `ms-photos:`, 11 image types) | NEW 0.1.0-13: next/prev in name order, zoom/pan, rotate+save, slideshow, full screen, info, delete to Recycle Bin, GIF animation, EXIF orientation. Gate 30. | yes |
| sg-zip | Compressed (zipped) folders (`.zip`, Extract All, Compress to ZIP file) | NEW 0.1.0-10: own inflate/deflate, browse window, wizard, zip-slip refused. Gate 30. | -- (as Windows) |
| sg-taskmgr | Task Manager (`taskmgr.exe`, Ctrl+Shift+Esc) | NEW 0.1.0-14: fewer/more details, Processes, Performance, Startup, Users, Details, Services. Gate 30. | yes |
| sg-media | Media Player (`wmplayer.exe`, 17 audio/video types) | NEW 0.1.0-11: DirectShow via winegstreamer; needs the GStreamer plugin packages (sg-image). Gate 24. | yes |
| sg-sticky | Sticky Notes (`stikynot.exe`) | NEW 0.1.0-16: rich-text notes, colours, notes list + search, autosave/restore. Gate 28. | yes |
| sg-charmap | Character Map (`charmap.exe`) | NEW 0.1.0-18: font grid, magnifier, characters to copy, Advanced view search by U+ and name, Unicode names. Gate 20. | yes |

## Bundled applications (sg-image stages, sg-session installs)

| App | State | Start |
|---|---|---|
| PowerShell 7 (`pwsh.exe`, upstream MIT build) | Runs; on the machine PATH; gate `sg-apps-check`. | yes (`.lnk`) |
| Python 3.14 (python.org NuGet build) | Runs, pip, PEP 514; gate `sg-apps-check`. | yes (`.lnk`) |
| Wine Mono 9.4 / Wine Gecko 2.47 | .NET Framework programs; mshtml for iexplore/hh/mshta. | -- |
| Install Stained Glass OS (live boot only) | sg-setup. | yes (`.lnk`) |

## How the Windows names reach our programs

`CreateProcess("calc.exe")` searches system32 and PATH, **never App Paths**.
So wine-sg 10.0-35 adds `calc.exe`, `charmap.exe`, `mspaint.exe` and
`snippingtool.exe` to system32 and syswow64 as launchers that start what App
Paths registers for their own name (0120, 0124); Wine's own `taskmgr.exe` and
`wmplayer.exe` hand off the same way (0121, as `control.exe` does since
0072); explorer runs `snippingtool.exe /clip` on Win+Shift+S and Print Screen
(0122) and `taskmgr.exe` on Ctrl+Shift+Esc (0123); wineboot honours Task
Manager's Startup tab (0125). Gates: wine-sg `test/handoff-gate.sh` (22
checks), `test/startup-gate.sh` (9).

**Integration notes (main session):** sg-shell's `defaults/7x-*.reg` are
imported only when a prefix is first created -- existing prefixes need them
re-imported (sg-session: `sg-prefix-init` does not re-run defaults on an initialised prefix); the image needs the GStreamer plugin packages added to
`sg-image/mkosi.conf` (base, good, ugly, libav) for Media Player; wine-sg
10.0-35 + sg-shell 0.1.0-10..18 need publishing together (Build-Depends gained `unicode-data` for Character Map).

## Gap list against a stock Windows 10/11

| Windows app | Status |
|---|---|
| Calculator | **Done** (sg-calc) |
| Paint | **Done** (sg-paint). Paint 3D: none. |
| Snipping Tool / Snip & Sketch | **Done** (sg-snip) |
| Photos | **Done** (sg-photos) -- viewer only (no albums/editing) |
| Media Player | **Done** (sg-media) -- needs the image's GStreamer packages |
| Task Manager | **Done** (sg-taskmgr) |
| Zip folders | **Done** (sg-zip) -- no "Send to" item yet (per-user SendTo, sg-session) |
| Sticky Notes | **Done** (sg-sticky) |
| Character Map | **Done** (sg-charmap) |
| Settings | Control Panel (sg-control) stands in; no separate Settings app. |
| Terminal | **Done** (sg-terminal, wt.exe) -- tabs, profiles, split panes, search. |
| Clock / Alarms & Clock | Wine's `clock.exe` face only; no alarms, timers, stopwatch, world clock. |
| Magnifier, On-Screen Keyboard | **Done** (sg-magnify, sg-osk; magnify.exe/osk.exe, Win+Plus/Win+Esc, Win+Ctrl+O; wine-sg 0181-0182). |
| Disk Management, Disk Cleanup | None (Linux disks under Wine have no Windows volume layer to manage). |
| Event Viewer | None (`wevtutil` stub only). |
| Device Manager | None. |
| Services (services.msc) | Task Manager's Services tab only; no MMC. |
| Computer Management / MMC | None. |
| System Information | Wine's msinfo32 is an About box. |
| Resource Monitor | None (Task Manager's Performance tab). |
| Remote Desktop Connection | **Done earlier** (sg-mstsc). |
| WordPad | **Done** (sg-wordpad) -- ribbon, ruler, RTF/.docx/.odt/text, pictures, printing and preview (RichEdit EM_FORMATRANGE, wine-sg 0184). |
| PDF viewing | None out of the box (Edge is user-supplied; iexplore/Gecko cannot show PDFs). |
| Web browser | Only Wine's Internet Explorer on Gecko 2.47 -- not usable for today's web. Users install Edge/Firefox. |
| Fonts viewer | **Done** (sg-fontview: fontview.exe, the Fonts folder, per-user and all-users install; wine-sg 0183). |
| Help (Get Help, .chm) | hh.exe reads .chm; no Tips/Get Help app. |
| Notepad, File Explorer | Owned by other workers. |

### Remaining gaps, ranked (what a Windows user reaches for first)

1. **A web browser and PDF viewing** -- the biggest hole; decide policy (a
   first-run "get a browser" page, or reimplementing a PDF viewer on a
   free renderer -- clean-room rule applies).
2. **Settings app** (Windows 10/11 Settings layout over the Control Panel's
   pages) -- Win+I goes to the Control Panel today.
3. ~~Windows Terminal~~ -- done (sg-terminal).
4. **Alarms & Clock** (alarms, timer, stopwatch, world clock).
5. ~~WordPad refresh~~ -- done (sg-wordpad).
6. **Event Viewer / Services / Device Manager / Computer Management** --
   admin tools; need an MMC-style host and data sources (journald, SCM, udev).
7. ~~Magnifier and On-Screen Keyboard~~ -- done.
8. **System Information** (a real msinfo32).
9. ~~Font viewer and a Fonts folder~~ -- done.
10. **Disk Cleanup / Disk Management** (map to Linux storage via a broker).
11. **Resource Monitor**.
