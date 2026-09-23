# 0006. Wine prohibits LLM-generated code

- **Status:** accepted
- **Date:** 2026-09-21
- **Deciders:** David Hamner — *"Given Wine's policy we will simply not write
  upstream patches."*
- **Relates to:** brief rule 4, [S2 analysis](../s2-wineserver-analysis.md), [ADR 0005](0005-building-wine-ourselves.md)

## Context

The brief says, in §5 under S2:

> Before submitting anything upstream, check Wine's current contribution policy
> regarding AI-assisted code and record it in an ADR.

S2 is the point where that stops being hypothetical: it is expected to produce
Wine patches, and rule 4 says to shape every one of them for upstream
submission. So the policy was checked before writing any.

## The finding

**Wine prohibits LLM-generated code.** From Wine's Clean Room Guidelines:

> Don't use an LLM tool to generate code. There's no guarantee that the training
> material of that LLM respects our Clean Room Guidelines, or that its output is
> compatible with the LGPL.

Source: `https://gitlab.winehq.org/wine/wine/-/wikis/Clean-Room-Guidelines`

Two distinct objections are being made, and they have different consequences:

1. **Clean room.** Wine cannot verify that an LLM's training material respected
   their clean-room rules. This is the same concern that governs every other
   contribution route, applied to a source they cannot audit.
2. **LGPL compatibility.** Wine is not confident LLM output can be licensed
   LGPL at all.

### Verification status

- Corroborated by the CHAOSS AI-alignment working group's policy survey
  ([chaoss/wg-ai-alignment#108](https://github.com/chaoss/wg-ai-alignment/issues/108)),
  which quotes the same sentence and cites the same URL.
- **The primary source could not be read directly.** `gitlab.winehq.org` is
  behind Anubis bot protection and returns Access Denied to automated fetches.
- The only recent wine-devel thread touching AI ("Solving the slow review
  problem with AI") is satire, not a policy change. No evidence the policy is
  being revised.

**David should confirm the wording from the wiki himself before relying on it.**
A human browser can read what an automated fetch cannot, and a policy this
consequential should not rest on second-hand quotation.

## What this means

**Rule 4 is unachievable for AI-written Wine code.** "Shape every Wine patch for
upstream submission" and "the patch was written by an LLM" cannot both hold.
There is no version of careful, small, well-tested AI-written patches that
becomes acceptable — the objection is to the provenance, not the quality.

It also draws a line through S2 specifically. The
[S2 analysis](../s2-wineserver-analysis.md) concluded "patch set, not a rewrite",
and identified six changes inside `server/`. **Every one of those is Wine source
code**, so every one falls under this policy.

Note that objection 2 is not only about upstream acceptance. If LLM output's
LGPL compatibility is genuinely uncertain, that uncertainty attaches to code we
ship *downstream* in `wine-sg` too — we would be distributing a derivative of an
LGPL work. That is a question for David with legal advice, not one to resolve by
reasoning about it here.

### Nothing has been contaminated yet

Worth stating plainly, because it is the useful part of having checked early:

- `wine-sg` contains **no AI-written Wine code**. Its four patches are carried
  unmodified from Debian's packaging with their original authors' DEP-3 headers.
- Everything else in `wine-sg` — `build.sh`, `debian/`, the WoW64 gate — is
  build machinery, not Wine source.
- The S2 work done so far is a source *analysis* and a *gate*. Reading Wine to
  understand it, and writing tests that exercise it from outside, are not
  covered by a policy about generating Wine code.

## Options

### A. A human writes the Wine patches

The AI does analysis, gates, harnesses, specifications and everything outside
the Wine tree; a human writes the code that lands in `server/`. Upstreaming stays
open. Costs: the Wine work goes at human pace, and S2's six changes are not
small.

### B. Permanent downstream fork, never submitted

Write the patches however, keep them in `wine-sg` forever. Contradicts rule 4,
forfeits upstream review, and leaves objection 2's licensing question unresolved
while we distribute.

### C. Drop the multi-user ambition

Rescope S2 away from patching Wine. This is not really available — the S2
analysis shows the machine-level wineserver *is* Wine changes.

## Decision

**B. We do not submit patches upstream.** Wine changes stay downstream in
`wine-sg`, permanently.

David's call, made after reading the finding: *"Given Wine's policy we will
simply not write upstream patches."*

This resolves the question the policy actually poses to us. Wine's rule governs
what Wine accepts; if we are not asking them to accept anything, it does not
constrain what we write. So **Wine patches may be written here**, and S2's
Wine-side work is unblocked.

### What this amends

**Brief rule 4 is amended by this decision.** It said:

> Shape every Wine patch for upstream submission (small, tested, one concern).

The *submission* half is now void — there will be no submission. **The
engineering half is kept anyway**, deliberately: small, tested,
one-concern patches are how a downstream series stays rebasable across upstream
releases. A sprawling patch that touches six things at once is painful to
forward-port whether or not anyone upstream ever reads it. So the discipline
survives its original justification.

`wine-sg`'s existing split still holds and still matters:

- `patches/fixes/` — carried from elsewhere, original authorship intact
- `patches/sg/` — ours

The distinction is no longer "what we owe upstream" but "what we wrote versus
what we inherited", which is still worth knowing at a glance when a rebase
conflicts.

### What this does *not* resolve

Wine raised two objections, and this decision answers only the first.

Objection 2 — that LLM output may not be LGPL-compatible at all — is about
**distribution**, not submission. We distribute `wine-sg`, which is a derivative
of an LGPL work. Declining to upstream does not touch that question; it is the
same question whether the patches go to Wine or only to our own users.

I am not able to resolve it, and reasoning about it in an ADR would be worth
nothing. **It needs actual legal advice.** Flagged, not settled — see
*Open question for David* below.

**Answered by David, 2026-09-22:** he sees no legal issue in distributing
modified versions of Wine; the only constraint is that upstream will not accept
the patches. `wine-sg` is published.

## Consequences

- **S2's Wine-side work proceeds**, downstream. Changes 1 and 2 from the
  analysis — machine-wide server directory and `SO_PEERCRED` authentication —
  are the immediate next step.
- **We own these patches forever.** No upstream review, no upstream maintenance,
  and every upstream release is a rebase we do ourselves. That is the price of
  the decision and it should be budgeted rather than discovered.
- **`sg-testlab`'s winetest baseline becomes more important, not less.**
  Upstream review was the thing that would have caught mistakes in these patches.
  With that gone, the baseline is the only safety net, and any `wine-sg` patch
  must not regress it.
- **Patches stay small and one-concern anyway.** Not for upstream's benefit —
  for the rebase.
- **S1 (`wdf-wine`) was never affected.** It ports Microsoft's MIT-licensed WDF
  into a separate repo: not Wine source, and MIT carries none of the LGPL
  concern.
- **The rest of the project is unaffected.** `sg-image`, `sg-session`,
  `sg-testlab`, `gpo-agent`, `prt-broker`, `sg-compositor`, `sg-greeter` are our
  own AGPL code under our own policy.

## Open question for David

Objection 2 — whether LLM output can be LGPL at all — bears on more than
upstreaming. If taken seriously it affects anything we distribute that derives
from an LGPL work. **That needs a decision informed by actual legal advice**,
and this ADR should be updated with the answer rather than left implying the
question was settled here.
