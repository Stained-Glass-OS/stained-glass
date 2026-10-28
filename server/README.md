# Project server jobs (freesoft.page)

- `sg-winget-latest` (+ `.service`, `.timer`): every hour, every winget package's newest
  version from winget's own index (its CDN's `source2.msix`), written to
  `/srv/www/winget/latest.tsv` (`id<TAB>version`). The SG Store reads it once per run
  instead of asking GitHub's API per app (60 requests an hour per address).
  Also `/srv/www/winget/index.tsv` (`id<TAB>version<TAB>hash`): the first 8 hex digits of
  each package's hash in that index, its folder on winget's CDN
  (`packages/<id>/<hash>/versionData.mszyml`). The Store reads the manifests there, as
  winget does, checked against the SHA-256 winget's version data gives, instead of
  raw.githubusercontent.com (429 to a busy address: 67 of 120 in a row from this server).

Install or update: copy this folder to the server and run `sh install.sh` there as root.
`site/publish.sh` excludes `/winget/` so a site publish keeps it.
