#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Retroactive SEO for existing posts: Related Guides block (idempotent).
FAQ schema only applies to future posts (old posts have no FAQ section)."""
import json
from pathlib import Path
from generate import related_block

ROOT = Path(__file__).resolve().parents[1]
BLOG = ROOT / "blog"
POSTS = json.loads((ROOT / "_gen" / "posts.json").read_text(encoding="utf-8"))

changed = 0
for post in POSTS:
    slug = post["slug"]
    f = BLOG / slug / "index.html"
    if not f.exists():
        print(f"  ⚠️ missing: {slug}"); continue
    page = f.read_text(encoding="utf-8")
    if "Related Guides" in page:
        print(f"  = already: {slug}"); continue
    rel = related_block(POSTS, slug, tag=post.get("tag"))
    if rel and '<div class="share">' in page:
        page = page.replace('<div class="share">', rel + '<div class="share">', 1)
        f.write_text(page, encoding="utf-8")
        changed += 1
        print(f"  ✓ {slug}")
print(f"\n✓ {changed}/{len(POSTS)} posts updated")
