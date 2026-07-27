#!/usr/bin/env python3
import argparse, json, os, re, sys, urllib.request

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
    ap.add_argument("--site", required=True)
    ap.add_argument("--sitemap", required=True)
    ap.add_argument("--limit", type=int, default=2)
    args = ap.parse_args()
    sa = os.environ.get("GOOGLE_INDEXING_SA", "").strip()
    if not sa:
        print("no sa"); sys.exit(1)
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession
    creds = service_account.Credentials.from_service_account_info(
        json.loads(sa), scopes=["https://www.googleapis.com/auth/webmasters.readonly"])
    session = AuthorizedSession(creds)
    urls = sitemap_urls(args.sitemap)[:args.limit]
    print(f"site={args.site} urls={urls}")
    for u in urls:
        try:
            res = inspect(session, args.site, u)
            print("OK", u, res.get("verdict"), res.get("coverageState"))
        except Exception as e:
            print("HATA", u, "::", e)

if __name__ == "__main__":
    main()
