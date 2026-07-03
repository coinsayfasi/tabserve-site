#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tabserve blog — AI ile ÖZGÜN, tam-SEO yazı üretici (Claude API, stdlib).
Kurallar: hedef anahtar kelime=title=H1; H2→H3→H4(→H5); 600+ KELİME; özgün (spin değil);
app CTA + internal link; Article schema. Doğrulama geçmezse YAYINLAMAZ.
Kullanım:
  ANTHROPIC_API_KEY=... python _gen/generate.py            # 1 yeni yazı üret+yayınla
  python _gen/generate.py --rebuild                         # API'siz: listeleme+sitemap yeniden kur
Env: ANTHROPIC_API_KEY, BLOG_MODEL (ops, varsayılan claude-sonnet-4-6), BLOG_COUNT (ops)."""
import os, re, sys, json, html, time, datetime, urllib.request, urllib.error, urllib.parse
from pathlib import Path

SOCIAL = [("YouTube","https://youtube.com/@tabserve"),("Instagram","https://instagram.com/tabservee"),
          ("TikTok","https://tiktok.com/@tabserve"),("Bluesky","https://bsky.app/profile/tabserve.bsky.social"),("Pinterest","https://pinterest.com/nedir_nasil")]

def _svg(d): return f'<svg viewBox="0 0 24 24" width="19" height="19" fill="currentColor" aria-hidden="true"><path d="{d}"/></svg>'
ICON = {
 "X":_svg("M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"),
 "f":_svg("M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"),
 "P":_svg("M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.663.967-2.911 2.168-2.911 1.024 0 1.518.769 1.518 1.688 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.099.12.112.225.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.172.271-.402.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.354-.629-2.758-1.379l-.749 2.848c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.607 0 11.985-5.365 11.985-11.987C23.97 5.39 18.592.026 11.985.026L12.017 0z"),
 "W":_svg("M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51l-.57-.01c-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.71.306 1.263.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884"),
 "in":_svg("M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.848 3.37-1.848 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"),
 "YouTube":_svg("M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"),
 "Instagram":_svg("M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069M12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12s.014 3.668.072 4.948c.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24s3.668-.014 4.948-.072c4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948s-.014-3.667-.072-4.947c-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0m0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324M12 16a4 4 0 110-8 4 4 0 010 8m6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881"),
 "TikTok":_svg("M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"),
 "Bluesky":_svg("M12 10.8c-1.087-2.114-4.046-6.053-6.798-7.995C2.566.944 1.561 1.266.902 1.565.139 1.908 0 3.08 0 3.768c0 .69.378 5.65.624 6.479.815 2.736 3.713 3.66 6.383 3.364-3.912.58-7.387 2.005-2.83 7.078 5.013 5.19 6.87-1.113 7.823-4.308.953 3.195 2.05 9.271 7.733 4.308 4.267-4.308 1.172-6.498-2.74-7.078 2.67.297 5.568-.628 6.383-3.364.246-.828.624-5.79.624-6.478 0-.69-.139-1.861-.902-2.206-.659-.298-1.664-.62-4.3 1.24C16.046 4.748 13.087 8.687 12 10.8Z"),
}
ICON["Pinterest"] = ICON["P"]

COOKIE_BANNER = '''<div id="cookie-banner" style="display:none;position:fixed;left:0;right:0;bottom:0;z-index:60;background:#ffffff;border-top:1px solid #ece8e1;box-shadow:0 -6px 24px rgba(31,39,51,.08);padding:14px 18px;font-size:13.5px;color:#384250;line-height:1.5">
  <div style="max-width:1080px;margin:0 auto;display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between">
    <span>We use cookies for analytics and advertising (incl. Google AdSense). See our <a href="/cookies.html" style="color:#2f6bff">Cookie Policy</a>.</span>
    <span><button onclick="cookieOK(0)" style="background:none;border:1px solid #d5d9e0;color:#384250;padding:7px 14px;border-radius:9px;cursor:pointer;margin-right:8px">Reject</button><button onclick="cookieOK(1)" style="background:linear-gradient(110deg,#2f6bff,#8b5cf6);border:0;color:#fff;padding:7px 16px;border-radius:9px;cursor:pointer;font-weight:600">Accept</button></span>
  </div>
</div>
<script>(function(){try{if(!localStorage.getItem("cookie_consent"))document.getElementById("cookie-banner").style.display="block";}catch(e){}})();
function cookieOK(v){try{localStorage.setItem("cookie_consent",v?"accepted":"rejected");}catch(e){}document.getElementById("cookie-banner").style.display="none";}</script>'''


def post_extras(url, title):
    """Alt paylaş çubuğu + yazar kutusu + sol kayan çubuk (SVG ikonlu)."""
    u = urllib.parse.quote(url, safe=''); t = urllib.parse.quote(title, safe='')
    S = [("X",f"https://twitter.com/intent/tweet?url={u}&amp;text={t}"),("f",f"https://www.facebook.com/sharer/sharer.php?u={u}"),
         ("P",f"https://pinterest.com/pin/create/button/?url={u}&amp;description={t}"),("W",f"https://wa.me/?text={t}%20{u}"),
         ("in",f"https://www.linkedin.com/sharing/share-offsite/?url={u}")]
    lbl = {"X":"X","f":"Facebook","P":"Pinterest","W":"WhatsApp","in":"LinkedIn"}
    share = '<div class="share"><span>Share this post:</span>' + ''.join(
        f'<a class="ico" href="{h}" target="_blank" rel="noopener" aria-label="{lbl[n]}">{ICON[n]}</a>' for n,h in S) + '</div>'
    follow = ''.join(f'<a class="ico" href="{lu}" target="_blank" rel="noopener" aria-label="{ln}">{ICON.get(ln,ln)}</a>' for ln,lu in SOCIAL)
    author = ('<div class="author-box"><img class="ab-logo" src="/assets/logo.svg" alt="Tabserve" width="56" height="56">'
              '<div class="ab-body"><b>Written by Tabserve</b><p>We\'re an independent app studio building simple, useful '
              'mobile apps for travel, trips and rentals — OneBag, Routevia and RentFlow. We share practical guides to help you '
              f'pack smarter, travel better and manage rentals with less hassle.</p><div class="follow"><span>Follow us:</span>{follow}</div></div></div>')
    rail = '<div class="share-rail" aria-label="Share this post">' + ''.join(
        f'<a href="{h}" target="_blank" rel="noopener" aria-label="{lbl[n]}">{ICON[n]}</a>' for n,h in S) + '</div>'
    return share + author, rail

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
The article should be genuinely helpful on its own and subtly fit a brand that makes {one} (called {name}). A small app promo box is added automatically afterwards — just write the article body.

STRICT RULES — follow every one:
1. The target keyword "{kw}" must appear in the TITLE and be the clear topic. The title doubles as the page H1 — do NOT output an <h1>.
2. Length: 600-800 words of real body text (count WORDS, not characters). Do not pad with fluff.
3. Heading hierarchy: use 4-6 <h2> headings (natural keyword variations), <h3> subheadings under H2s, and at least one deeper <h4> (use <h5> only where it genuinely helps). Logical nesting H2 > H3 > H4.
4. End with an <h2>Frequently Asked Questions</h2> section: 3 questions — each question as <h3>, its answer as a <p>. Then a short concluding paragraph.
4b. Right AFTER the intro paragraph add a "Key Takeaways" box with EXACTLY this structure:
<div class="quickfacts"><h2>Key Takeaways</h2><ul>
<li>...</li><li>...</li><li>...</li>
</ul></div>
(3-5 bullets, each a concrete, actionable point from the article.)
5. ORIGINAL and specific — real, useful guidance. Do NOT fabricate statistics, studies, prices or quotes. No repetition, no "spun"/generic filler.
5b. BANNED phrases: "unforgettable experience", "breathtaking", "hidden gem", "must-see", "look no further", "in today's world". Replace hype with concrete utility: which entrance, morning vs afternoon, how long it takes, walking distances, whether it suits kids, parking/transit notes.
6. Allowed body tags ONLY: h2, h3, h4, h5, p, ul, li, strong, a. No markdown, no <h1>, no <html>/<head>/<style>.
7. Include 1-2 outbound links to GENUINELY AUTHORITATIVE, relevant external sources to back up the content (e.g. an official tourism board, a government/regulator page, or a relevant Wikipedia article). Only use well-known, stable URLs you are confident exist — prefer https://en.wikipedia.org/wiki/<Topic> or an official site's homepage; NEVER invent specific deep URLs. Place them naturally inside sentences, not in headings.

Output ONLY valid minified JSON (no code fences, no commentary), exactly these keys:
{{"title":"...","meta_description":"max 155 chars, includes the keyword","keywords":"4-6 comma-separated keywords","slug":"kebab-case-from-title","img_query":"2-4 English words for a stock photo that VISUALLY matches the article (e.g. packing cubes suitcase / Istanbul Hagia Sophia)","body":"the article HTML"}}"""

def _post(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    for attempt in range(4):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=90).read())
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
                            "generationConfig":{"maxOutputTokens":8192,"temperature":0.75,"thinkingConfig":{"thinkingBudget":0}}},
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
<meta name="robots" content="index,follow">
<meta property="og:type" content="article">
<meta property="og:title" content="__TITLE__">
<meta property="og:description" content="__DESC__">
<meta property="og:url" content="__URL__">
<meta property="og:image" content="__OGIMG__">
<link rel="icon" type="image/svg+xml" href="/assets/logo.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;600&display=swap" onload="this.onload=null;this.rel='stylesheet'"><noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;600&display=swap"></noscript>
<link rel="stylesheet" href="/assets/blog.css">
<script type="application/ld+json">__SCHEMA__</script>
<script src="/assets/analytics.js" defer></script>
</head>
<body>
<div class="aurora"></div>
<nav><div class="nwrap">
  <a class="logo" href="/"><img src="/assets/logo.svg" alt="">Tabserve</a>
  <div class="nav-links"><a href="/">Apps</a><a href="/blog/">Blog</a><a href="mailto:teknopattv@gmail.com">Contact</a></div>
</div></nav>
<main class="wrap page">
__RAIL__
  <div class="crumb"><a href="/">Home</a> › <a href="/blog/">Blog</a> › __CRUMB__</div>
  <article class="post">
    <h1 class="title">__TITLE__</h1>
    <p class="meta">__TAG__ · __READ__ min read · Updated __NICE__</p>
__BODY__
  </article>
</main>
<footer class="site-footer">
  <div class="wrap foot-grid">
    <div class="foot-brand">
      <a class="logo" href="/"><img src="/assets/logo.svg" alt="" width="30" height="30">Tabserve</a>
      <p>Simple, useful mobile apps for travel, trips and rentals — free to start on iOS &amp; Android.</p>
    </div>
    <div class="foot-col">
      <h4>Apps</h4>
      <a href="https://coinsayfasi.github.io/onebag/">OneBag</a>
      <a href="https://coinsayfasi.github.io/routevia-app/">Routevia</a>
      <a href="https://coinsayfasi.github.io/rentflow/">RentFlow</a>
    </div>
    <div class="foot-col">
      <h4>Company</h4>
      <a href="/about.html">About</a>
      <a href="/blog/">Blog</a>
      <a href="mailto:teknopattv@gmail.com">Contact</a>
    </div>
    <div class="foot-col">
      <h4>Legal</h4>
      <a href="/privacy.html">Privacy Policy</a>
      <a href="/cookies.html">Cookie Policy</a>
      <a href="/terms.html">Terms of Use</a>
    </div>
  </div>
  <div class="foot-bottom"><div class="wrap">
    <span>© 2026 Tabserve · Built by Yunus Güneş</span>
    <span>Made with ♥ in Türkiye</span>
  </div></div>
</footer>
<div id="cookie-banner" style="display:none;position:fixed;left:0;right:0;bottom:0;z-index:60;background:#0d1426;border-top:1px solid rgba(255,255,255,.1);padding:14px 18px;font-size:13.5px;color:#cdd5ea;line-height:1.5">
  <div style="max-width:1080px;margin:0 auto;display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between">
    <span>We use cookies for analytics and advertising (incl. Google AdSense). See our <a href="/cookies.html" style="color:#6a9bff">Cookie Policy</a>.</span>
    <span><button onclick="cookieOK(0)" style="background:none;border:1px solid rgba(255,255,255,.25);color:#cdd5ea;padding:7px 14px;border-radius:9px;cursor:pointer;margin-right:8px">Reject</button><button onclick="cookieOK(1)" style="background:linear-gradient(110deg,#6a9bff,#b27bff);border:0;color:#fff;padding:7px 16px;border-radius:9px;cursor:pointer;font-weight:600">Accept</button></span>
  </div>
</div>
<script>(function(){try{if(!localStorage.getItem('cookie_consent'))document.getElementById('cookie-banner').style.display='block';}catch(e){}})();
function cookieOK(v){try{localStorage.setItem('cookie_consent',v?'accepted':'rejected');}catch(e){}document.getElementById('cookie-banner').style.display='none';}</script>
</body>
</html>
"""

def insert_cta(body, cta):
    if "{{APP_CTA}}" in body:
        return body.replace("{{APP_CTA}}", cta, 1)
    pos = [m.start() for m in re.finditer(r"<h2", body)]
    if len(pos) >= 2:
        i = pos[len(pos)//2]; return body[:i] + cta + body[i:]
    return body + cta

def fetch_hero(query, slug):
    """Pexels'ten konuya birebir uygun YATAY görsel indir →
    assets/blog/<slug>.webp (1600w) + <slug>-800.webp (mobil, srcset).
    Key yoksa veya sonuç zayıfsa sessizce görselsiz devam eder."""
    key = os.environ.get("PEXELS_API_KEY", "").strip()
    if not key: return False
    out = ROOT / "assets" / "blog"
    if any((out / f"{slug}.{e}").exists() for e in ("webp","jpg","jpeg","png")):
        return True
    try:
        u = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
            {"query": query, "orientation": "landscape", "size": "large", "per_page": 5})
        r = json.loads(urllib.request.urlopen(
            urllib.request.Request(u, headers={"Authorization": key, "User-Agent": "tabserve-blog/1.0"}), timeout=25).read())
        photos = r.get("photos") or []
        if not photos: return False
        src = photos[0]["src"].get("large2x") or photos[0]["src"].get("large")
        raw = urllib.request.urlopen(urllib.request.Request(
            src, headers={"User-Agent": "tabserve-blog/1.0"}), timeout=40).read()
        out.mkdir(parents=True, exist_ok=True)
        try:
            import io
            from PIL import Image
            im = Image.open(io.BytesIO(raw)).convert("RGB")
            for w_, suf in ((1600, ""), (800, "-800")):
                img = im if im.width <= w_ else im.resize(
                    (w_, round(im.height * w_ / im.width)), Image.LANCZOS)
                img.save(out / f"{slug}{suf}.webp", "WEBP", quality=82)
        except ImportError:
            (out / f"{slug}.jpg").write_bytes(raw)
        print(f"  🖼  Pexels: {slug} <- {query} (photo: {photos[0].get('photographer','?')})")
        return True
    except Exception as e:
        print(f"  (görsel atlandı: {type(e).__name__})")
        return False

def _openverse(q, n):
    out = []
    try:
        u = "https://api.openverse.org/v1/images/?q=" + q.replace(" ", "+") + "&license_type=commercial&size=medium&page_size=18"
        r = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent":"tabserve-blog/1.0"}), timeout=20).read())
        seen = set()
        for it in r.get("results", []):
            img = it.get("url") or it.get("thumbnail") or ""
            if img and img not in seen:
                seen.add(img)
                out.append({"url": img, "creator": it.get("creator") or "Unknown", "license": (it.get("license") or "CC").upper()})
            if len(out) >= n: break
    except Exception as e:
        print(f"  (görsel hata: {type(e).__name__})")
    return out

def get_images(query, n=3, fallback="travel"):
    """Anahtarsız Openverse görselleri — uzun sorgu sonuç vermezse kısaltıp/fallback dener."""
    ws = query.split()
    for q in [" ".join(ws[:3]), " ".join(ws[:2]), fallback]:
        if not q.strip(): continue
        out = _openverse(q, n)
        if out: return out
    return []

def _figure(img, alt, caption_text, hero=False):
    cap = (html.escape(caption_text) + " — " if caption_text else "") + f"Photo: {html.escape(img['creator'])} (Openverse, {html.escape(img['license'])})"
    w, h = (1200, 630) if hero else (1000, 560)
    perf = ' fetchpriority="high"' if hero else ' decoding="async"'  # LCP boost / async decode
    return (f'<figure class="{"hero" if hero else "inpost"}"><img src="{html.escape(img["url"])}" '
            f'alt="{html.escape(alt)}" loading="{"eager" if hero else "lazy"}"{perf} width="{w}" height="{h}">'
            f'<figcaption>{cap}</figcaption></figure>')

def _h2_text(body, p):
    m = re.match(r'<h2[^>]*>(.*?)</h2>', body[p:], re.S)
    return re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else ''

def faq_schema(body):
    """FAQPage JSON-LD from the article's own FAQ section (rich results)."""
    m = re.search(r'<h2[^>]*>[^<]*Frequently Asked Questions[^<]*</h2>([\s\S]*)', body, re.I)
    if not m: return None
    strip = lambda s: re.sub(r'<[^>]+>', '', s).strip()
    qas = re.findall(r'<h3[^>]*>([\s\S]*?)</h3>\s*<p[^>]*>([\s\S]*?)</p>', m.group(1))
    items = [{"@type":"Question","name":strip(q),
              "acceptedAnswer":{"@type":"Answer","text":strip(a)}}
             for q, a in qas if strip(q) and strip(a)]
    if not items: return None
    return {"@context":"https://schema.org","@type":"FAQPage","mainEntity":items}

# Kardeş TR site çapraz linkleri (aynı yayıncı — EN↔TR doğal iç ağ)
SISTER_URL = "https://gezi.tabserve.com.tr"
CROSS = {  # apps slug -> gezi slug (birebir konu eşleşmesi)
  "cappadocia-travel-guide": "kapadokya-gezi-rehberi-en-iyi-gezilecek-yerler-ve-ipuclari",
  "antalya-travel-guide-beaches-old-town-day-trips": "antalya-gezilecek-yerler-gezi-rehberi",
}

def related_block(posts, current_slug, tag=None, n=4):
    """'Related Guides' — iç linkleme; aynı etiketli yazılar öncelikli + kardeş site."""
    others = [p for p in posts if p["slug"] != current_slug]
    if tag:
        same = [p for p in others if p.get("tag") == tag]
        rest = [p for p in others if p.get("tag") != tag]
        others = same + rest
    others = others[:n]
    if not others: return ""
    lis = "".join(f'<li><a href="/blog/{p["slug"]}/">{html.escape(p["title"])}</a></li>'
                  for p in others)
    x = CROSS.get(current_slug)
    if x:
        lis += (f'<li><a href="{SISTER_URL}/blog/{x}/" hreflang="tr">'
                f'Bu rehberi Türkçe okuyun (Türkiye Gezi Rehberi)</a></li>')
    else:
        lis += (f'<li><a href="{SISTER_URL}/" hreflang="tr">'
                f'Türkçe gezi rehberleri — Türkiye Gezi Rehberi</a></li>')
    return ('<section class="related"><h2>Related Guides</h2><ul>'
            + lis + '</ul></section>')

def write_post(d, app, posts=()):
    slug = d["slug"]; url = f"{SITE}/blog/{slug}/"
    body = insert_cta(d["body"], APPS[app]["cta"])
    ogimg = f"{SITE}/assets/tabserve-og.png"
    # Görsel: kullanıcı assets/blog/<slug>.(jpg|png|webp) yüklerse hero olarak kullanılır; yoksa görselsiz (temiz).
    for ext in ("webp","jpg","jpeg","png"):
        ip = ROOT / "assets" / "blog" / f"{slug}.{ext}"
        if ip.exists():
            rel = f"/assets/blog/{slug}.{ext}"
            small = ROOT / "assets" / "blog" / f"{slug}-800.{ext}"
            srcset = (f' srcset="/assets/blog/{slug}-800.{ext} 800w, {rel} 1600w"'
                      f' sizes="(max-width:820px) 100vw, 780px"') if small.exists() else ""
            body = (f'<figure class="hero"><img src="{rel}"{srcset} alt="{html.escape(d["title"])}" loading="eager" fetchpriority="high" '
                    f'width="1200" height="630"><figcaption>{html.escape(d["meta_description"])}</figcaption></figure>') + body
            ogimg = SITE + rel
            break
    today = datetime.date.today()
    schemas = [{"@context":"https://schema.org","@type":"Article","headline":d["title"],
        "description":d["meta_description"],"image":ogimg,"author":{"@type":"Organization","name":"Tabserve"},
        "publisher":{"@type":"Organization","name":"Tabserve","logo":{"@type":"ImageObject","url":f"{SITE}/assets/tabserve-og.png"}},
        "datePublished":today.isoformat(),"dateModified":today.isoformat(),"mainEntityOfPage":url}]
    faq = faq_schema(body)
    if faq: schemas.append(faq)
    schema = json.dumps(schemas if len(schemas) > 1 else schemas[0], ensure_ascii=False)
    read = max(4, round(words(body)/180))
    extras, rail = post_extras(url, d["title"])
    body = body + related_block(posts, slug, tag=APPS[app]["tag"]) + extras
    page = (PAGE.replace("__TITLE__", html.escape(d["title"])).replace("__DESC__", html.escape(d["meta_description"]))
        .replace("__KW__", html.escape(d["keywords"])).replace("__URL__", url).replace("__OGIMG__", html.escape(ogimg))
        .replace("__SCHEMA__", schema).replace("__CRUMB__", html.escape(d["title"][:40]))
        .replace("__TAG__", APPS[app]["tag"]).replace("__READ__", str(read)).replace("__RAIL__", rail)
        .replace("__NICE__", today.strftime("%B %Y")).replace("__BODY__", body))
    (BLOG / slug).mkdir(parents=True, exist_ok=True)
    (BLOG / slug / "index.html").write_text(page, encoding="utf-8")

PER_PAGE = 9  # listeleme sayfası başına yazı

# Site GENELİ arama: /assets/search.json'dan tüm yazılarda arar (sayfalamadan bağımsız)
SEARCH = """
<div class="psearch" style="max-width:540px;margin:0 auto 26px;position:relative">
  <input id="q" type="search" placeholder="Search articles…" aria-label="Search articles" autocomplete="off"
    style="width:100%;box-sizing:border-box;padding:13px 20px 13px 46px;border-radius:999px;border:1px solid rgba(120,120,140,.28);background:rgba(255,255,255,.75);font:inherit;font-size:15px;outline:none">
  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" style="position:absolute;left:17px;top:50%;transform:translateY(-50%);opacity:.5" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
  <p id="qn" style="display:none;text-align:center;color:var(--muted);margin:14px 0 0">No results — try a different word.</p>
</div>
<div id="qres" class="posts" style="display:none"></div>
<script>document.addEventListener('DOMContentLoaded',function(){var q=document.getElementById('q');if(!q)return;
var grid=document.querySelector('.posts:not(#qres)'),nav=document.querySelector('.pagenav'),res=document.getElementById('qres'),qn=document.getElementById('qn'),idx=null;
function esc(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML}
q.addEventListener('input',function(){var v=q.value.trim().toLowerCase();
 if(!v){res.style.display='none';res.innerHTML='';if(grid)grid.style.display='';if(nav)nav.style.display='';qn.style.display='none';return}
 function run(){var hits=idx.filter(function(p){return (p.t+' '+p.d).toLowerCase().indexOf(v)>-1}).slice(0,30);
  if(grid)grid.style.display='none';if(nav)nav.style.display='none';
  if(!hits.length){res.style.display='none';res.innerHTML='';qn.style.display='block';return}
  qn.style.display='none';
  res.innerHTML=hits.map(function(p){return '<a class="pcard in" href="'+p.u+'"><h2>'+esc(p.t)+'</h2><p>'+esc(p.d)+'</p></a>'}).join('');
  res.style.display='';}
 if(idx){run()}else{fetch('/assets/search.json').then(function(r){return r.json()}).then(function(j){idx=j;run()}).catch(function(){})}
});});</script>
"""

def rebuild_index(posts):
    def card(p):
        return (f'    <a class="pcard" href="/blog/{p["slug"]}/"><span class="tag">{html.escape(p["tag"])}</span>'
                f'<h2>{html.escape(p["title"])}</h2><p>{html.escape(p["desc"])}</p></a>')
    # site geneli arama index'i
    (ROOT / "assets" / "search.json").write_text(json.dumps(
        [{"t": p["title"], "d": p["desc"], "u": f"/blog/{p['slug']}/"} for p in posts],
        ensure_ascii=False), encoding="utf-8")

    head = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>__T__ | Tabserve</title>
<meta name="description" content="Practical guides on carry-on packing, Türkiye travel and managing rental property — from the makers of OneBag, Routevia and RentFlow.">
<link rel="canonical" href="__CANON__">__PREVNEXT__
<link rel="icon" type="image/svg+xml" href="/assets/logo.svg">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;600&display=swap" onload="this.onload=null;this.rel='stylesheet'"><noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;600&display=swap"></noscript>
<link rel="stylesheet" href="/assets/blog.css"><script src="/assets/analytics.js" defer></script>
</head>
<body>
<div class="aurora"></div>
<nav><div class="nwrap"><a class="logo" href="/"><img src="/assets/logo.svg" alt="">Tabserve</a>
<div class="nav-links"><a href="/">Apps</a><a href="/blog/">Blog</a><a href="mailto:teknopattv@gmail.com">Contact</a></div></div></nav>"""
    foot = """<footer class="site-footer">
  <div class="wrap foot-grid">
    <div class="foot-brand">
      <a class="logo" href="/"><img src="/assets/logo.svg" alt="" width="30" height="30">Tabserve</a>
      <p>Simple, useful mobile apps for travel, trips and rentals — free to start on iOS &amp; Android.</p>
    </div>
    <div class="foot-col">
      <h4>Apps</h4>
      <a href="https://coinsayfasi.github.io/onebag/">OneBag</a>
      <a href="https://coinsayfasi.github.io/routevia-app/">Routevia</a>
      <a href="https://coinsayfasi.github.io/rentflow/">RentFlow</a>
    </div>
    <div class="foot-col">
      <h4>Company</h4>
      <a href="/about.html">About</a>
      <a href="/blog/">Blog</a>
      <a href="https://gezi.tabserve.com.tr/">Türkiye Gezi Rehberi (TR)</a>
      <a href="mailto:teknopattv@gmail.com">Contact</a>
    </div>
    <div class="foot-col">
      <h4>Legal</h4>
      <a href="/privacy.html">Privacy Policy</a>
      <a href="/cookies.html">Cookie Policy</a>
      <a href="/terms.html">Terms of Use</a>
    </div>
  </div>
  <div class="foot-bottom"><div class="wrap">
    <span>© 2026 Tabserve · Built by Yunus Güneş</span>
    <span>Made with ♥ in Türkiye</span>
  </div></div>
</footer>
<script>const io=new IntersectionObserver(e=>e.forEach(x=>{if(x.isIntersecting){x.target.classList.add('in');io.unobserve(x.target)}}),{threshold:.12});document.querySelectorAll('.pcard,.reveal').forEach((el,i)=>{el.style.transitionDelay=(i%4*70)+'ms';io.observe(el)});</script>
<noscript><style>.pcard,.reveal{opacity:1;transform:none}</style></noscript>
""" + COOKIE_BANNER + "\n</body></html>\n"

    # ── Sayfalamalı listeleme: /blog/ (p.1), /blog/page/2/ ... ────────────────
    chunks = [posts[i:i+PER_PAGE] for i in range(0, len(posts), PER_PAGE)] or [[]]
    total = len(chunks)
    page_url  = lambda n: f"{SITE}/blog/" if n == 1 else f"{SITE}/blog/page/{n}/"
    page_href = lambda n: "/blog/" if n == 1 else f"/blog/page/{n}/"

    for n, chunk in enumerate(chunks, 1):
        cards = "\n".join(card(p) for p in chunk)
        prevnext = ""
        if n > 1:     prevnext += f'\n<link rel="prev" href="{page_url(n-1)}">'
        if n < total: prevnext += f'\n<link rel="next" href="{page_url(n+1)}">'
        pagenav = ""
        if total > 1:
            items = [f'<a href="{page_href(n-1)}" aria-label="Previous">‹</a>' if n > 1 else '<span class="dis">‹</span>']
            items += [('<span class="cur">%d</span>' % i) if i == n else f'<a href="{page_href(i)}">{i}</a>' for i in range(1, total+1)]
            items.append(f'<a href="{page_href(n+1)}" aria-label="Next">›</a>' if n < total else '<span class="dis">›</span>')
            pagenav = '<nav class="pagenav" aria-label="Pages">' + "".join(items) + '</nav>'
        title = "Blog — Travel, trips &amp; landlord tips" if n == 1 else f"Blog — Page {n}"
        body = f"""
<main class="wrap page">
  <div class="crumb"><a href="/">Home</a> › Blog{'' if n == 1 else f' › Page {n}'}</div>
  <h1 class="title">The Tabserve Blog</h1>
  <p class="meta">Practical guides on packing smart, exploring Türkiye, and managing rentals — from the makers of OneBag, Routevia &amp; RentFlow.{f' ({len(posts)} guides)' if n == 1 else ''}</p>
{SEARCH}
  <div class="posts">
{cards}
  </div>
  {pagenav}
</main>
"""
        page = head.replace("__T__", title).replace("__CANON__", page_url(n)).replace("__PREVNEXT__", prevnext) + body + foot
        outdir = BLOG if n == 1 else BLOG / "page" / str(n)
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "index.html").write_text(page, encoding="utf-8")

    # yazı azalırsa bayat sayfa dizinlerini temizle
    pd = BLOG / "page"
    if pd.exists():
        for d in pd.iterdir():
            if d.is_dir() and d.name.isdigit() and int(d.name) > total:
                for f in d.iterdir(): f.unlink()
                d.rmdir()

    # sitemap
    static = [("/","1.0","weekly"),("/blog/","0.8","weekly"),("/privacy.html","0.3","yearly")]
    urls = "".join(f'  <url><loc>{SITE}{u}</loc><changefreq>{c}</changefreq><priority>{p}</priority></url>\n' for u,p,c in static)
    urls += "".join(f'  <url><loc>{SITE}/blog/page/{n}/</loc><changefreq>weekly</changefreq><priority>0.5</priority></url>\n' for n in range(2, total+1))
    urls += "".join(f'  <url><loc>{SITE}/blog/{po["slug"]}/</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>\n' for po in posts)
    (ROOT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n', encoding="utf-8")

def main():
    posts = load(POSTS_F, [])
    if "--rebuild" in sys.argv:
        rebuild_index(posts); print(f"✓ listeleme+sitemap yeniden kuruldu ({len(posts)} yazı)"); return
    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")):
        sys.exit("⚠️ GEMINI_API_KEY (ücretsiz) veya ANTHROPIC_API_KEY gerekli")
    state = load(STATE_F, {"used":[]}); used = set(state["used"])
    n = int(os.environ.get("BLOG_COUNT","1")); made = 0; new_urls = []
    if os.environ.get("BLOG_PER_APP"):  # her app'ten 1 kullanılmamış konu (1 onebag + 1 routevia + 1 rentflow)
        targets = [nx for ap in ["onebag","routevia","rentflow"]
                   if (nx := next((t for t in TOPICS if t["app"]==ap and t["keyword"] not in used), None))]
    else:
        targets = [t for t in TOPICS if t["keyword"] not in used][:n]
    for topic in targets:
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
        fetch_hero(d.get("img_query") or kw, d["slug"])
        write_post(d, app, posts)
        posts.insert(0, {"slug":d["slug"],"title":d["title"],"desc":d["meta_description"],
                         "tag":APPS[app]["tag"],"date":datetime.date.today().isoformat()})
        used.add(kw); made += 1
        new_urls.append(f"{SITE}/blog/{d['slug']}/")
        print(f"  ✓ yayınlandı: /blog/{d['slug']}/")
    # dedup posts by slug (en yeni kalsın)
    seen=set(); uniq=[]
    for p in posts:
        if p["slug"] in seen: continue
        seen.add(p["slug"]); uniq.append(p)
    POSTS_F.write_text(json.dumps(uniq, ensure_ascii=False, indent=1), encoding="utf-8")
    STATE_F.write_text(json.dumps({"used":list(used)}, ensure_ascii=False, indent=1), encoding="utf-8")
    rebuild_index(uniq)
    (GEN / "new_urls.txt").write_text("\n".join(new_urls), encoding="utf-8")  # index_ping.py için
    print(f"\n✓ {made} yeni yazı · toplam {len(uniq)} · {len(used)}/{len(TOPICS)} konu kullanıldı")

if __name__ == "__main__":
    main()
