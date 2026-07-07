#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Yeni OneBag blog yazısı yayınlanınca 'onebag' FCM topic'ine push atar.
Frekans kilidi: Salı + Cuma (haftada 2 — utility app, sık push spam olur).
Env: FIREBASE_SA_ONEBAG (onebag-8abf1 service account JSON; yoksa atlar).
FORCE_ONEBAG_PUSH=1 veya PUSH_URL ile frekans atlanır (test)."""
import os, re, json, html, datetime, urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

GEN = Path(__file__).resolve().parent
ROOT = GEN.parent
NEW = GEN / "new_urls.txt"
BLOG = ROOT / "blog"
TOPIC = "onebag"
PUSH_WEEKDAYS = {1, 4}  # Salı + Cuma
esc = html.unescape


def meta(h, *pats):
    for p in pats:
        m = re.search(p, h, re.I | re.S)
        if m:
            return esc(re.sub(r"\s+", " ", m.group(1)).strip())
    return ""


def local_html(url):
    slug = url.rstrip("/").split("/blog/")[-1]
    p = BLOG / slug / "index.html"
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""


def main():
    force = os.environ.get("FORCE_ONEBAG_PUSH", "").lower() in {"1", "true", "yes"}
    today = datetime.datetime.now(ZoneInfo("Europe/Istanbul"))
    if not force and today.weekday() not in PUSH_WEEKDAYS:
        print("Push: frekans sınırı — OneBag bildirimi yalnızca Salı/Cuma")
        return

    sa_json = os.environ.get("FIREBASE_SA_ONEBAG")
    push_url = os.environ.get("PUSH_URL", "").strip()
    urls = [push_url] if push_url else (
        [u.strip() for u in NEW.read_text(encoding="utf-8").splitlines() if u.strip()]
        if NEW.exists() else []
    )
    urls = [u for u in urls if "/blog/" in u]

    # Sadece OneBag yazıları (içerikte onebag app CTA'sı geçenler)
    onebag = []
    for u in urls:
        h = local_html(u)
        if h and "coinsayfasi.github.io/onebag/" in h:
            onebag.append((u, h))
    if not onebag:
        print("Push: yeni OneBag yazısı yok"); return
    if not sa_json:
        print("⚠️ FIREBASE_SA_ONEBAG yok → push atlandı"); return

    url, h = onebag[0]
    title = meta(h, r'og:title["\']\s+content=["\'](.*?)["\']', r"<title>(.*?)</title>")
    title = re.sub(r"\s*[|·]\s*[^|·]*$", "", title).strip()[:60] or "New travel packing tips"
    desc = meta(
        h, r'og:description["\']\s+content=["\'](.*?)["\']',
        r'name=["\']description["\']\s+content=["\'](.*?)["\']',
    )[:120] or "Pack smarter with OneBag."

    from google.oauth2 import service_account
    import google.auth.transport.requests
    creds = service_account.Credentials.from_service_account_info(
        json.loads(sa_json),
        scopes=["https://www.googleapis.com/auth/firebase.messaging"],
    )
    creds.refresh(google.auth.transport.requests.Request())
    project = json.loads(sa_json)["project_id"]

    body = {"message": {
        "topic": TOPIC,
        "notification": {"title": f"🧳 {title}", "body": desc},
        "data": {"url": url, "type": "blog", "app": "onebag"},
        "apns": {"payload": {"aps": {"sound": "default"}}},
    }}
    req = urllib.request.Request(
        f"https://fcm.googleapis.com/v1/projects/{project}/messages:send",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {creds.token}",
                 "Content-Type": "application/json"},
        method="POST")
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    print(f"✓ OneBag push gönderildi ({TOPIC}): {title} → {resp.get('name', resp)}")


if __name__ == "__main__":
    main()
