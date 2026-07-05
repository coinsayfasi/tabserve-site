#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apps.tabserve.com.tr YENİ blog yazılarını Mastodon'a postlar. Her yazı
app'ine göre (OneBag/RentFlow/Routevia) KENDİ store linki + hashtag + dil alır.
Mail/şifre YOK, sadece access token. Mastodon linkten og önizleme kartı üretir.
Env: MASTODON_INSTANCE, MASTODON_TOKEN. Yoksa güvenli atlar."""
import os, re, json, html, urllib.parse, urllib.request
from pathlib import Path

GEN = Path(__file__).resolve().parent
ROOT = GEN.parent
NEW = GEN / "new_urls.txt"
esc = html.unescape

APPS = {
    "onebag":   {"tags": "#travel #packing #traveltips #carryon",
                 "link": "https://coinsayfasi.github.io/go/onebag/",
                 "cta": "📲 Get OneBag free", "emoji": "🧳", "lang": "en"},
    "rentflow": {"tags": "#landlord #realestate #property #rental",
                 "link": "https://coinsayfasi.github.io/go/rentflow/",
                 "cta": "📲 Get RentFlow free", "emoji": "🏠", "lang": "en"},
    "routevia": {"tags": "#türkiye #gezi #seyahat #travel",
                 "link": "https://coinsayfasi.github.io/go/routevia/",
                 "cta": "📲 Routevia", "emoji": "🗺️", "lang": "tr"},
}


def toot(instance, token, status, lang):
    data = urllib.parse.urlencode({"status": status, "visibility": "public",
                                   "language": lang}).encode()
    req = urllib.request.Request(
        f"{instance.rstrip('/')}/api/v1/statuses", data=data, method="POST",
        headers={"Authorization": f"Bearer {token}"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def local_html(url):
    slug = url.rstrip("/").split("/blog/")[-1]
    p = ROOT / "blog" / slug / "index.html"
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""


def meta(h, *pats):
    for p in pats:
        m = re.search(p, h, re.I | re.S)
        if m:
            return esc(re.sub(r"\s+", " ", m.group(1)).strip())
    return ""


def detect(h):
    if "coinsayfasi.github.io/onebag/" in h:
        return "onebag"
    if "/routevia-app/" in h:
        return "routevia"
    if "/rentflow/" in h:
        return "rentflow"
    return "onebag"


def main():
    instance = os.environ.get("MASTODON_INSTANCE"); token = os.environ.get("MASTODON_TOKEN")
    if not (instance and token):
        print("⚠️ MASTODON_INSTANCE/TOKEN yok → Mastodon atlandı"); return
    urls = [u.strip() for u in NEW.read_text(encoding="utf-8").splitlines()
            if u.strip() and "/blog/" in u] if NEW.exists() else []
    if not urls:
        print("Mastodon: yeni yazı yok"); return
    for url in urls:
        h = local_html(url)
        if not h:
            continue
        title = meta(h, r'og:title["\']\s+content=["\'](.*?)["\']',
                     r"<title>(.*?)</title>").split(" | ")[0]
        desc = meta(h, r'og:description["\']\s+content=["\'](.*?)["\']',
                    r'name=["\']description["\']\s+content=["\'](.*?)["\']')
        if not title:
            continue
        a = APPS[detect(h)]
        status = (f"{a['emoji']} {title}\n\n{desc[:170]}\n\n{url}\n\n"
                  f"{a['cta']}: {a['link']}\n\n{a['tags']}")[:480]
        toot(instance, token, status, a["lang"])
        print(f"  ✓ Mastodon [{detect(h)}]: {url}")


if __name__ == "__main__":
    main()
