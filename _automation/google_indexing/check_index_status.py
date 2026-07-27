#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Search Console URL Inspection API ile bir sitemap'teki tüm URL'lerin index
durumunu tarar, "index'lenmemiş" olanları listeler.
Kurulum (bir kerelik):
  1. Google Cloud Console'da aynı service account'a (GOOGLE_INDEXING_SA'yı
     oluşturduğun proje) "Search Console API" servisini enable et.
  2. https://search.google.com/search-console -> ilgili mülk (property) ->
     Settings -> Users and permissions -> Add user -> service account'un
     client_email adresini "Full" yetkiyle ekle.
Kullanım:
  GOOGLE_INDEXING_SA='<service-account-json>' python3 check_index_status.py \
      --site https://rentflow.tabserve.com.tr --sitemap https://rentflow.tabserve.com.tr/sitemap.xml
"""
import argparse, json, os, re, sys, time, urllib.request

def sitemap_urls(sitemap_url):
    xml = urllib.request.urlopen(sitemap_url, timeout=30).read().decode("utf-8", "ignore")
    return re.findall(r"<loc>\s*(.*?)\s*</loc>", xml)

def inspect(session, site, url):
    body = {"inspectionUrl": url, "siteUrl": site}
    r = session.post("https://searchconsole.googleapis.com/v1/urlInspection/index:inspect",
                      json=body, timeout=30)
    r.raise_for_status()
    return r.json()["inspectionResult"]["indexStatusResult"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True, help="Search Console'daki property URL'i (örn. https://rentflow.tabserve.com.tr)")
    ap.add_argument("--sitemap", required=True, help="Taranacak sitemap.xml URL'i")
    ap.add_argument("--limit", type=int, default=0, help="0 = hepsi (yavaş; API kotası ~2000/gün)")
    args = ap.parse_args()

    sa = os.environ.get("GOOGLE_INDEXING_SA", "").strip()
    if not sa:
        print("⚠️ GOOGLE_INDEXING_SA env değişkeni yok."); sys.exit(1)
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession
    creds = service_account.Credentials.from_service_account_info(
        json.loads(sa), scopes=["https://www.googleapis.com/auth/webmasters.readonly"])
    session = AuthorizedSession(creds)

    urls = sitemap_urls(args.sitemap)
    if args.limit:
        urls = urls[:args.limit]
    print(f"🔍 {len(urls)} URL kontrol ediliyor ({args.site})...\n")

    not_indexed, indexed, errors = [], [], []
    for i, u in enumerate(urls, 1):
        try:
            res = inspect(session, args.site, u)
            verdict = res.get("verdict", "?")
            state = res.get("coverageState", "?")
            if verdict == "PASS":
                indexed.append(u)
            else:
                not_indexed.append((u, state))
            print(f"  [{i}/{len(urls)}] {verdict:10s} {state:35s} {u}")
        except Exception as e:
            errors.append((u, str(e)))
            print(f"  [{i}/{len(urls)}] HATA {type(e).__name__}: {u} :: {e}")
        time.sleep(1.2)  # kota koruması

    print(f"\n✓ index'li: {len(indexed)}  ✗ index-dışı: {len(not_indexed)}  hata: {len(errors)}")
    if not_indexed:
        print("\n— INDEX'LENMEMİŞ URL'ler —")
        for u, state in not_indexed:
            print(f"  {state:35s} {u}")

if __name__ == "__main__":
    main()
