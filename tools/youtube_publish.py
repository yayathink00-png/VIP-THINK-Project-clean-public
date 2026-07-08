#!/usr/bin/env python3
import json
import mimetypes
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
DEFAULT_REDIRECT_URI = "https://developers.google.com/oauthplayground"
FULL_YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube"


def load_env_file():
    if not ENV_PATH.exists():
        return
    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def youtube_paths():
    load_env_file()
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET_JSON", "").strip()
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN_FILE", "").strip()
    return {
        "client_secret": Path(client_secret).expanduser() if client_secret else Path(),
        "refresh_token": Path(refresh_token).expanduser() if refresh_token else Path(),
    }


def youtube_available():
    paths = youtube_paths()
    return paths["client_secret"].is_file() and paths["refresh_token"].is_file()


def oauth_client_config():
    paths = youtube_paths()
    if not paths["client_secret"].is_file():
        raise FileNotFoundError(f"YouTube client secret not found: {paths['client_secret']}")
    client_data = json.loads(paths["client_secret"].read_text(encoding="utf-8"))
    cfg = client_data.get("web") or client_data.get("installed")
    if not cfg:
        raise ValueError("YouTube client secret JSON must contain web or installed config")
    return cfg


def access_token():
    paths = youtube_paths()
    if not paths["refresh_token"].is_file():
        raise FileNotFoundError(f"YouTube refresh token not found: {paths['refresh_token']}")
    cfg = oauth_client_config()
    refresh = paths["refresh_token"].read_text(encoding="utf-8").strip()
    body = urllib.parse.urlencode(
        {
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "refresh_token": refresh,
            "grant_type": "refresh_token",
        }
    ).encode("utf-8")
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body_text)
        except json.JSONDecodeError:
            payload = {"error": "http_error", "status": exc.code, "body": body_text}
    if "access_token" not in payload:
        raise RuntimeError("Could not refresh YouTube token: " + json.dumps(payload, ensure_ascii=False))
    return payload["access_token"]


def token_info():
    token = access_token()
    url = "https://oauth2.googleapis.com/tokeninfo?" + urllib.parse.urlencode({"access_token": token})
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"http_status": exc.code, "raw": raw}
    scopes = set((payload.get("scope") or "").split())
    payload["has_full_youtube_scope"] = FULL_YOUTUBE_SCOPE in scopes
    return payload


def youtube_auth_url(redirect_uri=DEFAULT_REDIRECT_URI):
    cfg = oauth_client_config()
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(
        {
            "client_id": cfg["client_id"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": FULL_YOUTUBE_SCOPE,
            "access_type": "offline",
            "prompt": "consent",
        }
    )


def exchange_auth_code(code, redirect_uri=DEFAULT_REDIRECT_URI):
    cfg = oauth_client_config()
    body = urllib.parse.urlencode(
        {
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
    ).encode("utf-8")
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"http_status": exc.code, "raw": raw}
    return payload


def upload_video(video_path, title, description="", privacy="private", tags=None, category_id="27", publish_at=None):
    path = Path(video_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Video file not found: {path}")
    token = access_token()
    metadata = {
        "snippet": {
            "title": title or path.stem,
            "description": description or "",
            "tags": tags or ["auto-publish"],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy or "private",
            "selfDeclaredMadeForKids": False,
        },
    }
    if publish_at:
        metadata["status"]["privacyStatus"] = "private"
        metadata["status"]["publishAt"] = publish_at
    boundary = "----codex-youtube-" + uuid.uuid4().hex
    content_type = mimetypes.guess_type(path.name)[0] or "video/mp4"
    chunks = [
        f"--{boundary}\r\n".encode("utf-8"),
        b"Content-Type: application/json; charset=UTF-8\r\n\r\n",
        json.dumps(metadata, ensure_ascii=False).encode("utf-8"),
        b"\r\n",
        f"--{boundary}\r\n".encode("utf-8"),
        f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
        path.read_bytes(),
        b"\r\n",
        f"--{boundary}--\r\n".encode("utf-8"),
    ]
    body = b"".join(chunks)
    url = "https://www.googleapis.com/upload/youtube/v3/videos?" + urllib.parse.urlencode(
        {"uploadType": "multipart", "part": "snippet,status"}
    )
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "multipart/related; boundary=" + boundary,
            "Content-Length": str(len(body)),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=240) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            result = {"http_status": exc.code, "raw": raw}
    if result.get("id"):
        result["watch_url"] = "https://www.youtube.com/watch?v=" + result["id"]
    return result
