#!/bin/bash
# Build the website and put it on https://freesoft.page, leaving /apt and /iso
# (published by sg-image), /addons (the Wine Mono builds sg-image pins, uploaded by
# hand -- a publish without this exclude deleted them, 2026-10-03: CI 404) and /reports (the Debug Reports, which the report
# receiver writes: sg-image server/reports) alone.
#
#   site/publish.sh
#
# SPDX-License-Identifier: AGPL-3.0-or-later
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
OUT="$(dirname "$HERE")/build/site"
HOST="${SG_SITE_HOST:-root@freesoft.page}"
DIR="${SG_SITE_DIR:-/srv/www}"
python3 "$HERE/build.py" "$OUT"
rsync -a --delete --exclude /apt/ --exclude /iso/ --exclude /reports/ --exclude /addons/ -e "ssh -i ${SG_SITE_SSH_KEY:-$HOME/.ssh/sg} -o BatchMode=yes" \
    "$OUT/" "$HOST:$DIR/"
echo "live at https://freesoft.page/"
