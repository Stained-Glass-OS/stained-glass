# 0009 — Security model for the credential UI: at least Windows, ideally better

* Status: accepted
* Date: 2026-09-22
* Builds on: [ADR 0008](0008-wine-side-login-and-lock.md)

## Context

ADR 0008 put the login and lock screens inside Wine so that remote-support
tools can see them, and admitted a weakness: the lock screen runs inside a
session full of running applications, and Wine has no Secure Attention
Sequence, so it is *weaker* than Windows.

David's instruction: equivalent or better than Windows. "A weak security model
with Windows equivalency could be very dangerous" — and that is exactly right.
A system that looks like Windows invites people to trust it like Windows. If
the lock screen can be keylogged by any program the user ran earlier, then
every habit that is safe on Windows becomes unsafe here, silently.

So this ADR replaces the "we raise the bar but do not match Ctrl+Alt+Del"
position with a design that matches or beats Windows on each axis.

## What Windows actually provides

| Mechanism | What it buys |
|---|---|
| Secure Attention Sequence (Ctrl+Alt+Del) | Only the kernel can deliver it; no program can fake or swallow it, so the user can always reach the real credential UI |
| Secure Desktop (`Winlogon` desktop) | Programs on `Default` cannot post messages to it, enumerate its windows, or capture it |
| Session isolation | Services live in session 0, away from the interactive session |
| Credential Guard (recent, VBS) | Derived secrets isolated from the OS itself |

And what it does **not** provide: while the machine is locked, **every
application the user was running keeps running**. Windows defends the
credential UI from them; it does not stop them.

## Decision

Four mechanisms. Two bring us to parity; two put us ahead.

### 1. The lock screen is not in the user's session (parity, then some)

It runs on a dedicated window station in the **machine-level, session 0**
wineserver — the Windows system, not the user's — as its own account. That is
the `Winlogon`-desktop idea, and `wine-sg` already has the pieces: patch 0007
puts session 0 on its own window station, and patches 0002/0003 give window
stations and desktops real security descriptors, so the separation is enforced
by the server rather than being a convention.

A program in the user's session is on `WinSta0`. It cannot post to, enumerate,
or read the lock screen's windows, because they are on a different station
owned by a different user.

### 2. Everything in the user's session is frozen while locked (better)

On lock, the user's session processes are moved to a frozen cgroup. A frozen
process does not run: it cannot poll the keyboard, cannot capture the screen,
cannot race anything, cannot phone home. On unlock they thaw and continue.

**Windows cannot do this** — its applications run throughout. This is the
single biggest improvement available to us, and it costs nothing to implement
because the kernel already has `cgroup.freeze`.

Session 0 is deliberately *not* frozen: that is where the RMM and remote-access
services live, and freezing them would make a locked machine unreachable, which
is the problem ADR 0008 exists to solve.

### 3. The compositor owns input (better than SAS)

Wine has no Secure Attention Sequence, and we do not need one. Under Wayland a
client cannot grab the keyboard globally — input routing belongs to the
compositor. While locked, the compositor routes **all** input to the lock
surface and nothing else, so there is no keystroke for another program to see
even if it were running.

This is stronger than Ctrl+Alt+Del in one specific way: SAS guarantees you can
*reach* the real UI, but on Windows a program can still watch the keyboard
while you type into it if it has the right hooks. Compositor-owned routing
means the keystrokes are never delivered anywhere else at all.

The "am I talking to the real lock screen?" guarantee that SAS provides is met
by the lock surface being the only thing the compositor will display and accept
input for while locked — a spoof would have to be the compositor.

### 4. The credential never enters the user's Wine (parity with Credential Guard's intent)

The lock UI collects into session 0's Wine, not the user's, and passes it
straight to PAM through the bridge. It is never written to a registry, a file,
or a log, and is cleared from the buffers that held it as soon as PAM has it.

We do not claim Credential Guard equivalence: we have no VBS isolation, and a
kernel compromise ends the discussion. That is true of Windows without VBS too,
and it is worth being precise rather than generous.

## Consequences

**Where we end up, against Windows:**

| Property | Windows | Stained Glass |
|---|---|---|
| Credential UI isolated from user programs | Secure Desktop | Separate window station, separate Unix user, separate session |
| User programs during lock | keep running | **frozen** |
| Keystrokes reachable by other programs | possible with hooks | **never delivered to them** |
| Guaranteed path to the real UI | Ctrl+Alt+Del | compositor is the only thing that can draw or route while locked |
| Credential isolated from the OS | Credential Guard (VBS) | **no equivalent** — stated plainly |
| Remote support can reach a locked machine | yes | yes (session 0 is not frozen) |

**The honest gap is Credential Guard.** Everything else is parity or better.

**This must be proved, not asserted.** The claim "a program in the user's
session cannot observe the lock screen" is exactly the kind of claim that is
comfortable to believe and easy to get wrong. `sg-session` carries an
adversarial gate: a Windows program that logs every keystroke it can obtain by
every means Wine offers, started before the lock, with the gate typing a known
string into the lock screen. If that string appears in its log, the gate fails.

**What this costs.** Freezing a session is visible: media stops, downloads
stall, a long build pauses. That is the correct trade for a workstation and it
should be a policy knob for machines doing unattended work, defaulting to
frozen.
