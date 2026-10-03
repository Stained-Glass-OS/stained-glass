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

Its exit status comes back to PowerShell (`$LASTEXITCODE`). Typing into an
interactive bash started from inside an interactive PowerShell does not work
yet -- run commands as above, or `exit` PowerShell to return to the bash it
came from.

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

## Policy

Group Policy works as on Windows for the machine and its users: `.reg` and
`.pol` files placed in `/etc/stained-glass/policy.d/` apply at every start;
`sg-gpupdate` applies them now.
