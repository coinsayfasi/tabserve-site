#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evergreen apps.tabserve.com.tr blog yazılarını Bluesky'a DÖNGÜSEL drip-post eder
→ AdSense'li siteye sürekli trafik + tazelik/backlink sinyali. Günde birkaç yazı,
hepsi bitince en eskiden devam. social_post.py YENİ yazıları anlık postlar; bu ESKİ
evergreen içeriği döndürür (10 gün cooldown → çakışmaz). Konuya göre hashtag.
Env: BLUESKY_IDENTIFIER, BLUESKY_PASSWORD (yoksa atlar). DRIP_PER_RUN (vars. 2)."""
import os, re, json, html, datetime, urllib.request
from pathlib import Path

GEN = Path(__file__).resolve().parent
ROOT = GEN.parent
STATE = GEN / "social_apps_state.json"
BASE = "https://apps.tabserve.com.tr"
PDS = "https://bsky.social"
PER_RUN = int(os.environ.get("DRIP_PER_RUN", "2"))
esc = html.unescape
TOPIC_TAGS = {
    "packing": "#travel #packing #traveltips #carryon #onebag",
    "turkiye": "#türkiye #turkey #travel #traveltips #routevia",
    "landlord": "#landlord #realestate #rental #property #rentflow",
}
DEFAULT_TAGS = "#travel #tips #guide"


def topic(slug):
    s = slug.lower()
    # Önce Türkiye (yer adları) — "beach/antalya" packing'e kaçmasın
    if any(k in s for k in ("turkiye", "türkiye", "istanbul", "cappadocia", "antalya", "ephesus", "pamukkale", "itinerary", "road-trip", "food", "things-to-do")):
        return "turkiye", "🇹🇷"
    if any(k in s for k in ("pack", "carry", "luggage", "baggage", "toiletr", "flight", "backpack")):
        return "packing", "✈️"
    if any(k in s for k in ("rent", "landlord", "tenant", "lease", "yield", "cash-flow", "deposit", "buy-to-let", "property", "cap-rate")):
        return "landlord", "🏠"
    return None, "📘"


def meta(h, *pats):
    for p in pats:
        m = re.search(p, h, re.I | re.S)
        if m:
            return esc(re.sub(r"\s+", " ", m.group(1)).strip())
    return ""


def candidates():
    blog = ROOT / "blog"
    urls = []
    if blog.exists():
        for d in sorted(p for p in blog.iterdir() if (p / "index.html").exists()):
            urls.append(f"{BASE}/blog/{d.name}/")
    return urls


def local_html(url):
    rel = url[len(BASE) + 1:].rstrip("/")
    p = ROOT / rel / "index.html"
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""


def api(method, token, body=None, raw=None, ctype="application/json"):
    h = {"Content-Type": ctype}
    if token:
        h["Authorization"] = f"Bearer {token}"
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(f"{PDS}/xrpc/{method}", data=data, headers=h, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=40).read())


def hashtag_facets(text):
    facets = []
    for m in re.finditer(r"#([^\s#]+)", text):
        s = len(text[:m.start()].encode()); e = len(text[:m.end()].encode())
        facets.append({"index": {"byteStart": s, "byteEnd": e},
                       "features": [{"$type": "app.bsky.richtext.facet#tag", "tag": m.group(1)}]})
    return facets


def load_state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"posted": {}}


def main():
    ident = os.environ.get("BLUESKY_IDENTIFIER"); pw = os.environ.get("BLUESKY_PASSWORD")
    if not (ident and pw):
        print("⚠️ BLUESKY yok → apps drip atlandı"); return
    urls = candidates()
    if not urls:
        print("apps drip: aday yok"); return

    st = load_state(); posted = st.get("posted", {})
    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff = (now - datetime.timedelta(days=10)).isoformat()
    pending = [u for u in urls if posted.get(u, "") < cutoff] or sorted(urls, key=lambda u: posted.get(u, ""))
    picks = pending[:PER_RUN]

    sess = api("com.atproto.server.createSession", None, {"identifier": ident, "password": pw})
    print(f"✓ Bluesky: {sess['handle']} — {len(picks)} apps yazı drip")

    for url in picks:
        h = local_html(url)
        if not h:
            continue
        slug = url.rstrip("/").split("/blog/")[-1]
        tkey, emoji = topic(slug)
        tags = TOPIC_TAGS.get(tkey, DEFAULT_TAGS)
        title = meta(h, r'og:title["\']\s+content=["\'](.*?)["\']', r"<title>(.*?)</title>").split(" | ")[0]
        hook = re.split(r"\s+:\s+|:\s+", title)[0][:90]
        desc = meta(h, r'og:description["\']\s+content=["\'](.*?)["\']', r'name=["\']description["\']\s+content=["\'](.*?)["\']')
        ogimg = meta(h, r'og:image["\']\s+content=["\'](.*?)["\']')
        text = f"{emoji} {hook}\n\n{desc[:110]}\nRead free 👇\n\n{tags}"[:295]
        thumb = None
        if ogimg:
            try:
                img = urllib.request.urlopen(urllib.request.Request(ogimg, headers={"User-Agent": "bsky/1.0"}), timeout=25).read()
                mime = "image/png" if ogimg.lower().endswith("png") else "image/jpeg"
                thumb = api("com.atproto.repo.uploadBlob", sess["accessJwt"], raw=img, ctype=mime).get("blob")
            except Exception:
                pass
        ext = {"uri": url, "title": title[:280], "description": desc[:300]}
        if thumb:
            ext["thumb"] = thumb
        rec = {"$type": "app.bsky.feed.post", "text": text, "facets": hashtag_facets(text), "langs": ["en"],
               "createdAt": now.isoformat().replace("+00:00", "Z"),
               "embed": {"$type": "app.bsky.embed.external", "external": ext}}
        api("com.atproto.repo.createRecord", sess["accessJwt"],
            {"repo": sess["did"], "collection": "app.bsky.feed.post", "record": rec})
        posted[url] = now.isoformat()
        print(f"  ✓ drip postlandı: {url}")

    st["posted"] = posted
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
