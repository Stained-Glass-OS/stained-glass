# Administration and remote support

Underneath, every Stained Glass machine is a Debian Linux system. That gives
an administrator tools Windows does not have -- above all, stepping into
another person's session from a terminal to see exactly what they see.

## Getting a terminal

- **On the machine:** **Win+X > Terminal**, or **Ctrl+Alt+F2** ... **F9** for
  a text console (works even when the desktop is frozen; **Ctrl+Alt+F1**
  returns). The sign-in screen allows the text consoles too.
- **From another machine:** `ssh name@machine`. SSH is on by default for
  accounts that may use it.

Administrators can use `sudo`.

## Into someone's Windows side: `su -`, then `powershell`

Windows has no good way to become another user from a command line. Here:

```
ssh admin@their-pc
sudo su - jane        # become Jane, in her environment
powershell            # PowerShell on Jane's Windows side
```

That PowerShell is Jane's: her registry (`HKCU:` is her hive), her
`%USERPROFILE%`, her programs and their settings. Look at what she sees,
fix a setting, start or stop her programs, read her logs -- without taking
over her screen.

```
PS C:\users\jane> Get-ItemProperty 'HKCU:\Control Panel\Desktop' | Select WallPaper
PS C:\users\jane> Get-Process
PS C:\users\jane> exit          # back to bash, still as Jane
```

As `root`, `powershell` opens the machine's own Windows side, as SYSTEM
(what `psexec -s` gives on Windows): machine-wide settings (`HKLM:`), services,
programs installed for everyone.

## From PowerShell back to Linux: `bash`

In PowerShell or the Command Prompt, `bash` runs the Linux shell as the same
person, in the same folder:

```
PS C:\users\jane\Documents> bash -c 'ls -la; df -h /'
PS C:\users\jane\Documents> bash ./fix-something.sh
```

Its exit status comes back to PowerShell (`$LASTEXITCODE`). Plain `bash`
opens an interactive bash in the same terminal -- over SSH too -- with its
own line editing and job control; Ctrl+C stops bash's command, not
PowerShell, and `exit` returns to PowerShell where you left it.

## Restarting things

| Problem | What to do |
|---|---|
| One program hangs | Task Manager > End task |
| The desktop hangs for one person | Ctrl+Alt+Backspace (their Windows programs end, the desktop comes back) |
| From a terminal, the same for someone | `sudo -u jane /usr/lib/stained-glass/sg-wine-reload` |
| The Windows side for everyone | `sudo systemctl restart sg-wineserver` (ends every Windows program on the machine) |

## Logs

- `journalctl -t sg-session` -- sessions, the desktop and its keeper.
- `journalctl -u sg-wineserver -u sg-prefix-init` -- the machine's Windows side
  and its setup.
- `/var/log/stained-glass/` -- the lock screen, administrator prompts, the
  elevation broker.
- **Report a problem** on a program's taskbar button makes a report a
  developer can read.

## Updates and packages

Everything the system is made of is a Debian package from the project's
repository, so `apt` is the whole story: `sudo apt update && sudo apt
full-upgrade` updates a machine, and the same works over SSH for many.
Updates download in the background and install at the next restart on their
own.

## The firewall

Stained Glass Firewall is on by default and blocks connections other
computers start, unless they are allowed -- see [The firewall](07-firewall.html).
`sg-firewall status` shows what it is doing; `journalctl -u sg-firewall`
what it allowed, asked about and blocked.

## Policy

Group Policy works as on Windows for the machine and its users: `.reg` and
`.pol` files placed in `/etc/stained-glass/policy.d/` apply at every start;
`sg-gpupdate` applies them now.

## A kiosk: a tablet that runs one app

A device that is meant for one job -- a tablet by the stereo that only plays
music with the Sonos app, a sign-in sheet by the door -- can start straight
into that app, with no sign-in screen and no desktop to wander off into. This
is what Windows calls automatic sign-in and assigned access.

**Set it up** (as an administrator):

1. Make an account for the job: **Settings > Accounts > Other users > Add
   someone else to this PC**. A *standard* account: anyone who can turn the
   tablet on can use it without its password.
2. Sign in as that account once and install the app it will run -- from the
   SG Store (Sonos, for example), or any other way. Make sure the app is in
   Start, for everyone or for you as the administrator (installers that ask
   usually mean "everyone"). Set the app up the way it should stay (for
   Sonos: find your system, pick the room). Sign out.
3. Sign in as an administrator and open **Settings > Accounts > Kiosk**.
   Under **When this PC starts, sign in automatically as**, choose the
   account. You are asked for an administrator's permission.
4. Under **Kiosk app**, press **Choose an app** and pick the app from the
   list of Start's apps.
5. Restart the tablet. It signs that account in by itself and opens the app
   full screen; the taskbar hides at the bottom edge of the screen. If the
   app is closed -- or crashes -- it opens again after a few seconds.

Without step 4 the account simply signs in by itself and gets the ordinary
desktop. To start an app at sign-in without the kiosk, see
[Starting programs at sign-in](03-programs.md#starting-programs-at-sign-in).

**Getting out of the kiosk.** Press **Ctrl+Alt+Del** and choose **Sign out**.
The ordinary sign-in screen appears -- the automatic sign-in happens only
once per start of the PC -- and an administrator can sign in. In the kiosk
account itself, pointing at or touching the bottom edge of the screen shows
the taskbar, and the **Start** key opens Start. Over the network, an
administrator can `ssh` in as always.

**Turning it off.** In **Settings > Accounts > Kiosk**, choose **Don't use a
kiosk app**, or set the automatic sign-in to **Nobody (show the sign-in
screen)**. The account's own taskbar setting comes back at its next sign-in.

**Worth knowing:**

- No password is stored. The sign-in service starts the account's session
  directly at boot (greetd's initial session); for an account that signs in
  by itself, the screen does not lock when it turns off or the PC sleeps.
- The account's saved passwords (its keyring) stay locked, since no password
  was typed, and it is not asked to unlock them at every start. Windows
  programs keep working; a Linux program that wants to save a password may
  ask for one.
- A program that starts a second program and exits (an updater-launcher) is
  followed to the program it started. A program that keeps closing at once
  is retried every minute after five quick tries, not in a tight loop.
- The settings live in `/etc/stained-glass/autologon.conf` and greetd's
  `/etc/greetd/config.toml` (a marked `[initial_session]` block); the session
  log (`journalctl -t sg-session`) shows `sg-kiosk:` lines when the app starts
  and closes.
