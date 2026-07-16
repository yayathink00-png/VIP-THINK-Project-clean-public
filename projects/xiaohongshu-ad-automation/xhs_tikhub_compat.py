#!/usr/bin/env python3
"""Compatibility adapter for the local blogger-distiller Xiaohongshu flow.

The installed skill can list an account's notes but some list endpoints omit
the per-note xsecToken required by the working web detail endpoint. This
adapter uses the skill's existing TikHub client and detail collector, adding
only an ID-based search enrichment step before detail collection.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SKILL_ROOT = Path("/Users/yangyi/.codex/skills/blogger-distiller")
KEYCHAIN_HELPER = Path("/private/tmp/xhs-keychain-helper")
KEYCHAIN_SERVICE = "vipthink-tikhub"
KEYCHAIN_ACCOUNT = "content-loop"
TIKHUB_CONFIG = Path.home() / ".xiaohongshu" / "tikhub_config.json"

sys.path.insert(0, str(SKILL_ROOT))

from scripts.crawl_xhs import (  # noqa: E402
    _extract_feeds_from_search,
    find_blogger,
    get_all_details,
    get_profile,
)
from scripts.utils.tikhub_client import TikHubClient  # noqa: E402


def load_token() -> str:
    token = os.environ.get("TIKHUB_API_TOKEN", "").strip()
    if token:
        return token
    if KEYCHAIN_HELPER.exists():
        result = subprocess.run(
            [str(KEYCHAIN_HELPER), "read", KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT],
            text=True,
            capture_output=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    if TIKHUB_CONFIG.exists():
        try:
            token = str(json.loads(TIKHUB_CONFIG.read_text(encoding="utf-8")).get("tikhub_api_token") or "").strip()
            if token:
                return token
        except (OSError, json.JSONDecodeError):
            pass
    raise RuntimeError("缺少 TikHub Token。请通过 TIKHUB_API_TOKEN 环境变量或 macOS 钥匙串提供。")


def note_id(feed: dict[str, Any]) -> str:
    return str(feed.get("id") or feed.get("note_id") or feed.get("noteId") or "")


def xsec_token(feed: dict[str, Any]) -> str:
    return str(feed.get("xsec_token") or feed.get("xsecToken") or "")


def enrich_xsec_tokens(client: TikHubClient, notes: dict[str, dict[str, Any]], account: str) -> dict[str, int]:
    matched = 0
    missing = 0
    for index, (identifier, note) in enumerate(notes.items(), start=1):
        if note.get("xsecToken"):
            continue
        title = str(note.get("title") or "").strip()
        queries = [title] if title else []
        if title:
            queries.append(f"{account} {title[:18]}")
        token = ""
        for query in queries:
            try:
                feeds = _extract_feeds_from_search(client.search_notes(query))
            except Exception:
                continue
            for feed in feeds:
                if note_id(feed) == identifier and xsec_token(feed):
                    token = xsec_token(feed)
                    break
            if token:
                break
        if token:
            note["xsecToken"] = token
            note["source"] = f"{note.get('source', 'profile')}+search_enrichment"
            matched += 1
        else:
            missing += 1
        print(f"[{index}/{len(notes)}] xsecToken: {'matched' if token else 'missing'}")
    return {"matched": matched, "missing": missing}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("account")
    parser.add_argument("--max-notes", type=int, default=50)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    token = load_token()
    client = TikHubClient(token=token)
    user_id, nickname, account_xsec = find_blogger(client, args.account)
    profile, notes = get_profile(client, user_id, account_xsec)
    notes = dict(sorted(notes.items(), key=lambda item: item[1].get("likedCount", 0), reverse=True)[: args.max_notes])
    enrichment = enrich_xsec_tokens(client, notes, nickname or args.account)

    (args.output / "notes_enriched.json").write_text(
        json.dumps(list(notes.values()), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    details = get_all_details(client, notes, str(args.output), nickname or args.account)
    (args.output / "notes_details.json").write_text(
        json.dumps(details, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (args.output / "compatibility_report.json").write_text(
        json.dumps(
            {
                "account": nickname,
                "user_id": user_id,
                "requested_note_limit": args.max_notes,
                "listed_notes": len(notes),
                "xsec_enrichment": enrichment,
                "valid_detail_count": sum(1 for item in details if not item.get("_error")),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
