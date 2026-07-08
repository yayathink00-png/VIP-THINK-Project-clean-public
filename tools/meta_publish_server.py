#!/usr/bin/env python3
import cgi
import html
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
PORT = int(os.environ.get("META_PUBLISH_PORT", "4057"))
GRAPH_BASE = "https://graph.facebook.com/v21.0"


def load_env_file():
    if not ENV_PATH.exists():
        return
    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def upsert_env(values):
    existing = {}
    if ENV_PATH.exists():
        for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if raw_line.strip() and not raw_line.strip().startswith("#") and "=" in raw_line:
                key, value = raw_line.split("=", 1)
                existing[key.strip()] = value.strip()
    existing.update(values)
    lines = ["# Local credentials. Do not commit this file."]
    for key in sorted(existing):
        lines.append(f"{key}={existing[key]}")
    lines.append("")
    ENV_PATH.write_text("\n".join(lines), encoding="utf-8")
    for key, value in values.items():
        os.environ[key] = value


def graph_request(method, path, token, params=None):
    query = dict(params or {})
    query["access_token"] = token
    data = None
    url = f"{GRAPH_BASE}/{path.lstrip('/')}"
    if method == "GET":
        url = f"{url}?{urllib.parse.urlencode(query)}"
    else:
        data = urllib.parse.urlencode(query).encode("utf-8")
    request = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
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


def token():
    load_env_file()
    return os.environ.get("META_ACCESS_TOKEN", "").strip()


def accounts():
    current_token = token()
    if not current_token:
        return {"data": []}
    return graph_request(
        "GET",
        "me/accounts",
        current_token,
        {
            "fields": "id,name,tasks,access_token,instagram_business_account{id,name,username}",
            "limit": 100,
        },
    )


def page_access_token(page_id):
    current_token = token()
    page_token = current_token
    account_data = accounts()
    for page in account_data.get("data", []):
        if page.get("id") == page_id and page.get("access_token"):
            page_token = page["access_token"]
            break
    return page_token


def publish_facebook(page_id, image_url, caption):
    page_token = page_access_token(page_id)
    result = graph_request(
        "POST",
        f"{page_id}/photos",
        page_token,
        {
            "url": image_url,
            "caption": caption,
            "published": "true",
        },
    )
    if result.get("id"):
        photo = graph_request(
            "GET",
            result["id"],
            page_token,
            {"fields": "id,link,created_time,name,picture"},
        )
        result["photo"] = photo
    if result.get("post_id"):
        _, _, story_id = result["post_id"].partition("_")
        if story_id:
            result["possible_post_url"] = f"https://www.facebook.com/{page_id}/posts/{story_id}"
    if result.get("photo", {}).get("link"):
        result["photo_url"] = result["photo"]["link"]
    return result


def schedule_facebook_photo(page_id, image_url, caption, scheduled_publish_time):
    page_token = page_access_token(page_id)
    result = graph_request(
        "POST",
        f"{page_id}/photos",
        page_token,
        {
            "url": image_url,
            "caption": caption,
            "published": "false",
            "scheduled_publish_time": str(scheduled_publish_time),
        },
    )
    if result.get("id"):
        photo = graph_request(
            "GET",
            result["id"],
            page_token,
            {"fields": "id,link,created_time,name,picture"},
        )
        result["photo"] = photo
        result["photo_url"] = photo.get("link")
    return result


def publish_instagram(ig_user_id, image_url, caption):
    current_token = token()
    create_result = graph_request(
        "POST",
        f"{ig_user_id}/media",
        current_token,
        {
            "image_url": image_url,
            "caption": caption,
        },
    )
    if "error" in create_result:
        return {"step": "create_container", **create_result}
    creation_id = create_result.get("id")
    if not creation_id:
        return {"error": {"message": "Instagram did not return a media container id"}, "raw": create_result}
    publish_result = graph_request(
        "POST",
        f"{ig_user_id}/media_publish",
        current_token,
        {"creation_id": creation_id},
    )
    result = {
        "container": create_result,
        "publish": publish_result,
    }
    if publish_result.get("id"):
        result["media"] = graph_request(
            "GET",
            publish_result["id"],
            current_token,
            {"fields": "id,caption,media_type,media_url,permalink,timestamp,username"},
        )
        if result.get("media", {}).get("permalink"):
            result["permalink"] = result["media"]["permalink"]
    return result


def page(title, body):
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #111827; }}
    .wrap {{ max-width: 980px; margin: 0 auto; }}
    input, textarea, select {{ width: 100%; box-sizing: border-box; padding: 8px; margin: 6px 0 14px; }}
    textarea {{ min-height: 120px; }}
    button {{ padding: 10px 16px; margin-right: 8px; }}
    pre {{ background: #f3f4f6; padding: 16px; white-space: pre-wrap; overflow-wrap: anywhere; }}
    .warn {{ color: #92400e; background: #fffbeb; padding: 12px; }}
    .ok {{ color: #065f46; background: #ecfdf5; padding: 12px; }}
  </style>
</head>
<body><div class="wrap">{body}</div></body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def send_html(self, title, body, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page(title, body).encode("utf-8"))

    def do_GET(self):
        current_token = token()
        if self.path.startswith("/setup"):
            body = """
<h1>Meta Token Setup</h1>
<p>粘贴 Facebook/Instagram System User token。会保存到本机 .env，不会显示在页面结果里。</p>
<form method="post" action="/setup">
  <textarea name="token" placeholder="Paste token here" required></textarea>
  <button type="submit">保存 token</button>
</form>
"""
            self.send_html("Meta Token Setup", body)
            return

        if not current_token:
            self.send_html(
                "Meta Publish",
                '<h1>Meta Publish</h1><div class="warn">还没有配置 META_ACCESS_TOKEN。</div><p><a href="/setup">先配置 token</a></p>',
            )
            return

        account_data = accounts()
        if "error" in account_data:
            self.send_html("Meta Publish", f"<h1>读取账号失败</h1><pre>{html.escape(json.dumps(account_data, ensure_ascii=False, indent=2))}</pre>")
            return

        page_options = []
        ig_options = []
        account_lines = []
        for item in account_data.get("data", []):
            page_id = item.get("id", "")
            page_name = item.get("name", page_id)
            page_options.append(f'<option value="{html.escape(page_id)}">{html.escape(page_name)} ({html.escape(page_id)})</option>')
            account_lines.append(f"Facebook Page: {page_name} ({page_id})")
            ig = item.get("instagram_business_account")
            if ig:
                ig_id = ig.get("id", "")
                ig_name = ig.get("username") or ig.get("name") or ig_id
                ig_options.append(f'<option value="{html.escape(ig_id)}">{html.escape(ig_name)} ({html.escape(ig_id)})</option>')
                account_lines.append(f"  Instagram: {ig_name} ({ig_id})")
            else:
                account_lines.append("  Instagram: none")

        body = f"""
<h1>Meta Publish</h1>
<div class="ok">Token 已配置。当前发现 {len(page_options)} 个 Facebook Page，{len(ig_options)} 个 Instagram 账号。</div>
<h2>账号</h2>
<pre>{html.escape(chr(10).join(account_lines) or "none")}</pre>
<h2>发布测试</h2>
<form method="post" action="/publish">
  <label>平台</label>
  <select name="platform">
    <option value="facebook">Facebook Page</option>
    <option value="instagram">Instagram</option>
  </select>
  <label>Facebook Page</label>
  <select name="page_id">{''.join(page_options)}</select>
  <label>Instagram 账号</label>
  <select name="ig_user_id">{''.join(ig_options)}</select>
  <label>图片 URL</label>
  <input name="image_url" value="https://res.cloudinary.com/jckpq8dp/image/upload/v1783305952/social-auto-publish/1-1-1783305950.jpg" required />
  <label>文案</label>
  <textarea name="caption">小學期末差倍必刷題</textarea>
  <button type="submit">发布</button>
</form>
<p><a href="/setup">更换 token</a></p>
"""
        self.send_html("Meta Publish", body)

    def do_POST(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers.get("Content-Type"),
            },
        )
        if self.path.startswith("/setup"):
            new_token = (form.getfirst("token") or "").strip()
            if not new_token:
                self.send_html("Meta Token Setup", "<h1>token 不能为空</h1>", status=400)
                return
            upsert_env({"META_ACCESS_TOKEN": new_token})
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
            return

        if self.path.startswith("/publish"):
            platform = (form.getfirst("platform") or "").strip()
            image_url = (form.getfirst("image_url") or "").strip()
            caption = (form.getfirst("caption") or "").strip()
            if platform == "facebook":
                result = publish_facebook((form.getfirst("page_id") or "").strip(), image_url, caption)
            elif platform == "instagram":
                result = publish_instagram((form.getfirst("ig_user_id") or "").strip(), image_url, caption)
            else:
                result = {"error": {"message": "Unknown platform"}}
            body = f"""
<h1>发布结果</h1>
<pre>{html.escape(json.dumps(result, ensure_ascii=False, indent=2))}</pre>
<p><a href="/">返回</a></p>
"""
            self.send_html("Publish Result", body)
            return

        self.send_html("Not Found", "<h1>Not Found</h1>", status=404)


if __name__ == "__main__":
    print(f"Meta publish page: http://localhost:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
