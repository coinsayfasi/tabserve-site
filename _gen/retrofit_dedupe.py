#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Görsel dedup + içerik-uyum geçişi.
- Aynı yazı içinde tekrar eden inpost görselleri tespit eder ve yenisiyle değiştirir.
- Her görseli bulunduğu H2 bölümünün BAŞLIĞINA göre çeker (içerik uyumu).
- gezi (TR): önce Wikimedia/Wikipedia (spesifik yer fotoğrafı), sonra Pexels.
- apps (EN): Pexels, bölüm başlığı sorgusuyla; sadece tekrar edenleri yeniler.
Dosya adları (slug-inN.webp) değişmez → HTML bozulmaz; alt+figcaption başlığa güncellenir.
"""
import re, glob, html, sys, io, hashlib, json, urllib.request, urllib.parse
from pathlib import Path

GEN = Path(__file__).resolve().parent
sys.path.insert(0, str(GEN))
import generate as G

IS_TR = "gezi" in str(G.ROOT).lower()
UA = {"User-Agent": "tabserve-blog/1.0 (+https://tabserve.com.tr)"}


def _get(url, timeout=25):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()


def ascii_fold(s):
    for a, b in (("ı", "i"), ("İ", "I"), ("ş", "s"), ("Ş", "S"), ("ğ", "g"),
                 ("Ğ", "G"), ("ü", "u"), ("Ü", "U"), ("ö", "o"), ("Ö", "O"), ("ç", "c"), ("Ç", "C")):
        s = s.replace(a, b)
    return s


def wiki_thumbs(term):
    """Wikipedia (tr sonra en) arama sonuçlarının lead görsellerini döndürür."""
    out = []
    for host in ("tr.wikipedia.org", "en.wikipedia.org"):
        try:
            u = f"https://{host}/w/api.php?" + urllib.parse.urlencode({
                "action": "query", "format": "json", "prop": "pageimages",
                "piprop": "thumbnail", "pithumbsize": 1280, "generator": "search",
                "gsrsearch": term, "gsrlimit": 4, "redirects": 1})
            r = json.loads(_get(u, 20))
            pages = sorted(r.get("query", {}).get("pages", {}).values(),
                           key=lambda p: p.get("index", 99))
            for p in pages:
                th = (p.get("thumbnail") or {}).get("source")
                if th:
                    out.append(th)
        except Exception:
            pass
    return out


def pexels_srcs(query):
    key = G.os.environ.get("PEXELS_API_KEY", "").strip()
    if not key:
        return []
    try:
        u = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
            {"query": query, "orientation": "landscape", "size": "large", "per_page": 15})
        r = json.loads(urllib.request.urlopen(urllib.request.Request(
            u, headers={"Authorization": key, **UA}), timeout=25).read())
        res = []
        for ph in r.get("photos") or []:
            res.append(ph["src"].get("large") or ph["src"].get("large2x"))
        return [s for s in res if s]
    except Exception:
        return []


def save_webp(src, dest):
    from PIL import Image
    raw = _get(src, 40)
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    if im.width > 1000:
        im = im.resize((1000, round(im.height * 1000 / im.width)), Image.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "WEBP", quality=80)
    return hashlib.md5(dest.read_bytes()).hexdigest()


def clean_heading(t):
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t).strip()
    t = re.sub(r"^\s*\d+[\.\)]\s*", "", t)          # "1. " ön ek
    t = re.sub(r"^[^\w\dığşöçüİĞŞÖÇÜ]+", "", t).strip()  # baştaki emoji/simge
    return t


def preceding_h2(h, pos):
    cand = [m.group(1) for m in re.finditer(r"<h2[^>]*>(.*?)</h2>", h, re.S) if m.start() < pos]
    return clean_heading(cand[-1]) if cand else ""


FIG_RE = re.compile(
    r'<figure class="inpost"><img src="([^"]+?-in(\d+)\.webp)"[^>]*?alt="([^"]*)"[^>]*?>'
    r'(?:<figcaption>.*?</figcaption>)?</figure>', re.S)


def main():
    aud = Path(G.ROOT) / "assets" / "blog"
    changed_articles = replaced = 0
    for f in sorted(glob.glob(str(G.ROOT / "blog/*/index.html"))):
        slug = Path(f).parent.name
        h = open(f, encoding="utf-8").read()
        t_m = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
        title = clean_heading(t_m.group(1)) if t_m else slug
        topic = re.split(r"[:—|]", title)[0].strip()
        figs = list(FIG_RE.finditer(h))
        if not figs:
            continue
        used = set()          # bu yazıda kullanılan görsel hash'leri
        art_changed = False
        for m in figs:
            src_path, idx, cur_alt = m.group(1), m.group(2), m.group(3)
            fpath = aud / f"{slug}-in{idx}.webp"
            cur_hash = hashlib.md5(fpath.read_bytes()).hexdigest() if fpath.exists() else None
            heading = preceding_h2(h, m.start()) or topic
            # apps'te alakalı+benzersizse dokunma; gezi'de içerik-uyumu için hepsini tazele
            if not IS_TR and cur_hash and cur_hash not in used:
                used.add(cur_hash)
                continue
            # aday görsel kaynakları (sıralı): wiki (gezi) → pexels. (src, is_wiki)
            cands = []
            if IS_TR:
                for term in (f"{heading} {topic}", heading, topic):
                    if term.strip():
                        cands += [(s, True) for s in wiki_thumbs(term)]
                pex_qs = [f"{ascii_fold(heading)} Turkey", f"{ascii_fold(topic)} Turkey", "Turkey travel scenery"]
            else:
                pex_qs = [heading, topic, "travel lifestyle"]
            for q in pex_qs:
                if q.strip():
                    cands += [(s, False) for s in pexels_srcs(q)]
            # ilk BENZERSİZ görseli seç
            chosen_hash = chosen_wiki = None
            for src, is_wiki in cands:
                tmp = fpath.with_name(fpath.stem + ".tmp.webp")
                try:
                    hh = save_webp(src, tmp)
                except Exception:
                    continue
                if hh in used:
                    tmp.unlink(missing_ok=True)
                    continue
                tmp.replace(fpath)
                chosen_hash, chosen_wiki = hh, is_wiki
                break
            if not chosen_hash:
                if cur_hash:
                    used.add(cur_hash)
                continue
            used.add(chosen_hash)
            new_alt = html.escape(heading[:120]) if heading else cur_alt
            credit = ('<span class="credit">Kaynak: Wikimedia Commons</span>' if chosen_wiki
                      else '')
            newfig = (f'<figure class="inpost"><img src="{src_path}" alt="{new_alt}" '
                      f'loading="lazy" decoding="async" width="1000" height="560">'
                      f'<figcaption>{new_alt}{credit}</figcaption></figure>')
            if newfig != m.group(0):
                h = h.replace(m.group(0), newfig, 1)
            art_changed = True
            replaced += 1
        if art_changed:
            open(f, "w", encoding="utf-8").write(h)
            changed_articles += 1
            print(f"  ✓ {slug}: {len([1])}… benzersizleştirildi")
    print(f"\n✓ dedupe: {changed_articles} yazı, {replaced} görsel yenilendi/benzersizleşti")


if __name__ == "__main__":
    main()
