#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Retrofit existing blog posts to match the new generate.py templates:
1. Author box: "Written by Tabserve" -> "Written by Aycan Merve Güneş" + role + link.
2. Article schema author: Organization -> Person (Aycan Merve Güneş).
3. Meta line: fix "Updated Published: X · Updated: X" -> "Published: <time>X</time> · Updated: <time>X</time>".
Idempotent (safe to re-run).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOG = ROOT / "blog"

OLD_AUTHOR = (
    '<div class="author-box"><img class="ab-logo" src="/assets/logo.svg" alt="Tabserve" width="56" height="56">'
    '<div class="ab-body"><b>Written by Tabserve</b><p>We\'re an independent app studio building simple, useful '
    'mobile apps for travel, trips and rentals — OneBag, Routevia and RentFlow. We share practical guides to help you '
    'pack smarter, travel better and manage rentals with less hassle.</p><div class="follow"><span>Follow us:</span>'
)
NEW_AUTHOR = (
    '<div class="author-box"><img class="ab-logo" src="/assets/logo.svg" alt="Aycan Merve Güneş — Tabserve" width="56" height="56">'
    '<div class="ab-body"><b>Written by <a href="/author.html">Aycan Merve Güneş</a></b>'
    '<p style="color:var(--muted);font-size:13px;margin:2px 0 8px">Independent Full Stack Developer · Founder of Tabserve</p>'
    '<p>Aycan builds and maintains Tabserve\'s apps — OneBag, Routevia and RentFlow — and writes practical, '
    'tested guides to help you pack smarter, travel better and manage rentals with less hassle.</p><div class="follow"><span>Follow us:</span>'
)

OLD_SCHEMA_AUTHOR = '"author": {"@type": "Organization", "name": "Tabserve"}'
NEW_SCHEMA_AUTHOR = '"author": {"@type": "Person", "name": "Aycan Merve Güneş", "jobTitle": "Independent Full Stack Developer", "url": "https://www.tabserve.com.tr/author.html"}'

DATE_RE = re.compile(
    r'Updated Published: ([A-Za-z]{3} \d{2}, \d{4}) · Updated: ([A-Za-z]{3} \d{2}, \d{4})'
)

MONTHS = {"Jan":"01","Feb":"02","Mar":"03","Apr":"04","May":"05","Jun":"06",
          "Jul":"07","Aug":"08","Sep":"09","Oct":"10","Nov":"11","Dec":"12"}

def to_iso(nice_date: str) -> str:
    mon, day, year = nice_date.replace(",", "").split()
    return f"{year}-{MONTHS[mon]}-{day.zfill(2)}"

def fix_dates(text: str) -> str:
    def repl(m):
        pub, upd = m.group(1), m.group(2)
        return (f'Published: <time datetime="{to_iso(pub)}">{pub}</time> · '
                f'Updated: <time datetime="{to_iso(upd)}">{upd}</time>')
    return DATE_RE.sub(repl, text)

changed = 0
for f in sorted(BLOG.glob("*/index.html")):
    text = f.read_text(encoding="utf-8")
    original = text
    text = text.replace(OLD_AUTHOR, NEW_AUTHOR)
    text = text.replace(OLD_SCHEMA_AUTHOR, NEW_SCHEMA_AUTHOR)
    text = fix_dates(text)
    if text != original:
        f.write_text(text, encoding="utf-8")
        changed += 1
        print(f"  ✓ {f.relative_to(ROOT)}")
print(f"\n{changed} blog post güncellendi.")
