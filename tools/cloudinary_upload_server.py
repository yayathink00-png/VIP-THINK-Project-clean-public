#!/usr/bin/env python3
import cgi
import hashlib
import html
import json
import mimetypes
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
PORT = int(os.environ.get("CLOUDINARY_UPLOAD_PORT", "4056"))


def load_env_file():
    if not ENV_PATH.exists():
        return
    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def cloudinary_config():
    load_env_file()
    return {
        "cloud_name": os.environ.get("CLOUDINARY_CLOUD_NAME", "").strip(),
        "api_key": os.environ.get("CLOUDINARY_API_KEY", "").strip(),
        "api_secret": os.environ.get("CLOUDINARY_API_SECRET", "").strip(),
        "folder": os.environ.get("CLOUDINARY_FOLDER", "social-auto-publish").strip(),
    }


def missing_config(config):
    return [key for key in ("cloud_name", "api_key", "api_secret") if not config[key]]


def sign_params(params, api_secret):
    parts = []
    for key in sorted(params):
        value = params[key]
        if value is None or value == "" or key in {"file", "api_key", "resource_type"}:
            continue
        parts.append(f"{key}={value}")
    payload = "&".join(parts) + api_secret
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def encode_multipart(fields, files):
    boundary = "----codex-cloudinary-" + uuid.uuid4().hex
    chunks = []
    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        chunks.append(str(value).encode())
        chunks.append(b"\r\n")
    for name, filename, content_type, data in files:
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(
            (
                f'Content-Disposition: form-data; name="{name}"; '
                f'filename="{filename}"\r\n'
            ).encode()
        )
        chunks.append(f"Content-Type: {content_type}\r\n\r\n".encode())
        chunks.append(data)
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode())
    return boundary, b"".join(chunks)


def upload_to_cloudinary(filename, content_type, data):
    config = cloudinary_config()
    missing = missing_config(config)
    if missing:
        raise ValueError("Missing Cloudinary config: " + ", ".join(missing))

    timestamp = int(time.time())
    base_name = Path(filename).stem or "image"
    safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in base_name)
    public_id = f"{safe_name}-{timestamp}"
    params = {
        "timestamp": timestamp,
        "folder": config["folder"],
        "public_id": public_id,
    }
    signature = sign_params(params, config["api_secret"])
    fields = {
        **params,
        "api_key": config["api_key"],
        "signature": signature,
    }
    boundary, body = encode_multipart(
        fields,
        [("file", filename, content_type, data)],
    )
    url = f"https://api.cloudinary.com/v1_1/{config['cloud_name']}/image/upload"
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Cloudinary upload failed: HTTP {exc.code} {error_body}")


def save_config(form):
    values = {
        "CLOUDINARY_CLOUD_NAME": (form.getfirst("cloud_name") or "").strip(),
        "CLOUDINARY_API_KEY": (form.getfirst("api_key") or "").strip(),
        "CLOUDINARY_API_SECRET": (form.getfirst("api_secret") or "").strip(),
        "CLOUDINARY_FOLDER": (form.getfirst("folder") or "social-auto-publish").strip(),
    }
    missing = [key for key, value in values.items() if key != "CLOUDINARY_FOLDER" and not value]
    if missing:
        raise ValueError("Missing fields: " + ", ".join(missing))
    lines = [
        "# Local Cloudinary credentials. Do not commit this file.",
        f"CLOUDINARY_CLOUD_NAME={values['CLOUDINARY_CLOUD_NAME']}",
        f"CLOUDINARY_API_KEY={values['CLOUDINARY_API_KEY']}",
        f"CLOUDINARY_API_SECRET={values['CLOUDINARY_API_SECRET']}",
        f"CLOUDINARY_FOLDER={values['CLOUDINARY_FOLDER']}",
        "",
    ]
    ENV_PATH.write_text("\n".join(lines), encoding="utf-8")
    for key, value in values.items():
        os.environ[key] = value


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
    input[type=file] {{ display: block; margin: 16px 0; }}
    button {{ padding: 10px 16px; }}
    code, pre {{ background: #f3f4f6; }}
    pre {{ padding: 16px; white-space: pre-wrap; overflow-wrap: anywhere; }}
    img {{ max-width: 360px; max-height: 360px; display: block; margin-top: 12px; border: 1px solid #e5e7eb; }}
    .warn {{ color: #92400e; background: #fffbeb; padding: 12px; }}
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
        if self.path.startswith("/setup"):
            config = cloudinary_config()
            body = f"""
<h1>Cloudinary Setup</h1>
<p>在这里填 Cloudinary Console > Settings > API Keys 里的信息。</p>
<form method="post" action="/setup">
  <label>Cloud name</label><br />
  <input name="cloud_name" value="{html.escape(config['cloud_name'])}" style="width:100%;padding:8px" required /><br /><br />
  <label>API key</label><br />
  <input name="api_key" value="{html.escape(config['api_key'])}" style="width:100%;padding:8px" required /><br /><br />
  <label>API secret</label><br />
  <input name="api_secret" type="password" style="width:100%;padding:8px" required /><br /><br />
  <label>Folder</label><br />
  <input name="folder" value="{html.escape(config['folder'])}" style="width:100%;padding:8px" /><br /><br />
  <button type="submit">保存配置</button>
</form>
"""
            self.send_html("Cloudinary Setup", body)
            return

        config = cloudinary_config()
        missing = missing_config(config)
        if missing:
            body = f"""
<h1>Cloudinary Upload</h1>
<div class="warn">还缺配置：{html.escape(", ".join(missing))}</div>
<p>请在 <code>{html.escape(str(ENV_PATH))}</code> 填入 Cloudinary Console 里的 API 信息。</p>
<p><a href="/setup">打开配置页面</a></p>
<pre>CLOUDINARY_CLOUD_NAME=你的 cloud name
CLOUDINARY_API_KEY=你的 api key
CLOUDINARY_API_SECRET=你的 api secret
CLOUDINARY_FOLDER=social-auto-publish</pre>
<p>填好后刷新这个页面。</p>
"""
            self.send_html("Cloudinary Upload", body)
            return

        body = """
<h1>Cloudinary Upload</h1>
<p>选择本地图片，上传后会得到 Instagram 可用的 HTTPS 图片链接。</p>
<form method="post" enctype="multipart/form-data">
  <input type="file" name="file" accept="image/png,image/jpeg,image/webp" required />
  <button type="submit">上传图片</button>
</form>
"""
        self.send_html("Cloudinary Upload", body)

    def do_POST(self):
        if self.path.startswith("/setup"):
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": self.headers.get("Content-Type"),
                },
            )
            try:
                save_config(form)
            except Exception as exc:
                self.send_html("Cloudinary Setup failed", f"<h1>保存失败</h1><pre>{html.escape(str(exc))}</pre>", status=400)
                return
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers.get("Content-Type"),
            },
        )
        item = form["file"] if "file" in form else None
        if item is None or not getattr(item, "filename", ""):
            self.send_html("Upload failed", "<h1>没有选择文件</h1>", status=400)
            return
        data = item.file.read()
        if not data:
            self.send_html("Upload failed", "<h1>文件为空</h1>", status=400)
            return
        guessed_type = mimetypes.guess_type(item.filename)[0]
        content_type = item.type or guessed_type or "application/octet-stream"
        if content_type not in {"image/jpeg", "image/png", "image/webp"}:
            self.send_html(
                "Upload failed",
                f"<h1>暂不支持这个文件类型：{html.escape(content_type)}</h1>",
                status=400,
            )
            return
        try:
            result = upload_to_cloudinary(item.filename, content_type, data)
        except Exception as exc:
            self.send_html("Upload failed", f"<h1>上传失败</h1><pre>{html.escape(str(exc))}</pre>", status=500)
            return

        secure_url = result.get("secure_url", "")
        body = f"""
<h1>上传成功</h1>
<p>Instagram 用这个链接：</p>
<pre>{html.escape(secure_url)}</pre>
<img src="{html.escape(secure_url)}" alt="uploaded image" />
<p><a href="/">继续上传</a></p>
"""
        self.send_html("Upload success", body)


if __name__ == "__main__":
    print(f"Cloudinary upload page: http://localhost:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
