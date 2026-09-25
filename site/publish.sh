#!/bin/bash
# Build the website and put it on https://freesoft.page, leaving /apt and /iso
# (published by sg-image) alone.
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
rsync -a --delete --exclude /apt/ --exclude /iso/ -e "ssh -i ${SG_SITE_SSH_KEY:-$HOME/.ssh/sg} -o BatchMode=yes" \
    "$OUT/" "$HOST:$DIR/"
echo "live at https://freesoft.page/"
