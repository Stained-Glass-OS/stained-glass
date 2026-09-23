# Package repository: size, hosting, and what blocks publishing

Backlog items F1/F2 ([vision-backlog.md](vision-backlog.md)). David's question:
*host the `.deb` repository on GitHub Pages if our packages fit, otherwise a
VPS.* Measured 2026-09-22.

## What a release weighs

| Package | Size | Notes |
|---|---:|---|
| `wine-sg` | 55.6 MB | Both architectures, stripped (1.5 GB unstripped) |
| `sg-session` | 0.25 MB | Scripts, greeter, lock service |
| `sg-shell` | 0.06 MB | Start menu, theme defaults |
| `sg-compositor` | 0.02 MB | |
| DXVK + VKD3D-Proton | 22 MB | Staged into the image today; not yet a `.deb` |
| PowerShell 7.6.6 | 101 MB | Upstream zip; staged, not yet a `.deb` |
| CPython 3.14.7 | 15 MB | NuGet package; staged, not yet a `.deb` |
| **Total, one version of everything** | **~195 MB** | |

Only `wine-sg` and the three small packages are `.deb`s today. For `apt
upgrade` to update Direct3D, PowerShell and Python, they need packaging too —
thin `.deb`s wrapping the pinned upstream builds.

## Does it fit on GitHub Pages?

GitHub's published limits for Pages: a **1 GB** site, a **100 GB/month** soft
bandwidth limit, and — for a site built from a git branch — git's **100 MB per
file** limit. Deploying through GitHub Actions avoids the git file limit.

- **Storage: yes.** One version of everything is ~195 MB, so a repository
  that keeps only the current version of each package (as `reprepro` does by
  default) fits with room to spare. Keeping a few old `wine-sg` versions for
  rollback still fits.
- **Per-file: only via Actions.** The PowerShell package would be ~100 MB, at
  git's limit. Deploy the repository as a Pages artifact from a workflow, not
  from a branch.
- **Bandwidth: this is what runs out.** A fresh machine pulls up to ~195 MB and
  each `wine-sg` update ~56 MB. Rough monthly transfer, two `wine-sg` updates a
  month:

  | Machines | New installs + updates | vs 100 GB |
  |---:|---:|---|
  | 50 | ~6 GB | fine |
  | 300 | ~34 GB + installs | fine |
  | 1,000 | ~110 GB + installs | over |

**Recommendation:** start on GitHub Pages (via Actions) for testers and early
fleets. Move to a VPS, or a VPS fronted by a CDN, before a deployment
approaches a few hundred machines. The client side does not change: machines
point at a URL, and the URL can move. Using a hostname we control from day one
(a CNAME to Pages now, a VPS later) keeps that move invisible to machines
already in the field.

## Decisions

**Decided by David, 2026-09-22:**

- **Publish.** Distributing modified Wine is fine under its licence; the only
  constraint is that upstream will not accept the patches (ADR 0006).
- **GitHub Pages first**, migrating to a VPS later.

**Also decided, 2026-09-22:**

- **The signing key is generated on the build machine** and kept in
  `~/.sgkeys/` there -- never in any repository. The repository is signed where
  the key is and then pushed, so no CI system holds the key.
- **The address is GitHub's own**, `https://stained-glass-os.github.io/apt/`,
  for now. Moving to a VPS later means shipping machines a new source first.
- **The repository lives in `Stained-Glass-OS/apt`**, published from a single
  orphan commit replaced on every publish, so `wine-sg`'s ~56 MB per release
  does not accumulate in git history.

## What can be built now without publishing

- `.deb` packaging for the D3D layers, PowerShell and Python payloads.
- A `make repo` target in `sg-image` that builds a signed repository locally
  from the staged `.deb`s with a throwaway key, and a gate that boots the image
  pointed at it and runs `apt update && apt upgrade` successfully. This proves
  the upgrade path end to end without distributing anything.
- The image's apt sources: Debian and its mirror, plus ours, with our key
  pinned to our repository only (`Signed-By`), so it cannot sign packages that
  replace Debian's.
