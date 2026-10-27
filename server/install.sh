#!/bin/sh
# Install the project server's own jobs on freesoft.page (run there as root, from this folder).
# sg-winget-latest: the SG Store's list of winget's newest versions, /winget/latest.tsv, hourly.
set -e
cd "$(dirname "$0")"
id sg-winget >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin sg-winget
install -d -o sg-winget -g sg-winget -m 755 /srv/www/winget
install -m 755 sg-winget-latest /usr/local/bin/sg-winget-latest
install -m 644 sg-winget-latest.service sg-winget-latest.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now sg-winget-latest.timer
systemctl start sg-winget-latest.service
