#!/usr/bin/env python3
"""Listen to DingTalk Stream messages and append supplier orders to CSV."""

from __future__ import annotations

import asyncio
import csv
import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import dingtalk_stream
    from dingtalk_stream import ChatbotMessage
    from dingtalk_stream.frames import AckMessage
except ImportError as exc:  # pragma: no cover - exercised by manual startup
    raise SystemExit(
        "缺少依赖。请先运行：python3 -m pip install -r requirements.txt"
    ) from exc

try:
    import httpx
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "缺少依赖 httpx。请先运行：python3 -m pip install -r requirements.txt"
    ) from exc

from parse_order_messages import (
    OUTPUT_FIELDS,
    load_people,
    load_prices,
    normalize_output_csv,
    output_row,
    parse_order_fields,
)
from dingtalk_sheet_writer import append_order_to_sheet


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
LIVE_CSV_PATH = ROOT / "output" / "orders_live.csv"
EVENTS_PATH = ROOT / "output" / "dingtalk_events.jsonl"
WEBHOOK_RE = re.compile(r"^https://(?:api|oapi)\.dingtalk\.com/")


def load_env(path: Path = ENV_PATH) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def extract_text(message: ChatbotMessage, raw_data: Any | None = None) -> str:
    text = getattr(message, "text", None) or ""
    if hasattr(text, "content"):
        content = (text.content or "").strip()
    elif isinstance(text, dict):
        content = (text.get("content") or "").strip()
    else:
        content = str(text).strip()

    if content:
        return content

    rich_text = getattr(message, "rich_text_content", None) or getattr(message, "rich_text", None)
    rich_list = getattr(rich_text, "rich_text_list", None) if rich_text else None
    if isinstance(rich_list, list):
        parts = []
        for item in rich_list:
            if isinstance(item, dict):
                parts.append(item.get("text") or item.get("content") or "")
            elif hasattr(item, "text"):
                parts.append(getattr(item, "text") or "")
        content = "".join(parts).strip()
        if content:
            return content

    if isinstance(raw_data, dict):
        raw_content = raw_data.get("content") or {}
        raw_rich_text = raw_content.get("richText") or raw_content.get("rich_text") or []
        if isinstance(raw_rich_text, list):
            return "".join(
                (item.get("text") or item.get("content") or "")
                for item in raw_rich_text
                if isinstance(item, dict)
            ).strip()

    return ""


def extract_order_time(message: ChatbotMessage) -> str:
    create_at = getattr(message, "create_at", None)
    if create_at:
        try:
            return datetime.fromtimestamp(int(create_at) / 1000).strftime("%Y/%-m/%-d")
        except Exception:
            pass
    return datetime.now().strftime("%Y/%-m/%-d")


def extract_sender(message: ChatbotMessage) -> str:
    return (
        getattr(message, "sender_nick", None)
        or getattr(message, "sender_staff_id", None)
        or getattr(message, "sender_id", None)
        or "未知"
    )


def serializable_message(message: ChatbotMessage, raw_data: Any) -> dict[str, Any]:
    return {
        "received_at": datetime.now().isoformat(timespec="seconds"),
        "message_id": getattr(message, "message_id", None),
        "conversation_id": getattr(message, "conversation_id", None),
        "conversation_title": getattr(message, "conversation_title", None),
        "conversation_type": getattr(message, "conversation_type", None),
        "sender_id": getattr(message, "sender_id", None),
        "sender_staff_id": getattr(message, "sender_staff_id", None),
        "sender_nick": getattr(message, "sender_nick", None),
        "is_in_at_list": getattr(message, "is_in_at_list", None),
        "text": extract_text(message, raw_data),
        "raw": raw_data,
    }


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


async def reply_text(session_webhook: str, content: str) -> None:
    if not session_webhook or not WEBHOOK_RE.match(session_webhook):
        return
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            session_webhook,
            json={"msgtype": "text", "text": {"content": content}},
        )


def build_reply(row: dict[str, str] | None) -> str | None:
    if row is None:
        return None

    if row["解析状态"] == "OK":
        return (
            "已记录下单："
            f"{row['类型']} {row['数量']}，{row['具体内容']}，"
            f"单价{row['单价']}，总价{row['总价']}。"
        )

    return (
        "未写入，缺少字段："
        f"{row['缺失字段']}。"
        "请按完整 9 字段格式补发。"
    )


def invalid_format_reply() -> str:
    return (
        "未写入。请按完整 9 字段格式发送："
        "下单 下单时间 下单人 所属部门 交付时间 类型 数量 具体内容 单价 总价"
    )


class OrderMessageHandler(dingtalk_stream.ChatbotHandler):
    def __init__(self) -> None:
        super().__init__()
        self.people = load_people(ROOT / "config" / "people_departments.csv")
        self.prices = load_prices(ROOT / "config" / "prices.csv")

    def pre_start(self) -> None:
        return

    async def process(self, message: Any):
        try:
            data = message.data
            if isinstance(data, str):
                data = json.loads(data)

            chatbot_message = ChatbotMessage.from_dict(data)
            if not getattr(chatbot_message, "session_webhook", None) and isinstance(data, dict):
                chatbot_message.session_webhook = (
                    data.get("sessionWebhook") or data.get("session_webhook") or ""
                )
            if not getattr(chatbot_message, "is_in_at_list", False) and isinstance(data, dict):
                chatbot_message.is_in_at_list = bool(data.get("isInAtList"))

            await self.handle_chatbot_message(chatbot_message, data)
            return AckMessage.STATUS_OK, "OK"
        except Exception as exc:
            append_jsonl(EVENTS_PATH, {"received_at": datetime.now().isoformat(), "error": repr(exc)})
            return AckMessage.STATUS_SYSTEM_EXCEPTION, "error"

    async def handle_chatbot_message(self, message: ChatbotMessage, raw_data: Any) -> None:
        event = serializable_message(message, raw_data)
        append_jsonl(EVENTS_PATH, event)

        text = event["text"] or ""
        row = parse_order_fields(
            order_time=extract_order_time(message),
            sender=extract_sender(message),
            message=text,
            people=self.people,
            prices=self.prices,
        )
        if row is None:
            reply = invalid_format_reply() if "下单" in text else None
            if reply:
                await reply_text(getattr(message, "session_webhook", "") or "", reply)
            return
        if row["解析状态"] != "OK":
            reply = build_reply(row)
            if reply:
                await reply_text(getattr(message, "session_webhook", "") or "", reply)
            return

        append_order_csv(LIVE_CSV_PATH, row)
        try:
            append_order_to_sheet(row)
        except Exception as exc:
            append_jsonl(
                EVENTS_PATH,
                {
                    "received_at": datetime.now().isoformat(timespec="seconds"),
                    "sheet_append_error": repr(exc),
                    "row": row,
                },
            )
        reply = build_reply(row)
        if reply:
            await reply_text(getattr(message, "session_webhook", "") or "", reply)


async def main() -> None:
    load_env()
    client_id = os.getenv("DINGTALK_CLIENT_ID", "").strip()
    client_secret = os.getenv("DINGTALK_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret:
        raise SystemExit("缺少 DINGTALK_CLIENT_ID 或 DINGTALK_CLIENT_SECRET，请先填写 .env")

    credential = dingtalk_stream.Credential(client_id, client_secret)
    client = dingtalk_stream.DingTalkStreamClient(credential)
    client.register_callback_handler(dingtalk_stream.ChatbotMessage.TOPIC, OrderMessageHandler())

    print("DingTalk Stream 已启动。请在群里发送：@内容机器人 下单 混剪 3条 周家高混剪 交付4/2")
    await client.start()


if __name__ == "__main__":
    asyncio.run(main())
