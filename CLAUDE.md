# stained-glass — meta repo

Docs only. No code ships from here.

## What lives here

- `docs/BRIEF.md` — the project brief. **Read it before doing anything in any
  Stained Glass repo.** It is the source of truth for scope, rules and phases.
- `ROADMAP.md` — phases and their gates.
- `docs/decisions/` — ADRs, numbered `NNNN-title.md`.
- `docs/multiuser-debt.md` — the running list of single-user assumptions.

## Working here

There is no build and no test. The gate on this repo is review.

**Writing an ADR.** Copy `docs/decisions/0000-template.md` to the next free
number. An ADR without evidence is not an ADR — record what you ran and what it
printed, and when you reject an option, **say what broke**. A rejected option
with no recorded failure gets re-litigated six months later.

**Adding debt.** When you write code elsewhere that assumes a single user, add
it to `docs/multiuser-debt.md` with a `D<n>` tag, and put a
`MULTIUSER-DEBT: D<n>` comment at the place in the code that incurs it. The list
is only useful if it is complete.

## Hard rules, in short

Full versions in `docs/BRIEF.md` §2. The ones easiest to violate by accident:

- **Clean room.** No leaked Microsoft source. No disassembling or decompiling
  Microsoft binaries. Black-box testing against real Windows is fine. Microsoft's
  own open source (e.g. MIT-licensed WDF) is fine but stays in its own repo,
  never inside the Wine tree.
- **Test domains only.** `SGTEST.LAN` and a developer Entra tenant. Never a
  production domain or a real credential. Never commit secrets — including test
  ssh keys, which are generated at build time, not checked in.
- **No gate, no merge.** A thing is not working until a script says so with an
  exit code.
- **Don't fork Wine until a patch forces it.**

## Before you write a Wine patch: don't

**Wine prohibits LLM-generated code.** From their Clean Room Guidelines: *"Don't
use an LLM tool to generate code. There's no guarantee that the training
material of that LLM respects our Clean Room Guidelines, or that its output is
compatible with the LGPL."*

The operating rule, until David says otherwise:

> **No AI-written code goes into Wine's tree, including `wine-sg/patches/sg/`.**

This is not about patch quality. The objection is to provenance, so careful
small well-tested patches do not become acceptable. Reading Wine to understand
it, and writing gates that exercise it from outside, are fine and are not
covered.

Full reasoning, including what it does to S2:
[ADR 0006](docs/decisions/0006-wine-llm-contribution-policy.md).

## Licensing, in one paragraph

New code is **AGPL-3.0-or-later** ([ADR 0004](docs/decisions/0004-licensing.md)).
The exception that will bite you: **anything bound for upstream Wine must be
LGPL-2.1+**, because AGPL-3.0 cannot be incorporated into an LGPL-2.1+ project.
A Wine patch written in an AGPL repo can never be submitted upstream, and you
will not discover that until you try. Wine-bound work goes in `wine-sg`.

## Decisions that are David's

Marked **[DAVID]** in the brief. Do not decide these unilaterally: creating
repos beyond the current phase, and anything that turns `wine-sg` into a hard
fork. Ask, and wait.

Licenses are **settled**: AGPL-3.0-or-later for new code, upstream's license for
forks and ports. See ADR 0004.
