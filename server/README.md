# Project server jobs (freesoft.page)

- `sg-winget-latest` (+ `.service`, `.timer`): every hour, every winget package's newest
  version from winget's own index (its CDN's `source2.msix`), written to
  `/srv/www/winget/latest.tsv` (`id<TAB>version`). The SG Store reads it once per run
  instead of asking GitHub's API per app (60 requests an hour per address).

Install or update: copy this folder to the server and run `sh install.sh` there as root.
`site/publish.sh` excludes `/winget/` so a site publish keeps it.
