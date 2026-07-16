#!/usr/bin/env python3
"""Minimal local receiver for Xiaohongshu OAuth redirects.

The authorization code is written only to a private temporary file so it can
be exchanged by a separate process. No credentials or token values are logged.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


DEFAULT_CODE_FILE = Path("/private/tmp/xhs-oauth-authorization-code.json")


def now() -> str:
    return datetime.now(UTC).isoformat()


def write_private_json(path: Path, value: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value), encoding="utf-8")
    os.chmod(temporary, 0o600)
    temporary.replace(path)


def make_handler(expected_state: str, code_file: Path):
    class CallbackHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args) -> None:
            # Query strings may include an authorization code; never log them.
            return

        def reply(self, status: HTTPStatus, body: str, content_type: str = "text/html; charset=utf-8") -> None:
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(encoded)

        def do_GET(self) -> None:
            request = urlparse(self.path)
            if request.path == "/health":
                self.reply(HTTPStatus.OK, json.dumps({"status": "ready"}), "application/json")
                return
            if request.path != "/oauth/xhs/callback":
                self.reply(HTTPStatus.NOT_FOUND, "Not found")
                return

            values = parse_qs(request.query)
            state = values.get("state", [""])[0]
            code = values.get("code", values.get("auth_code", [""]))[0]
            if state != expected_state:
                self.reply(HTTPStatus.BAD_REQUEST, "授权状态不匹配，请重新发起授权。")
                return
            if not code:
                self.reply(HTTPStatus.BAD_REQUEST, "未收到授权码，请返回广告后台重新授权。")
                return
            write_private_json(code_file, {"code": code, "state": state, "received_at": now()})
            self.reply(HTTPStatus.OK, "授权回调已收到，可以关闭此页面。")

    return CallbackHandler


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8788)
    parser.add_argument("--state", default=os.environ.get("XHS_OAUTH_STATE", "abcd"))
    parser.add_argument("--code-file", type=Path, default=DEFAULT_CODE_FILE)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(args.state, args.code_file))
    print(f"OAuth callback listening on http://127.0.0.1:{args.port}/oauth/xhs/callback")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
