# 0004. Licensing: AGPL-3.0-or-later where possible

- **Status:** accepted
- **Date:** 2026-09-21
- **Deciders:** David Hamner

## Context

The brief left several licenses marked **[DAVID]**: `sg-image` (default
LGPL-2.1+), `sg-session` ("same"), `prt-broker`, `sg-compositor` and
`sg-greeter`. `sg-shell` was left as "depends on origin".

David's decision: **AGPL, where possible.**

The qualifier is doing real work. Several repos in this project cannot be AGPL,
and one of the reasons is load-bearing enough that getting it wrong would
quietly break a rule the project depends on.

## Decision

**AGPL-3.0-or-later for all new-code repos.** Applied now to `sg-image` and
`sg-session`; the default for `sg-testlab`, `sg-pnp`, `gpo-agent`,
`prt-broker`, `sg-compositor` and `sg-greeter` when they start.

**Not AGPL, for reasons outside our control:**

| Repo | License | Why not AGPL |
|---|---|---|
| `wine-sg` | LGPL-2.1+ | It is a fork of Wine. A fork carries its upstream's license. |
| `wdf-wine` | MIT | It is a port of Microsoft's MIT-licensed WDF. The brief fixed this, and it was never a [DAVID] choice. |
| `sg-shell` | **split, see [ADR 0007](0007-shell-strategy.md)** | Explorer patches are LGPL-2.1+ in `wine-sg`; our own panels are separate programs and stay AGPL. |

Documentation in `stained-glass` stays **CC-BY-SA-4.0**. It is prose, not
software; CC-BY-SA is the copyleft license built for prose, and AGPL's terms
(source distribution, network interaction) describe things a document does not
do. Say the word and it changes, but this is a deliberate keep, not an oversight.

## The constraint that matters most

**Anything we intend to send upstream to Wine must not be AGPL.**

Wine is LGPL-2.1+. AGPL-3.0 code cannot be incorporated into an LGPL-2.1+
project — the relicensing only runs the other way. Rule 4 of the brief says to
shape every Wine patch for upstream submission, small and one concern at a
time. If Wine-bound code were written in an AGPL repo, that rule becomes
impossible to follow, and we would not find out until we tried to submit.

In practice this draws a line through the project:

- **Wine-side changes** — anything that ends up as a patch to Wine's tree, in
  `wine-sg` — are LGPL-2.1+, always.
- **Everything beside Wine** — daemons, agents, the compositor, the greeter,
  the image, the test harness — is AGPL-3.0-or-later.

S2 is where this line gets tested, since it is expected to produce both: Wine
patches *and* new machine-level services. Those belong in different repos under
different licenses, and the split has to be made deliberately rather than
discovered at submission time.

## The other incompatibility, for P7

**ReactOS is GPL-2.0-only.** GPL-2.0-only and AGPL-3.0 are incompatible in both
directions — GPL-2.0-only has no "or later" clause to upgrade through.

So the P7 shell bake-off is not only a technical choice:

- **Option A** (extend Wine's `explorer`) → LGPL-2.1+, upstreamable.
- **Option B** (run ReactOS `explorer.exe` under Wine) → GPL-2.0-only, and
  `sg-shell` cannot be AGPL.

The brief already notes that GPL-vs-LGPL is fine as separate binaries in
separate packages, and that remains true — we are distributing separate
programs, not linking them. But it means option B constrains `sg-shell`'s
license, and that should be on the table during the bake-off rather than
discovered after it.

## What AGPL means for the actual users

Worth stating plainly, because the target is managed enterprise fleets and this
is the kind of thing that surfaces late.

AGPL §13 adds one obligation over GPL-3.0: if you *modify* the software and let
users interact with it *remotely over a network*, you must offer those users the
source of your modified version.

- For the desktop components — `sg-session`, `sg-compositor`, `sg-greeter`,
  `sg-image` — §13 is close to inert. Nobody interacts with a login session over
  a network.
- For the **manageability surface** it is not inert. `gpo-agent`, `prt-broker`,
  and the P6 work (remote SCM, remote registry, WMI/CIM, WinRM) exist precisely
  to serve network clients. An organization that modifies those and exposes them
  to its own machines would owe source to the users of those endpoints.

For internal fleet use this is usually unremarkable: the "users" are the
organization's own machines and staff, and the obligation is to them. It becomes
a real question only for someone building a modified Stained Glass into a
product they operate for others — which is, presumably, much of the point of
choosing AGPL.

This is not an argument against the decision. It is the consequence, recorded so
it is not a surprise when a deployment asks about it.

## Consequences

- `sg-image` and `sg-session` relicensed from LGPL-2.1+ to AGPL-3.0-or-later.
  Cheap to do now: there are no outside contributors, so relicensing needs
  nobody's agreement.
- Every new repo starts AGPL-3.0-or-later unless it is a fork or a port, in
  which case it carries upstream's license.
- **Wine-bound code must be segregated by repo, not merely by directory.** A
  patch developed inside an AGPL repo is contaminated for upstream purposes.
- P7's bake-off now has a licensing axis. Record it in that ADR.
