# The firewall

Stained Glass has a firewall built in and turned on: **Stained Glass
Firewall**. It works the way the firewall on a Windows PC does, so if you
have used one, nothing here will surprise you.

## What it does

- **Connections other computers start to your PC are blocked**, unless you
  have allowed them. A program on another computer cannot reach a program on
  yours just because it is listening.
- **Connections your PC starts are never blocked.** Browsing, email, games,
  updates, streaming -- and the answers to them -- go through as before.
- Some things always pass because a network cannot work without them:
  getting an address from your router (DHCP), the messages IPv4 and IPv6
  rely on, and the PC talking to itself.

## Public and private networks

Every network you connect to is either **Public** or **Private**:

| | Public | Private |
|---|---|---|
| Meant for | A network you don't trust: a cafe, an airport, a hotel | A network you trust: your home, your office |
| Other devices can find your PC | No | Yes (Network Discovery) |
| File and printer sharing | No | Yes, if you share |
| Your PC answers ping | No | Yes |
| Apps you allowed | Only those ticked for Public | Those ticked for Private |

A network you join for the first time is **Public**. To change it, open
**Settings > Network & Internet > Firewall** and choose Public or Private
under **Network profile** (this needs an administrator, as on Windows).

On a PC that is part of a domain, the domain's own network is a **Domain**
network, treated like a Private one.

## When an app asks

When a program starts waiting for connections from other computers -- a
music player that your phone or speakers talk to (Sonos does this), a game
you host, a file transfer tool -- and nothing has decided about it yet, you
see:

> **Stained Glass Firewall has blocked some features of this app**

with the app's name, its publisher and where it is, and two boxes:

- **Private networks, such as my home or work network**
- **Public networks, such as those in airports and coffee shops** (not
  recommended because these networks often have little or no security)

The box for the network you are on now is already ticked. Choose **Allow
access** (the shield means it needs an administrator's approval) and the app
can be reached on those networks from then on -- whenever it is running.
Choose **Cancel** and it stays blocked; it will not ask again, and it appears
in the list of allowed apps with both boxes clear, so you can change your
mind later.

This works the same for Windows programs and for Linux apps.

Many installers set up the firewall themselves (as they do on Windows,
through the firewall's programming interface or `netsh advfirewall`): those
programs are allowed as soon as they are installed and never ask.

## Allowing an app yourself

**Settings > Network & Internet > Allowed apps** (also Control Panel >
System and Security > Stained Glass Firewall > *Allow an app through
firewall*) lists the apps and features that may be reached, with a
**Private** and a **Public** box for each:

- Choose **Change settings** (an administrator's approval), then tick or
  clear the boxes. A change takes effect within a couple of seconds.
- **Allow another app...** picks a program that has not asked yet.
- **Remove** takes an app off the list (it will ask again next time).

The built-in features are listed too:

| Feature | Networks | What it is |
|---|---|---|
| Remote access (SSH) | All | Signing in to this PC with `ssh`, which Stained Glass has on |
| Remote Desktop | All | Only while Remote Desktop is turned on |
| File and Printer Sharing | Private | Shared folders and printers |
| Network Discovery | Private | Finding other devices, and being found |
| Domain Controller | All | Only on a PC that is a domain controller |

## Opening a port

Most apps never need this: allowing the app is enough, and its ports open
only while it runs. For something that cannot ask -- a server you run by
hand, for example -- **Settings > Network & Internet > Inbound port rules**
(choose *Change settings*) adds a rule by port number (or a range such as
`5000-5010`), TCP or UDP, allow or block, and the networks it applies to. A
port rule is open whether or not anything is listening.

## Turning it off

**Settings > Network & Internet > Firewall** has a switch for each kind of
network. Turning one off lets every connection in on those networks, and
the page warns you while it is off. It is better to allow the one app you
need. **Restore firewalls to default** puts everything back as it was when
Stained Glass was installed: every allowed app and port is removed (apps
will ask again) and the firewall is on everywhere; your networks stay Public
or Private.

## When you updated to the version with the firewall

Nothing you already used should stop working: when the firewall arrives
with an update, the networks you were using become **Private**, and every
service and program that was accepting connections at that moment gets a
rule. What was allowed is written to
`/var/lib/stained-glass/firewall/upgrade.log`. Remove any you don't want on
the Allowed apps page.

## For administrators

- `sg-firewall status` shows the state: each network, each rule, and what is
  listening right now and whether it is allowed.
- `sudo sg-firewall rule-add allow private,public tcp 8080 '*' "My server"`
  adds a port rule; `rule-add allow private any '*' /usr/bin/app "App"`
  allows a program; `rule-remove`, `profile public off`, `network UUID
  private`, `reset` -- see `sg-firewall` with no arguments.
- `netsh advfirewall firewall add rule ...`, `netsh advfirewall set
  allprofiles state on|off` and `netsh advfirewall show currentprofile` work
  from an elevated Windows command prompt, as on Windows.
- The rules live in `/etc/stained-glass/firewall.conf`; rules Windows
  programs add are kept where Windows keeps them (the registry's
  FirewallRules key) and applied from there.
- The firewall is its own nftables table, `inet sg_firewall`. It never
  touches other tables: a VPN's kill switch (for example Eddie's Network
  Lock) works beside it. `journalctl -u sg-firewall` shows what it allowed,
  asked about and blocked.
- To switch it off completely: `sudo systemctl disable --now sg-firewall`.

The firewall keeps unwanted connections out. It is not a defence against a
program you choose to run that is itself malicious: such a program can
connect out, like any other. That is what [virus
protection](06-viruses.html) and installing software from the SG Store are
for.
