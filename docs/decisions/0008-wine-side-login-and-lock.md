# 0008 — The login and lock screens run inside Wine

* Status: accepted
* Date: 2026-09-22
* Supersedes: the P8 rule in `docs/BRIEF.md`, "Credentials never pass through Wine"

## Context

The brief put the greeter on the Linux side and kept credentials out of Wine
entirely. That is the safer arrangement, and it does not survive contact with
how managed fleets are actually supported.

RMM and remote-desktop tools — ScreenConnect, TeamViewer, AnyDesk, RDP — are
Windows programs. They run as services, attach to the console session, and
expect to find a *Windows* login screen there. An unattended machine sitting at
a `greetd` prompt is, to all of them, a machine showing nothing: they cannot
render it, cannot type into it, and cannot log a technician in.

For a fleet operating system that is close to disqualifying. The single most
common remote-support task is reaching a locked or logged-out machine. If
Stained Glass cannot be supported the way the Windows machines beside it are
supported, it does not matter how well it runs applications.

David's decision: the login and lock screens are Wine-side, with compatibility
for remote tools, "just like how other Windows systems are managed."

## Decision

The credential UI is a Windows program running under Wine. Authentication
itself stays on the Linux side, in PAM, reached through a small bridge.

```
  sg-greeter.exe  (Wine PE, Win10-style UI)
        |  inherited stdin/stdout pipes
  sg-greet-bridge (Linux, unprivileged)  <- launches Wine as its child
        |  greetd IPC
      greetd  ->  PAM  ->  session
```

The transport is a pair of inherited pipes, not a socket. Wine does not
implement `AF_UNIX` (`socket()` returns `WSAEAFNOSUPPORT`), and a loopback TCP
port would be reachable by every local user and need a shared secret to close
that hole again. A pipe handed to a child process is reachable by nobody else
at all, which is a property of the kernel rather than of our code. Verified:
a Windows PE running under Wine reads and writes its inherited stdio to a
Linux parent.

- **Wine never decides whether a login succeeds.** It collects the credential
  and forwards it. PAM remains the only authority, so every existing policy —
  account expiry, lockout, MFA modules, domain auth in Phase 2 — keeps working
  untouched.
- **The greeter session is its own Unix user** (`sggreet`) with its own prefix.
  It holds no user data, and a compromised user session cannot read it.
- **No Windows applications run in the greeter session.** Only the greeter.
- **The lock screen runs on a dedicated window station**, the way Windows keeps
  Winlogon on a separate desktop. `wine-sg` patch 0007 already gives us the
  mechanism, and patches 0002/0003 give window stations real security
  descriptors, so this is an enforced boundary rather than a convention.

## Consequences

**The password passes through Wine.** This is the cost, and it is not
hypothetical: Wine is a large codebase implementing a foreign ABI, and it is
now in the authentication path. We accept it because the alternative is a
fleet OS that cannot be remotely supported.

**The lock screen needs more than a separate window station.** The login screen
runs in a session with no other Windows programs in it; the lock screen, by
definition, does not. A separate window station raises the bar without matching
Windows' Secure Attention Sequence.

**Superseded by [ADR 0009](0009-credential-ui-security-model.md).** Leaving it
at "weaker than Windows" was not acceptable: a system that looks like Windows
gets trusted like Windows, so every habit that is safe there becomes silently
unsafe here. ADR 0009 takes the lock screen out of the user's session entirely,
freezes that session while locked, and gives the compositor sole ownership of
input — parity or better on every axis except Credential Guard, with an
adversarial gate to prove it rather than assert it.

Mitigations we do take:
- the credential is never written to the registry, to disk, or to any log;
- the greeter holds it only for the length of one PAM exchange;
- the bridge has no listening socket at all; it speaks to the greeter over
  pipes it created before forking, so no other process can connect to it;
- failure counting and delay stay in PAM, where fail2ban and lockout policies
  already see them.

**What would let us restore the original rule:** a compositor of our own
(`sg-compositor`, P8) could draw the credential field as a Wayland surface
outside Wine while the surrounding UI stays Windows-side. That keeps remote
tools working *and* keeps the password out of Wine. It is the right long-term
answer and it is a lot more work than this. Revisit when P8 lands.

## Alternatives rejected

- **Linux greeter (`greetd` + a GTK/Qt front end).** Safest, and unreachable by
  every remote-support tool a fleet already owns. Rejected on those grounds.
- **Linux greeter plus a separate Windows-side "remote console" mode.** Two
  login paths, two sets of bugs, and the remote path ends up being the Wine one
  anyway — so it has the same exposure with more code.
- **Autologin plus a Wine-side lock screen only.** Leaves the machine logged in
  across reboots, which is worse than the problem it avoids, and gives domain
  login nowhere to live in Phase 2.
