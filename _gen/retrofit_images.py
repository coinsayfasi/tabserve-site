#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Retrofit: mevcut blog yazılarını hedef görsel sayısına (1 hero + 4 inpost = 5)
tamamlar. Pexels'ten çeker, content H2'lerine yerleştirir, keyword-varied alt +
figcaption ekler. GitHub Action (PEXELS_API_KEY) ortamında çalışır.
Var olan görselleri korur; sadece eksik olanları ekler. FAQ/related bölgesine dokunmaz."""
import re, glob, html, sys, unicodedata
from pathlib import Path

GEN = Path(__file__).resolve().parent
sys.path.insert(0, str(GEN))
import generate as G  # fetch_inpost, ROOT reuse

TARGET = 4  # inpost hedefi
IS_TR = "gezi" in str(G.ROOT).lower()


def ascii_fold(s):
    s = s.replace("ı", "i").replace("İ", "I").replace("ş", "s").replace("Ş", "S")
    s = s.replace("ğ", "g").replace("Ğ", "G").replace("ü", "u").replace("ö", "o").replace("ç", "c")
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def content_end(h):
    end = len(h)
    for mk in ('class="related"', 'class="sources', 'Sık Sorulan', 'Frequently asked',
               'id="faq"', 'class="allapps"', 'class="faq'):
        i = h.find(mk)
        if i != -1:
            end = min(end, i)
    return end


def main():
    count = imgs = 0
    ctx_tr = ["Turkey", "Turkey landmark", "Turkey coast", "Turkey nature", "Turkey historic"]
    for f in sorted(glob.glob(str(G.ROOT / "blog/*/index.html"))):
        slug = Path(f).parent.name
        h = open(f, encoding="utf-8").read()
        have = len(set(re.findall(re.escape(slug) + r"-in(\d+)\.webp", h)))
        if have >= TARGET:
            continue
        need = TARGET - have
        kw_m = re.search(r'<meta name="keywords" content="([^"]*)"', h)
        kws = [k.strip() for k in kw_m.group(1).split(",") if k.strip()] if kw_m else []
        t_m = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
        title = re.sub(r"<[^>]+>", "", t_m.group(1)).strip() if t_m else slug
        topic = ascii_fold(re.split(r"[:—|]", title)[0].strip())
        end = content_end(h)
        pos = [m.start() for m in re.finditer(r"<h2", h) if m.start() < end]
        target_spots = [i for i in (5, 7, 9, 11, 6, 8) if i < len(pos)]
        added, inserts = 0, []
        for j, spot in enumerate(target_spots):
            if added >= need:
                break
            n = have + added + 1
            if IS_TR:
                query = f"{topic} {ctx_tr[j % len(ctx_tr)]}".strip()
            else:
                query = kws[j % len(kws)] if kws else topic
            rel = G.fetch_inpost(query, slug, n)
            if not rel:
                continue
            akw = kws[n % len(kws)] if kws else topic
            alt = html.escape((akw[:1].upper() + akw[1:]) if akw else topic)
            fig = (f'<figure class="inpost"><img src="{rel}" alt="{alt}" loading="lazy" '
                   f'decoding="async" width="1000" height="560"><figcaption>{alt}</figcaption></figure>')
            inserts.append((pos[spot], fig))
            added += 1
        for p, fig in sorted(inserts, reverse=True):
            h = h[:p] + fig + h[p:]
        if added:
            open(f, "w", encoding="utf-8").write(h)
            count += 1
            imgs += added
            print(f"  +{added} görsel: {slug}")
    print(f"\n✓ retrofit: {count} yazı, {imgs} yeni görsel eklendi")


if __name__ == "__main__":
    main()
