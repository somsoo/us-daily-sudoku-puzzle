"""Daily Sudoku Puzzle (us-daily-sudoku-puzzle.enjoy-onepage.com) page builder.

index.html is the source. This script copies it into Today's Sudoku (daily.html) and the level pages (level/*.html),
swapping only the <!-- PAGE:HEAD/HEADER/CONTENT START/END --> blocks and the <!-- PAGE:PRESET --> marker,
then rewrites sitemap.xml and rss.xml from the real files.

Usage (from the repo root):  python _build/build_pages.py
- Game code, ads and styles are copied from index.html unchanged: fix the game in index.html, then re-run.
- The folder name starts with '_' so GitHub Pages (Jekyll) does not publish this script.
- Korean twin: sudokuportal.enjoy-onepage.com uses the same paths; every page carries reciprocal hreflang links.
"""
import datetime as dt
import email.utils
import html
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://us-daily-sudoku-puzzle.enjoy-onepage.com"
KO_SITE = "https://sudokuportal.enjoy-onepage.com"
SITE_NAME = "Daily Sudoku Puzzle"
TITLE_MAX, DESC_MAX = 60, 160

PAGES = [
    {
        "path": "daily.html", "preset": {"mode": "daily", "level": "normal"},
        "title": "Today's Sudoku | Free Daily Sudoku Puzzle & Streaks",
        "desc": "One new sudoku every day, the same for everyone on the same date. Pick Easy to Expert, keep a daily streak and share your time.",
        "h1": "Today's Sudoku", "sub": "A new puzzle every day at midnight on your device · 4 levels",
        "intro_h2": "📅 What is Today's Sudoku?",
        "intro": "Today's Sudoku is one puzzle per day, generated from the date, so everyone who plays on the same calendar date "
                 "gets the same grid. It changes at midnight on your device's clock. Each level has its own daily puzzle: "
                 "switch levels with the menu above the board.",
        "blocks": [
            ("How your streak works", [
                "Finish at least one Today's Sudoku in a day and that day counts.",
                "Solve again the next day and your streak grows by one. Skip a day and it starts over.",
                "Games where you press Show solution are not recorded.",
                "Stats live only in this browser, so they do not carry over to another device or browser.",
            ]),
            ("Race a friend on the same puzzle", [
                "When you finish, tap 📤 Share your result to send your time with a link to the same puzzle.",
                "The link only holds the date and the level, never the answer.",
                "Past days can be replayed from a link such as ?date=2026-09-01&level=hard.",
            ]),
        ],
        "faq": [
            ("When does Today's Sudoku change?", "At midnight on your device's clock. It follows your device's date, so it changes with your local time zone."),
            ("Can I play it more than once a day?", "Yes. You can replay the same puzzle as often as you like, and your best time is kept on this device."),
            ("How is my streak counted?", "By solving Today's Sudoku on consecutive days. Pressing Show solution does not count as a solve."),
        ],
    },
    {
        "path": "level/easy.html", "preset": {"mode": "free", "level": "easy"},
        "title": "Easy Sudoku | Free Beginner Sudoku Puzzles, Unlimited",
        "desc": "Easy sudoku with 36-40 empty cells that you can solve with singles only. Unlimited free puzzles for beginners, no sign-up.",
        "h1": "Easy Sudoku", "sub": "36-40 empty cells · solvable with singles · great for beginners",
        "intro_h2": "🌱 Who Easy Sudoku is for",
        "intro": "Easy puzzles suit first-timers, returning players and anyone who wants a relaxing few minutes. Every puzzle has "
                 "exactly one solution and can be finished with singles alone, so you never need to guess.",
        "blocks": [
            ("A simple order for your first puzzles", [
                "Start with the row, column or box that has the most numbers filled in. If only one cell is empty, place the missing number.",
                "Pick one number and scan the whole grid. If a row already has a 5, no other cell in that row can be 5.",
                "Pencil in candidates for tricky cells. When you place a number, matching notes nearby are cleared for you.",
                "If something looks wrong, use Check mistakes to show wrong cells in red.",
            ]),
        ],
        "faq": [
            ("What is the difference between Easy and Medium?", "Both can be solved with singles only. Medium has more empty cells (45-50), so you need more hidden singles and longer scans."),
            ("Can kids play Easy Sudoku?", "Yes, if they know the numbers 1 to 9 and the rule that a number cannot repeat in a row, column or box. Easy is a good place to start."),
        ],
    },
    {
        "path": "level/normal.html", "preset": {"mode": "free", "level": "normal"},
        "title": "Medium Sudoku | Free Intermediate Sudoku, Unlimited",
        "desc": "Medium sudoku with 45-50 empty cells. Practice hidden singles and pencil notes with unlimited free puzzles in your browser.",
        "h1": "Medium Sudoku", "sub": "45-50 empty cells · practice hidden singles and notes",
        "intro_h2": "🙂 What changes at Medium",
        "intro": "Medium is the next step once the rules feel natural. It can still be solved with singles, but with more empty "
                 "cells you will rely on hidden singles and careful notes.",
        "blocks": [
            ("When you get stuck at Medium", [
                "Hidden single: inside one box, row or column, look for a number that has only one possible cell.",
                "Cross-check: scan a row and a column at the same time to rule out candidates.",
                "Keep notes light: note cells with two or three candidates instead of filling every cell.",
                "Track your progress: your best time for each level is saved on this device.",
            ]),
        ],
        "faq": [
            ("Is it normal to get stuck at Medium?", "Yes. With more empty cells, the next single takes longer to find. Scan box by box and a hidden single will turn up."),
            ("Can I replay the same puzzle?", "Yes. The link in your address bar includes the puzzle number, so opening it again gives you the same grid."),
        ],
    },
    {
        "path": "level/hard.html", "preset": {"mode": "free", "level": "hard"},
        "title": "Hard Sudoku | Free Advanced Sudoku Puzzles, Unlimited",
        "desc": "Hard sudoku with 51-55 empty cells. Some need candidate techniques such as naked pairs and pointing. Unlimited and free.",
        "h1": "Hard Sudoku", "sub": "51-55 empty cells · may need candidate techniques",
        "intro_h2": "🔥 How to approach Hard Sudoku",
        "intro": "Hard puzzles have 51-55 empty cells, and singles alone may stall. That is when pencil notes and candidate "
                 "techniques come in. Every puzzle still has exactly one solution.",
        "blocks": [
            ("Techniques for Hard", [
                "Naked pair: two cells in the same row, column or box share the same two candidates, so remove those numbers from the unit's other cells.",
                "Pointing: if a number's candidates inside a box all sit in one row, remove that number from the rest of the row.",
                "Box-line reduction: if a number's candidates in a row all sit inside one box, remove it from the rest of that box.",
                "Each time you place a number, matching notes in its row, column and box are cleared automatically.",
            ]),
        ],
        "faq": [
            ("What is the difference between Hard and Expert?", "Expert has 56 or more empty cells and fewer givens, so you usually need pairs and patterns such as X-Wing."),
            ("Should I guess?", "You do not need to: every puzzle has one solution you can reach with logic, and a wrong guess is hard to undo."),
        ],
    },
    {
        "path": "level/expert.html", "preset": {"mode": "free", "level": "expert"},
        "title": "Expert Sudoku | Hardest Free Sudoku Puzzles",
        "desc": "Expert sudoku with 56+ empty cells and about 25 givens or fewer. X-Wing and hidden pairs may be needed. Free and unlimited.",
        "h1": "Expert Sudoku", "sub": "56+ empty cells · about 25 givens or fewer · the hardest level",
        "intro_h2": "🧠 Taking on Expert Sudoku",
        "intro": "Expert is the hardest level here. With so few givens, fill in candidates first and work through them with "
                 "patterns. Every puzzle has exactly one solution.",
        "blocks": [
            ("Expert strategy", [
                "Start by pencilling candidates into every empty cell. At Expert, your notes are the map.",
                "Hidden pair: when two numbers can only go in the same two cells of a unit, remove every other candidate from those cells.",
                "X-Wing: if a number's candidates in two rows sit in the same two columns, remove it from those columns in the other rows.",
                "Stuck? Look again around the last number you placed. One placement often unlocks the next.",
            ]),
        ],
        "faq": [
            ("How many givens do Expert puzzles have?", "Usually about 23 to 25."),
            ("It is too hard. What can I do?", "Use Check mistakes to find wrong cells, or practice the techniques on Hard first."),
        ],
    },
]

LINKS = [
    ("/daily.html", "📅 Today's Sudoku"), ("/level/easy.html", "🌱 Easy Sudoku"), ("/level/normal.html", "🙂 Medium Sudoku"),
    ("/level/hard.html", "🔥 Hard Sudoku"), ("/level/expert.html", "🧠 Expert Sudoku"), ("/", "🏠 Sudoku home"),
]


def esc(s):
    return html.escape(s, quote=True)


def page_url(path, site=SITE):
    return f"{site}/{path}"


def head_block(p):
    url, ko = page_url(p["path"]), page_url(p["path"], KO_SITE)
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebApplication", "@id": url + "#webapp", "name": p["h1"], "url": url, "applicationCategory": "GameApplication",
         "operatingSystem": "All", "inLanguage": "en", "description": p["desc"], "image": f"{SITE}/og-image.png",
         "isPartOf": {"@type": "WebSite", "name": SITE_NAME, "url": SITE + "/"},
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}},
        {"@type": "FAQPage", "@id": url + "#faq", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in p["faq"]]},
    ]}
    t, d = esc(p["title"]), esc(p["desc"])
    return "\n".join([
        "<!-- PAGE:HEAD START -->",
        f"<title>{html.escape(p['title'], quote=False)}</title>",
        f'<meta name="description" content="{d}">',
        '<meta name="robots" content="index, follow">',
        f'<link rel="canonical" href="{url}">',
        f'<link rel="alternate" hreflang="en" href="{url}">',
        f'<link rel="alternate" hreflang="ko" href="{ko}">',
        f'<link rel="alternate" hreflang="x-default" href="{url}">',
        '<meta name="theme-color" content="#f97316">',
        '<link rel="icon" href="/favicon.ico">',
        '<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">',
        '<link rel="manifest" href="/manifest.json">',
        '<meta name="apple-mobile-web-app-capable" content="yes">',
        '<meta property="og:locale" content="en_US">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:site_name" content="{SITE_NAME}">',
        f'<meta property="og:title" content="{t}">',
        f'<meta property="og:description" content="{d}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{SITE}/og-image.png">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{t}">',
        f'<meta name="twitter:description" content="{d}">',
        f'<meta name="twitter:image" content="{SITE}/og-image.png">',
        f'<link rel="alternate" type="application/rss+xml" title="{SITE_NAME} RSS" href="{SITE}/rss.xml">',
        f'<link rel="sitemap" type="application/xml" href="{SITE}/sitemap.xml">',
        '<script type="application/ld+json">',
        json.dumps(ld, ensure_ascii=False, indent=2),
        "</script>",
        "<!-- PAGE:HEAD END -->",
    ])


def header_block(p):
    return "\n".join(["<!-- PAGE:HEADER START -->", '<header class="header">', f"  <h1>{esc(p['h1'])}</h1>",
                      f"  <div class=\"header-sub\">{esc(p['sub'])}</div>", "</header>", "<!-- PAGE:HEADER END -->"])


def content_block(p):
    out = ["<!-- PAGE:CONTENT START -->", '<section class="section">', f"  <h2>{esc(p['intro_h2'])}</h2>", '  <div class="content-card">',
           f"    <p>{esc(p['intro'])}</p>"]
    for title, items in p["blocks"]:
        out.append(f"    <h3>{esc(title)}</h3>")
        out.append("    <ul>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>")
    out += ["  </div>", "</section>", "", '<section class="section" id="faq">', "  <h2>❓ Frequently asked questions</h2>"]
    for q, a in p["faq"]:
        out.append(f'  <div class="faq-item"><h3>Q. {esc(q)}</h3><p>{esc(a)}</p></div>')
    out += ["</section>", "", '<section class="section">', "  <h2>🧩 Other levels</h2>", '  <div class="link-grid">']
    self_href = "/" + p["path"]
    for href, label in LINKS:
        if href != self_href:
            out.append(f'    <a class="link-card" href="{href}">{esc(label)}</a>')
    out += ["  </div>", "</section>", "<!-- PAGE:CONTENT END -->"]
    return "\n".join(out)


def swap(text, name, block):
    pat = re.compile(r"<!-- PAGE:%s START -->.*?<!-- PAGE:%s END -->" % (name, name), re.S)
    new, n = pat.subn(lambda _: block, text)
    if n != 1:
        raise SystemExit(f"marker PAGE:{name} not found exactly once")
    return new


def build_page(src, p):
    text = swap(src, "HEAD", head_block(p))
    text = swap(text, "HEADER", header_block(p))
    text = swap(text, "CONTENT", content_block(p))
    preset = json.dumps(p["preset"], ensure_ascii=False)
    if text.count("<!-- PAGE:PRESET -->") != 1:
        raise SystemExit("marker PAGE:PRESET missing")
    return text.replace("<!-- PAGE:PRESET -->", f"<!-- PAGE:PRESET -->\n<script>window.SUDOKU_PRESET = {preset};</script>")


def title_desc(path):
    h = path.read_text(encoding="utf-8", errors="replace")
    t = re.search(r"<title[^>]*>(.*?)</title>", h, re.S)
    d = re.search(r'<meta[^>]+name=["\']description["\'][^>]*content=["\']([^"\']*)', h, re.I) or \
        re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]*name=["\']description', h, re.I)
    noindex = bool(re.search(r'<meta[^>]+name=["\']robots["\'][^>]+noindex', h, re.I))
    return (html.unescape(re.sub(r"\s+", " ", t.group(1))).strip() if t else path.name,
            html.unescape(d.group(1)).strip() if d else "", noindex)


def git_date(rel, first=False):
    out = subprocess.run(["git", "log", "--format=%cI", "--", rel], cwd=ROOT, capture_output=True, text=True).stdout.split()
    if not out:
        return dt.datetime.now(dt.timezone.utc)
    return dt.datetime.fromisoformat(out[-1] if first else out[0])


def site_pages():
    """Public pages for sitemap/RSS (noindex pages excluded, fixed order)."""
    rels = ["index.html", "daily.html"] + [f"level/{k}.html" for k in ("easy", "normal", "hard", "expert")]
    rels += ["disclaimer.html", "privacy.html", "terms.html"]
    return [r for r in rels if (ROOT / r).exists() and not title_desc(ROOT / r)[2]]


def loc(rel):
    return SITE + "/" if rel == "index.html" else f"{SITE}/{rel}"


def write_sitemap(rels, changed):
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for rel in rels:
        pr = "1.0" if rel == "index.html" else "0.9" if rel == "daily.html" else "0.8" if rel.startswith("level/") else "0.5"
        lm = today if rel in changed else git_date(rel).date().isoformat()
        lines += ["  <url>", f"    <loc>{esc(loc(rel))}</loc>", f"    <lastmod>{lm}</lastmod>", "    <changefreq>weekly</changefreq>",
                  f"    <priority>{pr}</priority>", "  </url>"]
    lines.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_rss(rels):
    now = dt.datetime.now(dt.timezone.utc)
    t, d, _ = title_desc(ROOT / "index.html")
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">', "<channel>",
           f"  <title>{esc(t)}</title>", f"  <link>{SITE}/</link>", f"  <description>{esc(d)}</description>", "  <language>en-us</language>",
           f'  <atom:link href="{SITE}/rss.xml" rel="self" type="application/rss+xml" />',
           f"  <lastBuildDate>{email.utils.format_datetime(now)}</lastBuildDate>"]
    items = []
    for rel in rels:
        if rel == "index.html":
            continue
        it, idesc, _ = title_desc(ROOT / rel)
        items.append((git_date(rel, first=True), rel, it, idesc))
    for when, rel, it, idesc in sorted(items, key=lambda x: x[0], reverse=True):
        out += ["  <item>", f"    <title>{esc(it)}</title>", f"    <link>{esc(loc(rel))}</link>", f'    <guid isPermaLink="true">{esc(loc(rel))}</guid>',
                f"    <description>{esc(idesc or it)}</description>", f"    <pubDate>{email.utils.format_datetime(when)}</pubDate>", "  </item>"]
    out += ["</channel>", "</rss>"]
    (ROOT / "rss.xml").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


def main():
    src = (ROOT / "index.html").read_text(encoding="utf-8")
    changed = {"index.html"}
    for p in PAGES:
        if len(p["title"]) > TITLE_MAX or len(p["desc"]) > DESC_MAX:
            raise SystemExit(f"{p['path']}: title {len(p['title'])} / desc {len(p['desc'])} over the {TITLE_MAX}/{DESC_MAX} limit")
        out = ROOT / p["path"]
        out.parent.mkdir(parents=True, exist_ok=True)
        text = build_page(src, p)
        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S):
            json.loads(block)
        if not out.exists() or out.read_text(encoding="utf-8") != text:
            out.write_text(text, encoding="utf-8", newline="\n")
            changed.add(p["path"])
    rels = site_pages()
    write_sitemap(rels, changed)
    write_rss(rels)
    print(f"built {len(PAGES)} pages; sitemap/rss entries: {len(rels)}")


if __name__ == "__main__":
    main()
