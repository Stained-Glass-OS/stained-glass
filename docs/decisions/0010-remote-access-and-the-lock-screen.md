# 0010 — Remote access to the login and lock screen

* Status: accepted
* Date: 2026-09-22
* Builds on: [ADR 0008](0008-wine-side-login-and-lock.md), [ADR 0009](0009-credential-ui-security-model.md)

## Context

ADR 0008 put the credential UI inside Wine so remote-support tools can see it.
ADR 0009 then isolated that UI so nothing in the user's session can observe it.
This ADR is where those two meet the actual remote tools, and it is the hard
part: the same lock screen that must be invisible to the user's own programs
must be reachable, and typeable, from across the network.

There are two remote patterns in the field, and Stained Glass should reproduce
both as closely as it can, because fleets use both.

**Pattern A — mirror the console and type into it.** ScreenConnect, TeamViewer,
AnyDesk and VNC show the technician the actual screen, lock screen included, and
let them type the username and password into it exactly as if sitting at the
machine. There is no separate credential step; the remote input drives the
on-screen login.

**Pattern B — authenticate before connecting.** Windows RDP (`mstsc`) takes the
username and password in the client, before "Connect". The protocol
authenticates up front (NLA / CredSSP), and on success the technician lands in
an already-unlocked desktop — the lock screen is never drawn for them.

## Decision

Both patterns terminate the credential at PAM, never in Wine, by reusing the
bridge from ADR 0008. The insight is that `sg-greet-bridge` already abstracts
the only thing that matters: *something collects a credential, PAM decides, a
session starts.* The on-screen greeter is one collector. Remote access adds two
more sources into the same funnel.

```
  credential source                      →  sg-greet-bridge  →  greetd  →  PAM  →  session
  ------------------------------------------
  sg-greeter.exe          (at the console)
  remote input via A      (drives sg-greeter, no new credential path)
  RDP NLA handler via B    (credential from the protocol, pre-connect)
```

### Pattern A: console shadow, session 0, gated by the compositor

The remote-access agent is a Windows program in session 0 — the machine
session, which ADR 0009 keeps unfrozen precisely so remote support survives a
lock. It does two privileged things: it reads the compositor's primary output
(to show the screen) and injects input into it (to type).

Both are **capabilities the compositor grants only to session 0.** This is the
same boundary ADR 0009 defends, seen from the other side: a user-session
program asking to capture the screen or inject into the lock surface is refused;
a session-0 agent is allowed. The compositor decides by the requesting client's
session, established at connect time, not by anything the client claims.

The technician then types into the on-screen `sg-greeter` through injected
input, and it flows through the bridge like any local login. No new credential
path exists, so no new place for the credential to leak.

### Pattern B: pre-authenticated RDP, credential straight to the bridge

The RDP server is a session-0 service. Its NLA exchange yields the username and
password before any graphical session is committed. It hands them to the bridge
as a credential source — the same `create_session` / `post_auth_message_response`
messages the on-screen greeter sends — and PAM decides. On success, greetd
starts the user's session and the RDP server streams it, already unlocked. The
lock screen is never rendered for this path, matching `mstsc`.

If the physical console is locked when a Pattern B login for the same user
succeeds, the console session is **thawed and attached to**, not duplicated:
one interactive session per user, as on Windows. A different user authenticating
remotely gets their own session; the console stays locked and frozen.

### Transit security is not optional

Both patterns move a password across the network, so both require the transport
to authenticate the server and encrypt before the credential is sent:

- Pattern B uses NLA/CredSSP over TLS — the FreeRDP server stack provides it,
  and it is the property that makes "type the password before connect" safe: the
  credential is not sent until the server is proven and the channel is private.
- Pattern A's keystrokes ride the agent's own transport, which must be TLS with
  a pinned or verified server identity. An agent that mirrors the lock screen
  over cleartext is a downgrade of the whole model and is not shipped.

The credential still never touches the registry, the disk, or a log, on either
path, and is cleared from the bridge's buffers as soon as PAM has it.

## Update: what building pattern B changed

Built in `sg-session` as `sg-rdp-authd` (credential half only; the session
needs `sg-compositor`). Three things in the design above turned out wrong or
incomplete:

- **Remote logins do not go through greetd.** greetd manages one physical seat.
  A remote session authenticates through PAM directly, which keeps PAM the only
  authority, and the funnel diagram above is correct in spirit (one path to
  PAM) but not in route.
- **Privilege separation is required, not optional.** The code that parses RDP
  off the network is the most exposed in the system and must not run as root;
  checking an arbitrary user's password needs root. A root monitor forked at
  startup does only the PAM check, over a socketpair; the RDP side drops to an
  unprivileged account before listening. The TLS key is loaded before the drop,
  so its file can be root-only.
- **NLA is not used for local accounts.** Server-side NLA must verify the
  client's NTLM exchange, which needs every user's NT hash on disk — the MD4
  hashes Windows keeps in the SAM, which pass-the-hash attacks target. Storing
  none of them is strictly better than Windows at rest. The cost is that the
  RDP connection sequence runs before authentication, where NLA would refuse an
  unauthenticated client earlier; authentication still completes before any
  session resource exists. Domain accounts get NLA via **Kerberos** in Phase 2,
  which needs only the machine keytab and is Windows' strongest mode.

And one trap worth knowing: FreeRDP 3's server `Logon` hook runs during
negotiation, before the client has sent any credential, and the connection
continues whatever it returns. The first build trusted it, and a refused logon
reached the session stage. Authentication happens in `PostConnect` from the
Client Info packet, with default deny on every connection, and the gate has a
case that fails if that regresses.

A client that connects **without** a credential is refused today. Real Windows
RDP shows such a client the Winlogon screen; ours will stream `sg-greeter` once
the compositor can, which makes pattern A and B the same screen for the user.

## Update: streaming the session (E1, 2026-09-24)

Pattern B now ends in a desktop. What building it settled:

- **A remote session is a session of its own**, not a view of the console:
  after PAM accepts a user, `sg-rdp-authd`'s root monitor starts
  `sg-session-start` for them under `systemd-run` (`PAMName=`, so logind and
  the profile service see an ordinary session) with sg-compositor on its
  headless backend, sized to the client. It gets a seat directory of its own,
  and with it its own lock service: Win+L typed into the client locks it and
  the password typed into the client unlocks it. Disconnecting leaves it
  running; the next login for that user reconnects to it, as on Windows.
- **The RDP side gains exactly one session, and only after PAM.** The monitor
  connects to that session's privileged compositor socket and passes the
  connection over (`SCM_RIGHTS`); the unprivileged worker never holds a
  capability for any session whose password it has not seen accepted.
- **Capture and injection are the compositor's privileged protocols**
  (screencopy, virtual keyboard and pointer), so the invariant above -- a
  user-session program can obtain neither -- is unchanged by remote access.
- **Uncompressed bitmap updates, for now.** FreeRDP 3.15's planar encoder does
  not round-trip (RLE streaks detail; raw planes swap red and blue), which the
  dev-box gate's pixel-exact comparison caught. An encoder of our own for the
  open RDP 6.0 bitmap compression spec is the planned replacement.
- **Still open:** a user signed in at the console is refused a remote login
  rather than having the session moved (Windows' behaviour), which needs the
  compositor to move a session between outputs; and pattern A.

## Consequences

**The security-critical invariant is one sentence:** screen capture and input
injection are session-0 capabilities, enforced by the compositor, and a
user-session program can obtain neither. If that invariant holds, Pattern A is
safe; if it can be bypassed from the user session, it *is* the keylogging hole
ADR 0009 closes, arriving through the compositor instead of through Wine. The
adversarial gate (`sg-lock-security-check`) exists to keep it honest, and it
must grow a case that runs the adversary as a would-be capture/inject client and
confirms the compositor refuses it.

**This needs `sg-compositor` (P8).** cage grants no per-client, session-scoped
capture or injection control, so the full design lands with our own compositor.
What is buildable now, and is: the bridge already accepts multiple credential
sources, so the Pattern B RDP-to-PAM funnel can be wired and gated ahead of the
compositor work, against the greetd stub the greeter gate already uses.

**We do not reimplement RDP.** The server is FreeRDP, which brings NLA, TLS and
the graphics pipeline. Our code is the session-0 service that binds it to the
bridge and to the compositor's capture/inject capabilities — not a protocol
stack, which in a credential path we would have no business writing ourselves.

## Alternatives rejected

- **A second, remote-only login path separate from the console greeter.** Two
  collectors, two sets of bugs, and the remote one is the higher-value target.
  Funnelling both through one bridge means one audited path to PAM.
- **Letting the RDP server authenticate against its own user store.** That puts
  an authority beside PAM, so policy (lockout, expiry, domain auth) would have
  to be duplicated and kept in sync. PAM stays the only authority.
- **Granting capture/inject to any Wine process that asks (as Windows' pre-UIPI
  model effectively did).** That is the hole. Session-scoped capability is the
  whole point.
