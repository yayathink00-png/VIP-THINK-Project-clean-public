#!/usr/bin/env python3
"""Exchange a received Xiaohongshu ad OAuth code and store tokens in Keychain."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path


TOKEN_URL = "https://adapi.xiaohongshu.com/api/open/oauth2/access_token"
DEFAULT_CODE_FILE = Path("/private/tmp/xhs-oauth-authorization-code.json")
KEYCHAIN_SOURCE = Path(__file__).resolve().parent / "xhs_keychain_helper.swift"
KEYCHAIN_BINARY = Path("/private/tmp/xhs-keychain-helper")
KEYCHAIN_SERVICE = "vipthink-xhs-ad-oauth-v2"
KEYCHAIN_ACCOUNT = "appId-8907"


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_code(path: Path) -> str:
    if not path.exists():
        fail("授权码文件不存在，请重新完成授权。")
    payload = json.loads(path.read_text(encoding="utf-8"))
    code = str(payload.get("code") or "")
    if not code:
        fail("授权码为空，请重新完成授权。")
    return code


def exchange(code: str, secret: str) -> dict:
    request_body = json.dumps({"app_id": 8907, "secret": secret, "auth_code": code}).encode("utf-8")
    request = urllib.request.Request(TOKEN_URL, data=request_body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        fail(f"Token 接口返回 HTTP {exc.code}。")
    except urllib.error.URLError as exc:
        fail(f"无法连接 Token 接口：{exc.reason}")
    if not isinstance(payload, dict):
        fail("Token 接口返回格式异常。")
    if payload.get("success") is False or payload.get("code") not in (None, 0, "0"):
        fail(f"Token 接口拒绝请求：{payload.get('msg') or payload.get('message') or payload.get('code') or '未知错误'}")
    data = payload.get("data", payload)
    if not isinstance(data, dict) or not any(key in data for key in ("access_token", "accessToken")):
        fail("Token 接口未返回 access token。")
    return data


def store_in_keychain(tokens: dict) -> None:
    value = json.dumps(tokens, ensure_ascii=False, separators=(",", ":"))
    if not KEYCHAIN_BINARY.exists() or KEYCHAIN_BINARY.stat().st_mtime < KEYCHAIN_SOURCE.stat().st_mtime:
        compiled = subprocess.run(["swiftc", str(KEYCHAIN_SOURCE), "-o", str(KEYCHAIN_BINARY)], text=True, capture_output=True)
        if compiled.returncode != 0:
            fail("无法编译 macOS 钥匙串存储组件。")
    result = subprocess.run(
        [str(KEYCHAIN_BINARY), "store", KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT],
        input=value,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        fail("无法写入 macOS 钥匙串。")
    verify = subprocess.run(
        [str(KEYCHAIN_BINARY), "read", KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT],
        text=True,
        capture_output=True,
    )
    if verify.returncode != 0 or verify.stdout != value:
        fail("macOS 钥匙串写入校验失败。")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-file", type=Path, default=DEFAULT_CODE_FILE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    secret = os.environ.get("XHS_AD_APP_SECRET", "")
    if not secret:
        fail("缺少 XHS_AD_APP_SECRET，仅接受临时环境变量。")
    code = load_code(args.code_file)
    if args.dry_run:
        print("ready_to_exchange=true")
        return 0
    tokens = exchange(code, secret)
    store_in_keychain(tokens)
    args.code_file.unlink(missing_ok=True)
    print("status=token_stored_in_macos_keychain")
    print("response_fields=" + ",".join(sorted(tokens.keys())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
