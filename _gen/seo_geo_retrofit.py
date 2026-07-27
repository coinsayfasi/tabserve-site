#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-time sitewide retrofit: canonical domain fix + author identity fix.
Safe, mechanical, idempotent text replacements across all HTML/XML/JSON.
Does NOT touch structural HTML (headings, schema additions) — those are
handled separately per-file since they need judgment, not blind replace.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPLACEMENTS = [
    ("apps.tabserve.com.tr", "www.tabserve.com.tr"),
    ("Yunus Güneş", "Aycan Merve Güneş"),
]

EXTS = {".html", ".xml", ".json"}
SKIP_DIRS = {"_gen", "__pycache__", ".git", "node_modules"}

changed_files = 0
total_replacements = 0

for path in ROOT.rglob("*"):
    if path.is_dir():
        continue
    if path.suffix not in EXTS:
        continue
    if any(part in SKIP_DIRS for part in path.parts):
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    original = text
    file_repl = 0
    for old, new in REPLACEMENTS:
        count = text.count(old)
        if count:
            text = text.replace(old, new)
            file_repl += count
    if text != original:
        path.write_text(text, encoding="utf-8")
        changed_files += 1
        total_replacements += file_repl
        print(f"  {file_repl:4d}  {path.relative_to(ROOT)}")

print(f"\n{changed_files} dosya değişti, {total_replacements} değişiklik yapıldı.")
