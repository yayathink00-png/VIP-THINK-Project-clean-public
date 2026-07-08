#!/usr/bin/env python3
"""Poll DingTalk group messages and append structured order messages to CSV.

This mode does not require users to @ the bot. It periodically reads messages
from a configured group and parses messages containing "下单".
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from dingtalk_sheet_writer import append_order_to_sheet
from dws_util import resolve_dws_path
from parse_order_messages import OUTPUT_FIELDS, normalize_output_csv, output_row, parse_order_fields


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"


def output_dir() -> Path:
    configured = os.getenv("DINGTALK_OUTPUT_DIR", "").strip()
    return Path(configured) if configured else ROOT / "output"


def state_path() -> Path:
    return output_dir() / "poll_state.json"


def poll_csv_path() -> Path:
    return output_dir() / "orders_poll.csv"


def events_path() -> Path:
    return output_dir() / "dingtalk_poll_events.jsonl"


def load_env(path: Path = ENV_PATH) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def load_state() -> dict[str, Any]:
    path = state_path()
    if not path.exists():
        return {"seen_message_ids": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def append_order_csv(path: Path, row: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalize_output_csv(path)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerow(output_row(row))


def dws_json(args: list[str]) -> dict[str, Any]:
    cmd = [resolve_dws_path(), *args, "--format", "json"]
    completed = subprocess.run(
        cmd,
        cwd=str(ROOT),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stdout or completed.stderr)
    return json.loads(completed.stdout)


def list_messages(group_id: str, start_time: str, limit: int) -> list[dict[str, Any]]:
    payload = dws_json(
        [
            "chat",
            "message",
            "list",
            "--group",
            group_id,
            "--time",
            start_time,
            "--limit",
            str(limit),
        ]
    )
    return payload.get("result", {}).get("messages", []) or []


def send_bot_reply(group_id: str, robot_code: str, text: str) -> None:
    dws_json(
        [
            "chat",
            "message",
            "send-by-bot",
            "--group",
            group_id,
            "--robot-code",
            robot_code,
            "--title",
            "对账记录",
            "--text",
            text,
        ]
    )


def send_user_reply(group_id: str, text: str) -> None:
    dws_json(
        [
            "chat",
            "message",
            "send",
            "--group",
            group_id,
            "--title",
            "对账记录",
            "--text",
            text,
        ]
    )


def try_send_reply(group_id: str, robot_code: str, text: str) -> None:
    sender = os.getenv("DINGTALK_REPLY_SENDER", "bot").strip().lower()
    if sender == "off":
        return
    try:
        if sender == "user":
            send_user_reply(group_id, text)
        elif robot_code:
            send_bot_reply(group_id, robot_code, text)
    except Exception as exc:
        append_jsonl(
            events_path(),
            {
                "polled_at": datetime.now().isoformat(timespec="seconds"),
                "reply_error": repr(exc),
                "reply_text": text,
            },
        )


def build_reply(row: dict[str, str]) -> str:
    if row["解析状态"] == "OK":
        text = f"已登记：{row['类型']} {row['数量']}，{row['具体内容']}，总价{row['总价']}"
        sheet_url = os.getenv("DINGTALK_SHEET_URL", "").strip()
        if sheet_url:
            text += f"\n对账表：{sheet_url}"
        return text
    return f"未写入，缺少字段：{row['缺失字段']}。请按完整 9 字段格式补发。"


def invalid_format_reply() -> str:
    return (
        "未写入。请按完整 9 字段格式发送："
        "下单 下单时间 下单人 所属部门 交付时间 类型 数量 具体内容 单价 总价"
    )


def process_once(group_id: str, start_time: str, limit: int, reply: bool) -> int:
    robot_name = os.getenv("DINGTALK_ROBOT_NAME", "内容机器人")
    robot_code = os.getenv("DINGTALK_ROBOT_CODE", "")
    state = load_state()
    seen = set(state.get("seen_message_ids", []))
    processed_count = 0

    messages = list_messages(group_id, start_time, limit)
    messages = sorted(messages, key=lambda item: item.get("createTime", ""))

    for msg in messages:
        message_id = msg.get("openMessageId") or ""
        if not message_id or message_id in seen:
            continue

        seen.add(message_id)
        append_jsonl(events_path(), {"polled_at": datetime.now().isoformat(timespec="seconds"), **msg})

        sender = msg.get("sender") or ""
        content = msg.get("content") or ""
        if sender == robot_name:
            continue
        if "下单" not in content:
            continue

        row = parse_order_fields(
            order_time=msg.get("createTime", ""),
            sender=sender,
            message=content,
        )
        if row is None:
            if reply:
                try_send_reply(group_id, robot_code, invalid_format_reply())
            continue
        if row["解析状态"] != "OK":
            if reply:
                try_send_reply(group_id, robot_code, build_reply(row))
            processed_count += 1
            continue

        append_order_csv(poll_csv_path(), row)
        try:
            append_order_to_sheet(row)
        except Exception as exc:
            append_jsonl(
                events_path(),
                {
                    "polled_at": datetime.now().isoformat(timespec="seconds"),
                    "sheet_append_error": repr(exc),
                    "row": row,
                },
            )
        processed_count += 1

        if reply:
            try_send_reply(group_id, robot_code, build_reply(row))

    state["seen_message_ids"] = sorted(seen)[-1000:]
    state["last_polled_at"] = datetime.now().isoformat(timespec="seconds")
    save_state(state)
    return processed_count


def main() -> None:
    load_env()

    parser = argparse.ArgumentParser(description="Poll DingTalk group orders without requiring @bot.")
    parser.add_argument("--group-id", default=os.getenv("DINGTALK_GROUP_ID", ""))
    parser.add_argument("--start-time", default=os.getenv("DINGTALK_POLL_START_TIME", ""))
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--reply", action="store_true", help="Send bot confirmation messages.")
    args = parser.parse_args()

    if not args.group_id:
        raise SystemExit("缺少群 ID：请设置 DINGTALK_GROUP_ID 或传 --group-id")
    if not args.start_time:
        raise SystemExit("缺少拉取起点：请设置 DINGTALK_POLL_START_TIME 或传 --start-time")

    while True:
        count = process_once(args.group_id, args.start_time, args.limit, args.reply)
        print(f"polled_at={datetime.now().isoformat(timespec='seconds')} parsed={count}")
        if args.once:
            return
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
