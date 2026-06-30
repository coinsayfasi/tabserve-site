#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tabserve blog — AI ile ÖZGÜN, tam-SEO yazı üretici (Claude API, stdlib).
Kurallar: hedef anahtar kelime=title=H1; H2→H3→H4(→H5); 600+ KELİME; özgün (spin değil);
app CTA + internal link; Article schema. Doğrulama geçmezse YAYINLAMAZ.
Kullanım:
  ANTHROPIC_API_KEY=... python _gen/generate.py            # 1 yeni yazı üret+yayınla
  python _gen/generate.py --rebuild                         # API'siz: listeleme+sitemap yeniden kur
Env: ANTHROPIC_API_KEY, BLOG_MODEL (ops, varsayılan claude-sonnet-4-6), BLOG_COUNT (ops)."""
import os, re, sys, json, html, time, datetime, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "_gen"
BLOG = ROOT / "blog"
TOPICS = json.loads((GEN / "topics.json").read_text(encoding="utf-8"))
POSTS_F = GEN / "posts.json"
STATE_F = GEN / "state.json"
SITE = "https://apps.tabserve.com.tr"
# Sağlayıcı: GEMINI (ücretsiz) öncelikli; yoksa Claude.
# Fallback zinciri — bir model deprecate olursa sıradakini dener (routevia prod gemini-flash-latest kullanıyor).
GEMINI_CANDIDATES = [m for m in [
    os.environ.get("GEMINI_MODEL"), "gemini-flash-latest", "gemini-3.5-flash",
    "gemini-flash-lite-latest", "gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-pro-latest",
] if m]
CLAUDE_MODEL = os.environ.get("BLOG_MODEL", "claude-sonnet-4-6")
_gemini_ok = None  # çalıştığı doğrulanan model (cache)

APPS = {
 "onebag":  {"tag":"Travel · OneBag",   "cta":'<div class="appcta"><b>🧳 Pack carry-on with confidence</b><p>OneBag builds a smart carry-on packing list for your exact trip and tracks your bag\'s weight against 80+ airlines\' limits — so you never forget an essential or pay an overweight fee.</p><a href="https://coinsayfasi.github.io/onebag/">See OneBag packing guides →</a></div>',
              "name":"OneBag","one":"a travel packing app with smart carry-on lists and an airline weight tracker"},
 "routevia":{"tag":"Travel · Routevia", "cta":'<div class="appcta"><b>🚗 Discover places &amp; map your route in minutes</b><p>Routevia shows you the best places to visit across Türkiye city by city, then plans an AI-powered route in seconds.</p><a href="https://coinsayfasi.github.io/routevia-app/">Explore places to visit in Türkiye →</a></div>',
              "name":"Routevia","one":"a Türkiye travel app that finds places to visit and plans AI trip routes"},
 "rentflow":{"tag":"Property · RentFlow","cta":'<div class="appcta"><b>🏠 Keep it all in one place</b><p>RentFlow lets you track rent, tenants, leases and expenses without spreadsheets — plus free calculators for rental yield, cash flow and legal rent increases across 18 countries.</p><a href="https://coinsayfasi.github.io/rentflow/">See RentFlow landlord calculators →</a></div>',
              "name":"RentFlow","one":"a rental manager for landlords with free yield and cash-flow calculators"},
}

def load(p, d): return json.loads(p.read_text(encoding="utf-8")) if p.exists() else d
def slugify(s): return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")[:70]
def words(htmlstr): return len(re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",htmlstr)).split())

PROMPT = """You are an expert SEO copywriter creating an ORIGINAL blog article for Tabserve's website.

TARGET KEYWORD: "{kw}"
ANGLE: {angle}
The article should be genuinely helpful on its own and subtly fit a brand that makes {one} (called {name}); you will place a token where a small app promo box goes.

STRICT RULES — follow every one:
1. The target keyword "{kw}" must appear in the TITLE and be the clear topic. The title doubles as the page H1 — do NOT output an <h1>.
2. Length: 600-800 words of real body text (count WORDS, not characters). Do not pad with fluff.
3. Heading hierarchy: use 4-6 <h2> headings (natural keyword variations), <h3> subheadings under H2s, and at least one deeper <h4> (use <h5> only where it genuinely helps). Logical nesting H2 > H3 > H4.
4. Place the exact token {{APP_CTA}} on its own line about 60% of the way through.
5. End with a short concluding paragraph.
6. ORIGINAL and specific — real, useful guidance. Do NOT fabricate statistics, studies, prices or quotes. No repetition, no "spun"/generic filler.
7. Allowed body tags ONLY: h2, h3, h4, h5, p, ul, li, strong, a. No markdown, no <h1>, no <html>/<head>/<style>.

Output ONLY valid minified JSON (no code fences, no commentary), exactly these keys:
{{"title":"...","meta_description":"max 155 chars, includes the keyword","keywords":"4-6 comma-separated keywords","slug":"kebab-case-from-title","body":"the article HTML"}}"""

def _post(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    for attempt in range(4):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=120).read())
        except urllib.error.HTTPError as e:
            if e.code in (429,529,500,503) and attempt < 3:
                time.sleep(8*(attempt+1)); continue
            raise
    raise RuntimeError("API başarısız")

def call_gemini(prompt, key):
    global _gemini_ok
    cands = ([_gemini_ok] if _gemini_ok else []) + [m for m in GEMINI_CANDIDATES if m != _gemini_ok]
    last = None
    for m in cands:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}"
        try:
            r = _post(url, {"contents":[{"parts":[{"text":prompt}]}],
                            "generationConfig":{"maxOutputTokens":4096,"temperature":0.75}},
                      {"content-type":"application/json"})
            cands_out = r.get("candidates")
            if not cands_out or not cands_out[0].get("content",{}).get("parts"):
                last = RuntimeError(f"{m}: boş yanıt ({r.get('promptFeedback','')})"); continue
            _gemini_ok = m
            print(f"  (model: {m})")
            return cands_out[0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            if e.code == 404:  # model deprecate/erişilemez → sıradakini dene
                last = e; continue
            raise
    raise last or RuntimeError("hiçbir Gemini modeli çalışmadı")

def call_claude(prompt, key):
    r = _post("https://api.anthropic.com/v1/messages",
        {"model":CLAUDE_MODEL,"max_tokens":2600,"messages":[{"role":"user","content":prompt}]},
        {"x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"})
    return r["content"][0]["text"]

def call_llm(prompt):
    gk = os.environ.get("GEMINI_API_KEY")
    if gk: return call_gemini(prompt, gk)
    ck = os.environ.get("ANTHROPIC_API_KEY")
    if ck: return call_claude(prompt, ck)
    sys.exit("⚠️ GEMINI_API_KEY (ücretsiz) veya ANTHROPIC_API_KEY gerekli")

def parse_json(txt):
    txt = txt.strip()
    if txt.startswith("```"): txt = re.sub(r"^```\w*\s*|\s*```$","",txt)
    i,j = txt.find("{"), txt.rfind("}")
    return json.loads(txt[i:j+1])

def validate(d, kw):
    b = d.get("body","")
    wc = words(b.replace("{{APP_CTA}}",""))
    h2,h3,h4 = len(re.findall(r"<h2",b)),len(re.findall(r"<h3",b)),len(re.findall(r"<h4",b))
    errs=[]
    if wc < 600: errs.append(f"kelime {wc}<600")
    if h2 < 3: errs.append(f"H2 {h2}<3")
    if h3 < 2: errs.append(f"H3 {h3}<2")
    if h4 < 1: errs.append(f"H4 {h4}<1")
    if "{{APP_CTA}}" not in b: errs.append("APP_CTA token yok")
    if kw.split()[0].lower() not in d.get("title","").lower(): errs.append("anahtar kelime title'da yok")
    return errs, wc, (h2,h3,h4)

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ | Tabserve</title>
<meta name="description" content="__DESC__">
<meta name="keywords" content="__KW__">
<link rel="canonical" href="__URL__">
<meta property="og:type" content="article">
<meta property="og:title" content="__TITLE__">
<meta property="og:description" content="__DESC__">
<meta property="og:url" content="__URL__">
<link rel="icon" type="image/svg+xml" href="/assets/logo.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/blog.css">
<script type="application/ld+json">__SCHEMA__</script>
</head>
<body>
<div class="aurora"></div>
<nav><div class="nwrap">
  <a class="logo" href="/"><img src="/assets/logo.svg" alt="">Tabserve</a>
  <div class="nav-links"><a href="/">Apps</a><a href="/blog/">Blog</a><a href="mailto:hello@tabserve.com.tr">Contact</a></div>
</div></nav>
<main class="wrap page">
  <div class="crumb"><a href="/">Home</a> › <a href="/blog/">Blog</a> › __CRUMB__</div>
  <article class="post">
    <h1 class="title">__TITLE__</h1>
    <p class="meta">__TAG__ · __READ__ min read · Updated __NICE__</p>
__BODY__
  </article>
</main>
<footer><div class="wrap">
  <a href="/">Apps</a> · <a href="/blog/">Blog</a> · <a href="/privacy.html">Privacy</a> · <a href="mailto:hello@tabserve.com.tr">Contact</a><br>
  <span style="opacity:.7">© 2026 Tabserve</span>
</div></footer>
</body>
</html>
"""

def write_post(d, app):
    slug = d["slug"]; url = f"{SITE}/blog/{slug}/"
    body = d["body"].replace("{{APP_CTA}}", APPS[app]["cta"])
    today = datetime.date.today()
    schema = json.dumps({"@context":"https://schema.org","@type":"Article","headline":d["title"],
        "description":d["meta_description"],"author":{"@type":"Organization","name":"Tabserve"},
        "publisher":{"@type":"Organization","name":"Tabserve","logo":{"@type":"ImageObject","url":f"{SITE}/assets/tabserve-og.png"}},
        "datePublished":today.isoformat(),"dateModified":today.isoformat(),"mainEntityOfPage":url}, ensure_ascii=False)
    read = max(4, round(words(body)/180))
    page = (PAGE.replace("__TITLE__", html.escape(d["title"])).replace("__DESC__", html.escape(d["meta_description"]))
        .replace("__KW__", html.escape(d["keywords"])).replace("__URL__", url)
        .replace("__SCHEMA__", schema).replace("__CRUMB__", html.escape(d["title"][:40]))
        .replace("__TAG__", APPS[app]["tag"]).replace("__READ__", str(read))
        .replace("__NICE__", today.strftime("%B %Y")).replace("__BODY__", body))
    (BLOG / slug).mkdir(parents=True, exist_ok=True)
    (BLOG / slug / "index.html").write_text(page, encoding="utf-8")

def rebuild_index(posts):
    cards = "\n".join(
      f'    <a class="pcard" href="/blog/{p["slug"]}/"><span class="tag">{html.escape(p["tag"])}</span>'
      f'<h2>{html.escape(p["title"])}</h2><p>{html.escape(p["desc"])}</p></a>' for p in posts)
    idx = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Blog — Travel, trips &amp; landlord tips | Tabserve</title>
<meta name="description" content="Practical guides on carry-on packing, Türkiye travel and managing rental property — from the makers of OneBag, Routevia and RentFlow.">
<link rel="canonical" href="{SITE}/blog/">
<link rel="icon" type="image/svg+xml" href="/assets/logo.svg">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/blog.css"></head>
<body>
<div class="aurora"></div>
<nav><div class="nwrap"><a class="logo" href="/"><img src="/assets/logo.svg" alt="">Tabserve</a>
<div class="nav-links"><a href="/">Apps</a><a href="/blog/">Blog</a><a href="mailto:hello@tabserve.com.tr">Contact</a></div></div></nav>
<main class="wrap page">
  <div class="crumb"><a href="/">Home</a> › Blog</div>
  <h1 class="title">The Tabserve Blog</h1>
  <p class="meta">Practical guides on packing smart, exploring Türkiye, and managing rentals — from the makers of OneBag, Routevia &amp; RentFlow.</p>
  <div class="posts">
{cards}
  </div>
</main>
<footer><div class="wrap"><a href="/">Apps</a> · <a href="/blog/">Blog</a> · <a href="/privacy.html">Privacy</a> · <a href="mailto:hello@tabserve.com.tr">Contact</a><br>
<span style="opacity:.7">© 2026 Tabserve · Built by Yunus Güneş</span></div></footer>
</body></html>
"""
    (BLOG / "index.html").write_text(idx, encoding="utf-8")
    # sitemap
    static = [("/","1.0","weekly"),("/blog/","0.8","weekly"),("/privacy.html","0.3","yearly")]
    urls = "".join(f'  <url><loc>{SITE}{u}</loc><changefreq>{c}</changefreq><priority>{p}</priority></url>\n' for u,p,c in static)
    urls += "".join(f'  <url><loc>{SITE}/blog/{po["slug"]}/</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>\n' for po in posts)
    (ROOT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n', encoding="utf-8")

def main():
    posts = load(POSTS_F, [])
    if "--rebuild" in sys.argv:
        rebuild_index(posts); print(f"✓ listeleme+sitemap yeniden kuruldu ({len(posts)} yazı)"); return
    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")):
        sys.exit("⚠️ GEMINI_API_KEY (ücretsiz) veya ANTHROPIC_API_KEY gerekli")
    state = load(STATE_F, {"used":[]}); used = set(state["used"])
    n = int(os.environ.get("BLOG_COUNT","1")); made = 0
    for topic in TOPICS:
        if made >= n: break
        if topic["keyword"] in used: continue
        kw, app = topic["keyword"], topic["app"]
        print(f"\n📝 [{app}] {kw}")
        prompt = PROMPT.format(kw=kw, angle=topic["angle"], one=APPS[app]["one"], name=APPS[app]["name"])
        d = None
        for tryi in range(2):
            txt = call_llm(prompt if tryi==0 else prompt+"\n\nYour previous attempt failed validation. Ensure 600+ WORDS and H2/H3/H4 hierarchy and the {{APP_CTA}} token.")
            try: cand = parse_json(txt)
            except Exception as e: print(f"  JSON parse hatası: {e}"); continue
            errs, wc, hh = validate(cand, kw)
            if not errs: d = cand; print(f"  ✓ {wc} kelime · H2/H3/H4={hh}"); break
            print(f"  ✗ doğrulama: {', '.join(errs)} → tekrar")
        if not d:
            print("  ⚠️ bu konu atlandı (kalite tutmadı)"); used.add(kw); continue
        d["slug"] = slugify(d.get("slug") or d["title"])
        write_post(d, app)
        posts.insert(0, {"slug":d["slug"],"title":d["title"],"desc":d["meta_description"],
                         "tag":APPS[app]["tag"],"date":datetime.date.today().isoformat()})
        used.add(kw); made += 1
        print(f"  ✓ yayınlandı: /blog/{d['slug']}/")
    # dedup posts by slug (en yeni kalsın)
    seen=set(); uniq=[]
    for p in posts:
        if p["slug"] in seen: continue
        seen.add(p["slug"]); uniq.append(p)
    POSTS_F.write_text(json.dumps(uniq, ensure_ascii=False, indent=1), encoding="utf-8")
    STATE_F.write_text(json.dumps({"used":list(used)}, ensure_ascii=False, indent=1), encoding="utf-8")
    rebuild_index(uniq)
    print(f"\n✓ {made} yeni yazı · toplam {len(uniq)} · {len(used)}/{len(TOPICS)} konu kullanıldı")

if __name__ == "__main__":
    main()
