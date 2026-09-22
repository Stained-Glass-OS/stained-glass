# 0011 — sg-compositor: our own Wayland compositor, starting from cage

* Status: accepted
* Date: 2026-09-22
* Builds on: ADR 0003, [0009](0009-credential-ui-security-model.md), [0010](0010-remote-access-and-the-lock-screen.md)

## Context

Phase 0 hosts the session in cage, a kiosk compositor that shows one
fullscreen application. It got us to a booting Windows shell, and it cannot
take us further. Three things now need a compositor we control:

- **Lock-screen input isolation** (ADR 0009). The adversarial gate proved that
  freezing the user's session does not stop a keylogger — `GetAsyncKeyState`
  press bits accumulate and are recovered on thaw. The load-bearing defence is
  that lock-screen key events never reach the user session's XWayland at all.
  Only the compositor routes input, so only the compositor can guarantee that.
- **Remote access** (ADR 0010). Screen capture and input injection must be
  capabilities granted to the machine session and refused to user-session
  programs. cage exposes neither control.
- **The shell** (ADR 0007, P7/P8). The taskbar and panels want layer-shell
  placement and a toplevel list; cage has neither, which is also why the Phase
  0 gate's window checks are X11-only (ADR 0003).

## Decision

Build `sg-compositor` on wlroots 0.18, **starting from cage 0.2.0**, in its own
repo.

- **cage, not tinywl.** cage is already what hosts our session, so milestone 1
  is "cage under a new name, and the existing session gate still passes" — a
  known-good base that every later change is measured against. tinywl would
  have meant rebuilding cage's XWayland and output handling first, for nothing.
- **MIT**, cage's licence. David's call: MIT is fine for components. cage's
  copyright notices stay on its files; our additions are MIT too, so the repo
  has one licence and no mixed-licence files. The first commit is cage
  verbatim, so upstream authorship is clear in history.
- **wlroots 0.18**, the version Debian trixie ships and cage builds against.

### Milestones, each with a gate

1. **Replace cage.** `sg-session`'s session gate passes with `sg-compositor`
   hosting the session. No behaviour change.
2. **Lock mode with input isolation.** While locked, one designated lock client
   receives all input and the user's XWayland receives none. Gated by
   `sg-lock-security-check` running on the real compositor: the adversary lives
   in the compositor's XWayland, the secret is typed into the lock client, and
   it must not appear.
3. **Session-scoped privileged protocols.** Screen capture and virtual
   keyboard/pointer are offered only to clients whose Unix uid is the machine
   session's (`wl_client_get_credentials`, which reads `SO_PEERCRED` — the
   kernel's word, not the client's). Gated by a user-session client asking and
   being refused, and a machine-session client asking and being served.

Then the shell work (layer shell, toplevels) builds on it.

## Consequences

- We own a compositor. cage is ~2,800 lines, small enough to own properly, but
  wlroots API changes between versions are now our problem; pinning to the
  distribution's wlroots keeps that to once per Debian release.
- The Phase 0 X11-only window checks can eventually be replaced by asking the
  compositor, which removes ADR 0003's limitation.
