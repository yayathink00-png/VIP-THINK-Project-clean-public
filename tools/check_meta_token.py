#!/usr/bin/env python3
import json
import os
import sys
import urllib.parse
import urllib.request


GRAPH_BASE = "https://graph.facebook.com"


def graph_get(path, token, params=None):
    query = dict(params or {})
    query["access_token"] = token
    url = f"{GRAPH_BASE}/{path.lstrip('/')}?{urllib.parse.urlencode(query)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"raw": body}
        return {"_http_error": exc.code, **payload}


def safe_name(value):
    if not value:
        return ""
    text = str(value)
    if len(text) <= 4:
        return text
    return text[:2] + "***" + text[-2:]


def main():
    token = os.environ.get("META_ACCESS_TOKEN", "").strip()
    if not token:
        print("ERROR: META_ACCESS_TOKEN is empty", file=sys.stderr)
        return 2

    print("Meta token check")
    print(f"- token: present, length={len(token)}")

    debug = graph_get("debug_token", token, {
        "input_token": token,
    })
    if "error" in debug:
        print("- debug_token: failed")
        print(json.dumps(debug["error"], ensure_ascii=False, indent=2))
    else:
        data = debug.get("data", {})
        print("- debug_token:")
        print(f"  valid: {data.get('is_valid')}")
        print(f"  app_id: {data.get('app_id')}")
        print(f"  type: {data.get('type')}")
        print(f"  expires_at: {data.get('expires_at')}")
        scopes = data.get("scopes") or []
        if scopes:
            print("  scopes:")
            for scope in scopes:
                print(f"    - {scope}")

    me = graph_get("me", token, {"fields": "id,name"})
    if "error" in me:
        print("- /me: failed")
        print(json.dumps(me["error"], ensure_ascii=False, indent=2))
    else:
        print(f"- user: id={safe_name(me.get('id'))}, name={me.get('name')}")

    permissions = graph_get("me/permissions", token)
    if "error" in permissions:
        print("- permissions: failed")
        print(json.dumps(permissions["error"], ensure_ascii=False, indent=2))
    else:
        granted = [
            item["permission"]
            for item in permissions.get("data", [])
            if item.get("status") == "granted"
        ]
        print("- granted permissions:")
        for permission in granted:
            print(f"  - {permission}")

    accounts = graph_get("me/accounts", token, {
        "fields": "id,name,tasks,instagram_business_account{id,name,username}",
        "limit": 100,
    })
    if "error" in accounts:
        print("- pages: failed")
        print(json.dumps(accounts["error"], ensure_ascii=False, indent=2))
        return 1

    pages = accounts.get("data", [])
    print(f"- pages found: {len(pages)}")
    for page in pages:
        print(f"  - page: {page.get('name')} ({safe_name(page.get('id'))})")
        tasks = page.get("tasks") or []
        if tasks:
            print(f"    tasks: {', '.join(tasks)}")
        ig = page.get("instagram_business_account")
        if ig:
            print(
                "    instagram_business_account: "
                f"{ig.get('username') or ig.get('name')} ({safe_name(ig.get('id'))})"
            )
        else:
            print("    instagram_business_account: none")

    needed_fb = {"pages_show_list", "pages_manage_posts", "pages_read_engagement"}
    granted_set = set()
    if "data" in permissions:
        granted_set = {
            item["permission"]
            for item in permissions.get("data", [])
            if item.get("status") == "granted"
        }
    missing_fb = sorted(needed_fb - granted_set)
    print("- facebook publishing readiness:")
    if pages and not missing_fb:
        print("  likely_ready: yes")
    else:
        print("  likely_ready: no")
        if not pages:
            print("  reason: no manageable pages returned by /me/accounts")
        if missing_fb:
            print(f"  missing_permissions: {', '.join(missing_fb)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
