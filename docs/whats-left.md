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
- Image thumbnails and bigger icon sizes; Tiles and grouped views (Wine's
  listview lacks them); Quick access pinning/recent files; details pane;
  drop onto the navigation pane; friendly type names ("Text Document");
  selected icons tint purple.
- "Send to > Compressed (zipped) folder" (per-user SendTo item, sg-session).

### Notepad
- Menu bar stays light in dark mode; printing untested (no printer);
  new strings English only.

### Settings / shell
- The taskbar ignores Settings' Taskbar/Start options; the lock screen
  ignores the chosen picture.
- Screen never turns off when idle: sg-compositor lacks the output-power
  protocol.
- Terminal: no split panes or search.
- Dark mode (system-wide), OOBE (first-run setup), Sleep in Start.

### Admin tools
- Disk Management: no create/delete/resize, no SMART.
- Services: no per-service security (`sc sdset`).
- `lusrmgr.msc` / `fsmgmt.msc` files not created yet.
- Device Manager: no enable/disable.
- Nothing writes the Security event log yet; its files are readable by the
  prefix group at the Linux level.
- `msinfo32 /report` returns before the file is written.

### Missing apps (ranked)
1. A web browser and PDF viewer out of the box (only Internet Explorer on
   Gecko 2.47; Edge is user-supplied).
2. WordPad refresh; Magnifier and On-Screen Keyboard; font viewer and the
   Fonts folder.

### Voice typing
- Text appears per utterance, not while speaking; spoken punctuation and
  filler words are English only; not yet tested with a real microphone in a
  VM.

### Platform
- Domain: real domain SID in Wine; machine GPOs from the domain.
- MSIX deployment (Store apps) in progress in wine-sg.
- winex11 BadWindow under Xvfb; desktop surface flush clipping.
- Out of scope (David, 2026-09-25): a signed boot chain (Secure Boot) and
  legacy BIOS boot. UEFI, unsigned, is the target.
- The apt site cannot carry files over 100 MB (GitHub), so the speech model
  ships only in the image/ISO.
