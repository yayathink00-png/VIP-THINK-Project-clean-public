#!/usr/bin/env python3
import html
import json
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


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
    except Exception as exc:
        return {"error": {"message": str(exc), "type": type(exc).__name__}}


def mask(value):
    text = str(value or "")
    if len(text) <= 4:
        return text
    return text[:2] + "***" + text[-2:]


def check_token(token):
    result = []
    result.append(("Token", f"present, length={len(token)}"))

    debug = graph_get("debug_token", token, {"input_token": token})
    if "error" in debug:
        result.append(("debug_token", json.dumps(debug["error"], ensure_ascii=False, indent=2)))
    else:
        data = debug.get("data", {})
        scopes = data.get("scopes") or []
        result.append(("valid", str(data.get("is_valid"))))
        result.append(("app_id", str(data.get("app_id"))))
        result.append(("type", str(data.get("type"))))
        result.append(("expires_at", str(data.get("expires_at"))))
        result.append(("scopes", "\n".join(scopes) if scopes else "(none returned)"))

    me = graph_get("me", token, {"fields": "id,name"})
    if "error" in me:
        result.append(("/me", json.dumps(me["error"], ensure_ascii=False, indent=2)))
    else:
        result.append(("user", f"{me.get('name')} ({mask(me.get('id'))})"))

    permissions = graph_get("me/permissions", token)
    granted = []
    if "error" in permissions:
        result.append(("permissions", json.dumps(permissions["error"], ensure_ascii=False, indent=2)))
    else:
        granted = [
            item["permission"]
            for item in permissions.get("data", [])
            if item.get("status") == "granted"
        ]
        result.append(("granted_permissions", "\n".join(granted) if granted else "(none)"))

    accounts = graph_get(
        "me/accounts",
        token,
        {
            "fields": "id,name,tasks,instagram_business_account{id,name,username}",
            "limit": 100,
        },
    )
    pages = []
    if "error" in accounts:
        result.append(("pages", json.dumps(accounts["error"], ensure_ascii=False, indent=2)))
    else:
        pages = accounts.get("data", [])
        lines = []
        for page in pages:
            lines.append(f"- {page.get('name')} ({mask(page.get('id'))})")
            tasks = page.get("tasks") or []
            if tasks:
                lines.append(f"  tasks: {', '.join(tasks)}")
            ig = page.get("instagram_business_account")
            if ig:
                lines.append(
                    "  instagram_business_account: "
                    f"{ig.get('username') or ig.get('name')} ({mask(ig.get('id'))})"
                )
            else:
                lines.append("  instagram_business_account: none")
        result.append(("pages_found", str(len(pages))))
        result.append(("pages", "\n".join(lines) if lines else "(none)"))

    needed_fb = {"pages_show_list", "pages_manage_posts", "pages_read_engagement"}
    missing_fb = sorted(needed_fb - set(granted))
    if pages and not missing_fb:
        readiness = "likely_ready: yes"
    else:
        reasons = []
        if not pages:
            reasons.append("no manageable pages returned")
        if missing_fb:
            reasons.append("missing " + ", ".join(missing_fb))
        readiness = "likely_ready: no\n" + "\n".join(reasons)
    result.append(("facebook_publishing_readiness", readiness))
    return result


def page(body):
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Meta Token Check</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #111827; }}
    textarea {{ width: 100%; min-height: 120px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
    button {{ padding: 10px 16px; margin-top: 12px; }}
    pre {{ background: #f3f4f6; padding: 16px; white-space: pre-wrap; }}
    .wrap {{ max-width: 980px; margin: 0 auto; }}
  </style>
</head>
<body><div class="wrap">{body}</div></body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        body = """
<h1>Meta Token Check</h1>
<p>把 Facebook/Instagram token 粘贴到下面。结果会脱敏显示，不会打印 token。</p>
<form method="post">
  <textarea name="token" placeholder="Paste token here"></textarea>
  <br />
  <button type="submit">检查 token</button>
</form>
"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page(body).encode("utf-8"))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length).decode("utf-8", errors="replace")
        token = urllib.parse.parse_qs(payload).get("token", [""])[0].strip()
        if not token:
            output = "ERROR: token is empty"
        else:
            rows = check_token(token)
            output = "\n\n".join(f"{name}:\n{value}" for name, value in rows)
        body = f"""
<h1>Meta Token Check Result</h1>
<pre>{html.escape(output)}</pre>
<p><a href="/">返回重新检查</a></p>
"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page(body).encode("utf-8"))


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 4055), Handler)
    print("Meta token checker: http://localhost:4055")
    server.serve_forever()
