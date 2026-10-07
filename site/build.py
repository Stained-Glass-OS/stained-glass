#!/usr/bin/env python3
"""Build the project website (https://freesoft.page) from this repo.

    site/build.py OUT_DIR

The front page is site/index.md; every docs/*.md and docs/decisions/*.md is
rendered to OUT_DIR/docs/. /apt/ and /iso/ on the server are not ours to
touch -- site/publish.sh rsyncs everything else.

SPDX-License-Identifier: AGPL-3.0-or-later
"""
import datetime
import html
import os
import re
import shutil
import subprocess
import sys

import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "build", "site")
GITHUB = "https://github.com/Stained-Glass-OS"
SITE = "https://freesoft.page/"
# /.well-known/security.txt (RFC 9116) needs a real contact -- the owner's
# choice, never guessed (site review 2026-10-07). Unset: no security.txt.
SECURITY_CONTACT = os.environ.get("SG_SITE_SECURITY_CONTACT", "")
NOW = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)


def lastmod(*paths):
    """The newest commit date of the sources, for the sitemap (the build's
    date when git has none)."""
    try:
        out = subprocess.run(["git", "-C", REPO, "log", "-1", "--format=%cI", "--", *paths],
                             capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        out = ""
    return out or NOW.isoformat()

CSS = """
:root {
  --bg: #faf8fc; --fg: #1d1a22; --muted: #5d5668; --card: #ffffff;
  --line: #e4dcee; --accent: #7a2fc0; --accent-2: #0f8a86; --code: #f1ecf7;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #15121a; --fg: #ece8f1; --muted: #a79fb3; --card: #1e1a25;
    --line: #342c40; --accent: #b784ef; --accent-2: #4cc7c1; --code: #262030;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg);
  font: 16px/1.6 Inter, "Segoe UI", system-ui, sans-serif; }
a { color: var(--accent); }
header.top { border-bottom: 1px solid var(--line); background: var(--card); }
header.top .wrap { display: flex; align-items: center; gap: 20px; padding-top: 12px; padding-bottom: 12px; }
header.top .brand { font-weight: 700; color: var(--fg); text-decoration: none; display: flex; gap: 10px; align-items: center; }
header.top nav { display: flex; gap: 16px; flex-wrap: wrap; }
header.top nav a { color: var(--muted); text-decoration: none; }
header.top nav a:hover { color: var(--accent); }
.wrap { max-width: 980px; margin: 0 auto; padding: 0 16px; }
main { padding: 28px 0 60px; }
.hero h1 { font-size: 2.4rem; line-height: 1.15; margin: 8px 0 12px; }
.hero p.lead { font-size: 1.15rem; color: var(--muted); max-width: 720px; }
.buttons { display: flex; gap: 12px; flex-wrap: wrap; margin: 20px 0 8px; }
.btn { display: inline-block; padding: 10px 18px; border-radius: 6px; text-decoration: none;
  background: var(--accent); color: #fff; font-weight: 600; }
.btn.secondary { background: transparent; color: var(--accent); border: 1px solid var(--accent); }
img.shot { width: 100%; height: auto; border-radius: 8px; border: 1px solid var(--line); }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 16px 18px; }
.card h3 { margin-top: 0; }
pre, code { font-family: "Cascadia Mono", ui-monospace, monospace; font-size: 0.92em; }
pre { background: var(--code); padding: 12px 14px; border-radius: 6px; overflow-x: auto; }
code { background: var(--code); padding: 1px 4px; border-radius: 4px; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; width: 100%; display: block; overflow-x: auto; }
th, td { border: 1px solid var(--line); padding: 6px 10px; text-align: left; vertical-align: top; }
blockquote { border-left: 3px solid var(--accent); margin: 0; padding: 2px 16px; color: var(--muted); }
footer { border-top: 1px solid var(--line); color: var(--muted); font-size: 0.9rem; padding: 18px 0 40px; }
.doclist li { margin: 4px 0; }
.notice { border: 1px solid var(--accent); border-left-width: 4px; border-radius: 6px; padding: 4px 16px; margin: 12px 0 20px; background: var(--card); }
main, .wrap { min-width: 0; }
pre { max-width: 100%; }
@media (max-width: 600px) {
  header.top .wrap { flex-direction: column; align-items: flex-start; gap: 6px; }
  header.top nav { gap: 12px; }
  .hero h1 { font-size: 1.9rem; }
  .grid { grid-template-columns: 1fr; }
}
"""

# The Start button's mark (sg-shell src/sg-taskbar.c draw_start_glyph): four
# diamond tiles -- squares on their points, half-diagonal 6 -- centred 8 px
# from the middle at the compass points: purple top, magenta right, amber
# bottom, turquoise left.
def _tile(cx, cy, fill, h=6):
    return (f'<path d="M{cx} {cy - h} {cx + h} {cy} {cx} {cy + h} {cx - h} {cy}Z" '
            f'fill="{fill}"/>')


MARK = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 28 28">'
        + _tile(14, 6, "#7B2FBE") + _tile(22, 14, "#C42E8E")
        + _tile(14, 22, "#E8A200") + _tile(6, 14, "#12B5B0") + '</svg>')
LOGO = MARK.replace('<svg ', '<svg width="24" height="24" aria-hidden="true" ', 1)


def page(title, body, depth=0):
    up = "../" * depth
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{up}style.css">
<link rel="icon" type="image/svg+xml" href="{up}logo.svg">
</head><body>
<header class="top"><div class="wrap">
<a class="brand" href="{up}index.html">{LOGO}Stained Glass OS</a>
<nav><a href="{up}index.html#download">Download</a><a href="{up}docs/index.html">Docs</a>
<a href="{up}apt/">Packages</a><a href="{up}iso/">ISOs</a><a href="{up}reports/">Debug Reports</a><a href="{GITHUB}">Source</a></nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">Stained Glass OS is free software: AGPL-3.0-or-later for new code,
upstream licences for Wine and Debian. Not affiliated with Microsoft; Windows is a trademark of
Microsoft Corporation.<br>"Set time zone automatically" uses <a href="https://db-ip.com">IP Geolocation by DB-IP</a>
and <a href="https://www.geonames.org">GeoNames</a> data (CC BY 4.0).<br>
<a href="{up}docs/ai-notes.html">AI architectural notes</a></div></footer>
</body></html>
"""


def md(text):
    return markdown.markdown(text, extensions=["tables", "fenced_code", "toc", "sane_lists", "attr_list", "md_in_html"])


def title_of(text, fallback):
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else fallback


def fix_links(body):
    # docs link to each other as foo.md; the site serves foo.html
    return re.sub(r'href="([^":#]+)\.md(#[^"]*)?"', r'href="\1.html\2"', body)


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "docs", "decisions"))
    with open(os.path.join(OUT, "style.css"), "w") as f:
        f.write(CSS)
    with open(os.path.join(OUT, "logo.svg"), "w") as f:
        f.write(MARK)
    shutil.copytree(os.path.join(HERE, "img"), os.path.join(OUT, "img"))
    if os.path.isdir(os.path.join(REPO, "docs", "images")):
        shutil.copytree(os.path.join(REPO, "docs", "images"), os.path.join(OUT, "docs", "images"))

    with open(os.path.join(HERE, "index.md")) as f:
        front = f.read()
    with open(os.path.join(OUT, "index.html"), "w") as f:
        f.write(page("Stained Glass OS", fix_links(md(front))))
    # the sitemap: every page rendered here (not /apt/, /iso/ or /reports/)
    pages = [("", lastmod(os.path.join(HERE, "index.md")))]

    entries = {"docs": [], "decisions": [], "guide": []}
    # the guide (guide/*.md): written for people using and running the
    # system, ahead of the project's own notes
    os.makedirs(os.path.join(OUT, "docs", "guide"), exist_ok=True)
    for sub, depth, key in (("guide", 2, "guide"), ("docs", 1, "docs"), ("docs/decisions", 2, "decisions")):
        src = os.path.join(REPO, sub)
        for name in sorted(os.listdir(src)):
            if not name.endswith(".md") or name.startswith("0000-"):
                continue
            with open(os.path.join(src, name)) as f:
                text = f.read()
            title = title_of(text, name[:-3])
            outname = name[:-3] + ".html"
            outdir = os.path.join(OUT, "docs", "guide") if key == "guide" else os.path.join(OUT, sub)
            with open(os.path.join(outdir, outname), "w") as f:
                f.write(page(title + " -- Stained Glass OS", fix_links(md(text)), depth))
            entries[key].append((outname, title))
            rel = ("docs/guide/" if key == "guide" else sub + "/") + outname
            pages.append((rel, lastmod(os.path.join(src, name))))

    guide = "\n".join(f'<li><a href="guide/{n}">{html.escape(t)}</a></li>' for n, t in entries["guide"])
    items = "\n".join(f'<li><a href="{n}">{html.escape(t)}</a></li>' for n, t in entries["docs"])
    decs = "\n".join(f'<li><a href="decisions/{n}">{html.escape(t)}</a></li>' for n, t in entries["decisions"])
    # People read the guide. The project's working notes and decision
    # records -- terse, written for the AI agents that build Stained Glass OS
    # and full of the owner's individual choices -- are on a page of their
    # own, linked from here and every page's footer (2026-10-06).
    body = (f"<h1>Documentation</h1>"
            f'<h2>Guide</h2><p>Using, running and supporting Stained Glass, and how it fits together.</p>'
            f'<ul class="doclist">{guide}</ul>'
            f'<p>For contributors and AI agents: the project\'s working notes and '
            f'decision records are in the <a href="ai-notes.html">AI architectural notes</a>.</p>')
    with open(os.path.join(OUT, "docs", "index.html"), "w") as f:
        f.write(page("Documentation -- Stained Glass OS", body, 1))
    notes = (f"<h1>AI architectural notes</h1>"
             f"<p>The project's working documents and architecture decision records, kept for the AI "
             f"agents that build Stained Glass OS and for contributors. They record decisions tersely, "
             f"as working notes, and are not user documentation: for using the system, see the "
             f'<a href="index.html">guide</a>. Rendered from the '
             f'<a href="{GITHUB}/stained-glass">stained-glass</a> repository; each code repository\'s '
             f"<code>CLAUDE.md</code> has the engineering detail.</p>"
             f'<h2>Project notes</h2><ul class="doclist">{items}</ul>'
             f'<h2>Architecture decisions</h2><ul class="doclist">{decs}</ul>')
    with open(os.path.join(OUT, "docs", "ai-notes.html"), "w") as f:
        f.write(page("AI architectural notes -- Stained Glass OS", notes, 1))
    every = lastmod(os.path.join(REPO, "guide"), os.path.join(REPO, "docs"))
    pages += [("docs/index.html", every), ("docs/ai-notes.html", every)]
    write_crawl_files(pages)
    print("site built in", OUT)


def write_crawl_files(pages):
    """robots.txt (every crawler welcome: owner, 2026-10-07), sitemap.xml and
    /.well-known/security.txt -- built here, as site/publish.sh's rsync
    --delete removes anything put on the server by hand."""
    with open(os.path.join(OUT, "robots.txt"), "w") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE}sitemap.xml\n")
    urls = "".join(f"<url><loc>{html.escape(SITE + rel)}</loc><lastmod>{mod}</lastmod></url>\n"
                   for rel, mod in sorted(pages))
    with open(os.path.join(OUT, "sitemap.xml"), "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                f"{urls}</urlset>\n")
    if not SECURITY_CONTACT:
        print("note: no SG_SITE_SECURITY_CONTACT, so no security.txt", file=sys.stderr)
        return
    # Expires at most a year out (RFC 9116); 180 days, renewed by every publish
    expires = (NOW + datetime.timedelta(days=180)).strftime("%Y-%m-%dT%H:%M:%SZ")
    os.makedirs(os.path.join(OUT, ".well-known"), exist_ok=True)
    with open(os.path.join(OUT, ".well-known", "security.txt"), "w") as f:
        f.write(f"Contact: {SECURITY_CONTACT}\nExpires: {expires}\nPreferred-Languages: en\n"
                f"Canonical: {SITE}.well-known/security.txt\n")


if __name__ == "__main__":
    main()
