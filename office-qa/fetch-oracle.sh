#!/bin/sh
# Fetch + verify the ONLYOFFICE DocumentBuilder QA oracle into a git-ignored
# dev/QA path. NEVER ships. See README.md and ADR 0016.
set -eu
VER=8.2.0-143
URL=https://download.onlyoffice.com/install/desktop/docbuilder/linux/onlyoffice-documentbuilder_amd64.deb
SHA=5dd570200cb72db9f59a4e31dc7ad8af5d2de979c194f45f4fc2a7785cf67d70
DEST=${1:-$(dirname "$0")/oracle}
mkdir -p "$DEST"
deb="$DEST/docbuilder.deb"
[ -f "$deb" ] || curl -sSL -o "$deb" "$URL"
echo "$SHA  $deb" | sha256sum -c - || { echo "SHA mismatch -- refusing to use"; exit 1; }
dpkg-deb -x "$deb" "$DEST/extracted"
bin="$DEST/extracted/opt/onlyoffice/documentbuilder"
echo "oracle $VER ready at: $bin"
echo "run: (cd '$bin' && LD_LIBRARY_PATH=. ./docbuilder script.docbuilder)"
