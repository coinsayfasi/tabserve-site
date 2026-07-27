#!/usr/bin/env python3
import json, os, sys

def inspect(session, site, url):
    body = {"inspectionUrl": url, "siteUrl": site}
    r = session.post("https://searchconsole.googleapis.com/v1/urlInspection/index:inspect",
                      json=body, timeout=30)
    r.raise_for_status()
    return r.json()["inspectionResult"]["indexStatusResult"]

def main():
    sa = os.environ.get("GOOGLE_INDEXING_SA", "").strip()
    if not sa:
        print("no sa"); sys.exit(1)
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession
    creds = service_account.Credentials.from_service_account_info(
        json.loads(sa), scopes=["https://www.googleapis.com/auth/webmasters.readonly"])
    session = AuthorizedSession(creds)
    site = "sc-domain:tabserve.com.tr"
    urls = [
        "https://apps.tabserve.com.tr/",
        "https://gezi.tabserve.com.tr/",
        "https://rentflow.tabserve.com.tr/",
        "https://www.tabserve.com.tr/",
    ]
    for u in urls:
        try:
            res = inspect(session, site, u)
            print("OK", u, res.get("verdict"), res.get("coverageState"))
        except Exception as e:
            print("HATA", u, "::", e)

if __name__ == "__main__":
    main()
