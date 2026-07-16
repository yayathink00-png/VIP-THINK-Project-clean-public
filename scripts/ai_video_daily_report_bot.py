#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "ai_video_daily_report.json"
DWS_BIN = os.environ.get("DWS_BIN") or shutil.which("dws") or "dws"


REQUIRED_HEADERS = [
    "日期",
    "项目/视频",
    "完成视频数",
    "处理Segment数",
    "处理Segment明细",
    "一次通过数",
    "一次通过明细",
    "返工数",
    "返工明细",
    "废弃结果数",
    "废弃结果说明",
    "采用结果数",
    "有效生成结果数",
    "即梦链路问题次数",
    "即梦链路说明",
    "生成效果问题数",
    "生成效果说明",
    "参考图策略问题数",
    "参考图策略说明",
    "播报确认",
    "是否已播报",
    "播报时间",
    "备注",
]

OPTIONAL_HEADERS = [
    "AI执行内容",
    "AI实现质量",
    "人工Gate节点",
    "人工判断结果",
    "人工调整动作",
]

HEADERS = REQUIRED_HEADERS + OPTIONAL_HEADERS


@dataclass
class ReportRow:
    row_number: int
    data: dict


def run_dws(args):
    result = subprocess.run(
        [DWS_BIN, *args],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "DWS command failed:\n"
            f"command: dws {' '.join(args)}\n"
            f"stdout: {result.stdout.strip()}\n"
            f"stderr: {result.stderr.strip()}"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"DWS returned non-JSON output:\n{result.stdout}") from exc


def normalize_date(value):
    raw = str(value or "").strip()
    if not raw:
        return ""

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y/%-m/%-d"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass

    # DingTalk Sheets can expose dates as display strings like 2026/7/8.
    parts = raw.replace(".", "/").replace("-", "/").split("/")
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        year, month, day = [int(part) for part in parts]
        return f"{year:04d}-{month:02d}-{day:02d}"

    return raw


def is_yes(value):
    return str(value or "").strip().lower() in {"是", "yes", "y", "true", "1", "已确认"}


def is_sent(value):
    return str(value or "").strip().lower() in {"是", "yes", "y", "true", "1", "已播报"}


def to_int(value, default=0):
    text = str(value or "").strip()
    if not text:
        return default
    try:
        return int(float(text))
    except ValueError:
        return default


def pct(numerator, denominator):
    if denominator <= 0:
        return "0.0%"
    return f"{numerator / denominator * 100:.1f}%"


def count_with_detail(label, count, detail, unit="个"):
    text = f"- {label}：{count} {unit}"
    detail_text = str(detail or "").strip()
    if detail_text:
        text += f"（{detail_text}）"
    return text


def today_for_timezone(tz_name):
    # The workflow is local to China; keep a no-dependency timezone fallback.
    if tz_name == "Asia/Shanghai":
        return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    return datetime.now().strftime("%Y-%m-%d")


def date_for_timezone(tz_name, offset_days=0):
    # The workflow is local to China; keep a no-dependency timezone fallback.
    if tz_name == "Asia/Shanghai":
        base = datetime.now(timezone(timedelta(hours=8)))
    else:
        base = datetime.now()
    return (base + timedelta(days=offset_days)).strftime("%Y-%m-%d")


def previous_report_date_for_timezone(tz_name):
    # Workday report rule: Monday reports last Friday; other weekdays report yesterday.
    if tz_name == "Asia/Shanghai":
        base = datetime.now(timezone(timedelta(hours=8)))
    else:
        base = datetime.now()
    offset_days = -3 if base.weekday() == 0 else -1
    return (base + timedelta(days=offset_days)).strftime("%Y-%m-%d")


def now_shanghai():
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")


def resolve_state_path(config):
    configured = Path(config.get("approval_state_path", "state/ai_video_daily_report_approval.json"))
    if configured.is_absolute():
        return configured
    return ROOT / configured


def load_state(config):
    path = resolve_state_path(config)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(config, state):
    path = resolve_state_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def read_rows(config):
    response = run_dws(
        [
            "sheet",
            "range",
            "read",
            "--node",
            config["sheet_node_id"],
            "--sheet-id",
            config["sheet_id"],
            "--range",
            config.get("read_range", "A:X"),
        ]
    )
    rows = response.get("displayValues") or response.get("values") or []
    if not rows:
        return []

    header = [str(cell).strip() for cell in rows[0]]
    missing = [name for name in REQUIRED_HEADERS if name not in header]
    if missing:
        raise RuntimeError(f"Sheet header mismatch. Missing columns: {', '.join(missing)}")

    parsed = []
    for index, row in enumerate(rows[1:], start=2):
        if not any(str(cell or "").strip() for cell in row):
            continue
        data = {name: "" for name in HEADERS}
        for col_index, name in enumerate(header):
            if name in data and col_index < len(row):
                data[name] = row[col_index]
        parsed.append(ReportRow(row_number=index, data=data))
    return parsed


def pick_rows(rows, report_date, include_sent=False):
    picked = []
    for row in rows:
        data = row.data
        if normalize_date(data["日期"]) != report_date:
            continue
        if not is_yes(data["播报确认"]):
            continue
        if is_sent(data["是否已播报"]) and not include_sent:
            continue
        picked.append(row)
    return picked


def render_one(row):
    data = row.data
    done = to_int(data["完成视频数"])
    total = to_int(data["处理Segment数"])
    passed = to_int(data["一次通过数"])
    reworked = to_int(data["返工数"])
    discarded = to_int(data["废弃结果数"])
    adopted = to_int(data["采用结果数"])
    effective = to_int(data["有效生成结果数"])

    lines = [
        f"项目：{data['项目/视频']}",
        "",
        "**今日产量**",
        f"- 完成视频：{done} 条",
        count_with_detail("处理 Segment", total, data["处理Segment明细"]),
        count_with_detail("一次通过", passed, data["一次通过明细"]),
        count_with_detail("返工", reworked, data["返工明细"]),
        count_with_detail("废弃结果", discarded, data["废弃结果说明"]),
        "",
        "**成功率**",
        f"- Segment 一次通过率：{pct(passed, total)}（{passed}/{total}）",
        f"- Segment 返工率：{pct(reworked, total)}（{reworked}/{total}）",
        f"- AI 生成可用率：{pct(adopted, effective)}（{adopted}/{effective}，不含未扣费的上传失败）",
    ]

    quality = str(data.get("AI实现质量") or "").strip()
    if quality:
        lines.extend(["", "**AI实现质量**", f"- {quality}"])

    ai_work = str(data.get("AI执行内容") or "").strip()
    human_gate = str(data.get("人工Gate节点") or "").strip()
    human_judgement = str(data.get("人工判断结果") or "").strip()
    human_adjustment = str(data.get("人工调整动作") or "").strip()
    if any([ai_work, human_gate, human_judgement, human_adjustment]):
        lines.extend(["", "**AI / 人工分工**"])
        if ai_work:
            lines.append(f"- AI执行：{ai_work}")
        if human_gate:
            lines.append(f"- 人工 Gate：{human_gate}")
        if human_judgement:
            lines.append(f"- 人工判断：{human_judgement}")
        if human_adjustment:
            lines.append(f"- 人工调整：{human_adjustment}")

    lines.extend(["", "**问题归因**"])

    problem_count = 0
    jimeng_count = to_int(data["即梦链路问题次数"])
    if jimeng_count > 0:
        lines.extend(["", f"- 即梦链路问题：{jimeng_count} 次", f"  {data['即梦链路说明']}"])
        problem_count += 1

    effect_count = to_int(data["生成效果问题数"])
    if effect_count > 0:
        lines.extend(["", f"- 生成效果问题：{effect_count} 个", f"  {data['生成效果说明']}"])
        problem_count += 1

    reference_count = to_int(data["参考图策略问题数"])
    if reference_count > 0:
        lines.extend(["", f"- 参考图策略问题：{reference_count} 个", f"  {data['参考图策略说明']}"])
        problem_count += 1

    if problem_count == 0:
        lines.append("- 无")

    note = str(data["备注"] or "").strip()
    if note:
        lines.extend(["", f"说明：{note}"])

    return "\n".join(lines)


def render_report(report_date, rows):
    chunks = [f"# AI 视频制作日报｜{report_date}", ""]
    for idx, row in enumerate(rows):
        if idx:
            chunks.extend(["", "---", ""])
        chunks.append(render_one(row))
    return "\n".join(chunks)


def send_report(config, report_date, markdown):
    group_id = str(config.get("target_group_id") or "").strip()
    robot_code = str(config.get("robot_code") or "").strip()
    if not group_id or not robot_code:
        raise RuntimeError(
            "target_group_id and robot_code are required for --send. "
            "Fill config/ai_video_daily_report.json first."
        )

    return run_dws(
        [
            "chat",
            "message",
            "send-by-bot",
            "--group",
            group_id,
            "--robot-code",
            robot_code,
            "--title",
            f"AI 视频制作日报｜{report_date}",
            "--text",
            markdown,
        ]
    )


def send_review_message(config, title, markdown):
    group_id = str(config.get("approval_group_id") or "").strip()
    user_id = str(config.get("review_user_id") or "").strip()
    robot_code = str(config.get("robot_code") or "").strip()
    if not robot_code:
        raise RuntimeError("robot_code is required for approval messages.")

    if group_id:
        if str(config.get("approval_send_mode") or "").strip().lower() == "user":
            return run_dws(
                [
                    "chat",
                    "message",
                    "send",
                    "--group",
                    group_id,
                    "--title",
                    title,
                    "--text",
                    markdown,
                ]
            )

        return run_dws(
            [
                "chat",
                "message",
                "send-by-bot",
                "--group",
                group_id,
                "--robot-code",
                robot_code,
                "--title",
                title,
                "--text",
                markdown,
            ]
        )

    if not user_id:
        raise RuntimeError(
            "review_user_id or approval_group_id is required for approval messages. "
            "Fill config/ai_video_daily_report.json first."
        )

    return run_dws(
        [
            "chat",
            "message",
            "send-by-bot",
            "--users",
            user_id,
            "--robot-code",
            robot_code,
            "--title",
            title,
            "--text",
            markdown,
        ]
    )


def mark_sent(config, rows):
    now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    for row in rows:
        run_dws(
            [
                "sheet",
                "range",
                "update",
                "--node",
                config["sheet_node_id"],
                "--sheet-id",
                config["sheet_id"],
                "--range",
                f"U{row.row_number}:V{row.row_number}",
                "--values",
                json.dumps([["是", now]], ensure_ascii=False),
            ]
        )


def approval_key(report_date, rows):
    row_part = ",".join(str(row.row_number) for row in rows)
    return f"{report_date}:{row_part}"


def request_approval(config, report_date, rows, markdown, force=False):
    state = load_state(config)
    pending = state.get("pending")
    key = approval_key(report_date, rows)
    if pending and pending.get("status") == "pending" and pending.get("key") == key and not force:
        print(
            f"Approval already pending for {report_date}. "
            "Use --force-approval to resend the preview.",
            file=sys.stderr,
        )
        return 0

    requested_at = now_shanghai()
    approval_text = "\n".join(
        [
            f"# AI 视频日报待确认｜{report_date}",
            "",
            "下面是准备发送到目标群的内容：",
            "",
            markdown,
            "",
            "---",
            "",
            "回复方式：",
            "- `OK`：确认发送到目标群",
            "- `修改：你的意见`：暂停发送，我按意见调整后重新发你确认",
            "- `不发`：取消本次播报",
        ]
    )
    send_review_message(config, f"AI 视频日报待确认｜{report_date}", approval_text)
    state["pending"] = {
        "key": key,
        "date": report_date,
        "row_numbers": [row.row_number for row in rows],
        "requested_at": requested_at,
        "status": "pending",
        "markdown": markdown,
        "feedback": "",
    }
    save_state(config, state)
    print(f"Approval preview sent for {report_date}.")
    return 0


def extract_texts(value):
    texts = []
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            texts.append(stripped)
    elif isinstance(value, list):
        for item in value:
            texts.extend(extract_texts(item))
    elif isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in {"text", "content", "msgtext", "markdown", "title", "body"}:
                texts.extend(extract_texts(item))
            elif isinstance(item, (dict, list)):
                texts.extend(extract_texts(item))
    return texts


def normalize_command(text):
    return str(text or "").strip().replace(" ", "").replace("　", "").lower()


def parse_message_time(value):
    text = str(value or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    return None


def is_allowed_reviewer(message, allowed_open_id):
    if not allowed_open_id:
        return True
    return str(message.get("senderOpenDingTalkId") or "").strip() == allowed_open_id


def filter_messages_for_approval(messages, requested_at, allowed_open_id):
    requested = parse_message_time(requested_at)
    filtered = []
    for message in messages:
        if not is_allowed_reviewer(message, allowed_open_id):
            continue
        created = parse_message_time(message.get("createTime"))
        if requested and created and created < requested:
            continue
        filtered.append(message)
    return filtered


def classify_reply(messages):
    ok_set = {"ok", "okay", "确认", "确认发送", "发送", "同意", "可以", "通过"}
    reject_set = {"no", "不发", "取消", "不要发", "先不发", "作废"}
    feedback_prefixes = ("修改", "不ok", "不OK", "意见", "调整", "改成", "重写", "不对")

    for message in messages:
        for text in extract_texts(message):
            command = normalize_command(text)
            if command in ok_set:
                return "ok", text
            if command in reject_set:
                return "reject", text
            if text.strip().startswith(feedback_prefixes):
                return "feedback", text.strip()
    return "", ""


def read_approval_messages(config, requested_at):
    group_id = str(config.get("approval_group_id") or "").strip()
    if group_id:
        response = run_dws(
            [
                "chat",
                "message",
                "list",
                "--group",
                group_id,
                "--time",
                requested_at,
                "--forward=true",
                "--limit",
                "50",
            ]
        )
        result = response.get("result") or {}
        return result.get("messages") or []

    bot_open_id = str(config.get("review_bot_open_dingtalk_id") or "").strip()
    if not bot_open_id:
        raise RuntimeError("review_bot_open_dingtalk_id is required to check approval replies.")

    response = run_dws(
        [
            "chat",
            "message",
            "list-direct",
            "--open-dingtalk-id",
            bot_open_id,
            "--time",
            requested_at,
            "--forward=true",
            "--limit",
            "20",
        ]
    )
    result = response.get("result") or {}
    return result.get("messages") or []


def check_approval(config):
    state = load_state(config)
    pending = state.get("pending")
    if not pending:
        print("No pending approval.")
        return 0

    if pending.get("status") == "approved_waiting_target":
        if not str(config.get("target_group_id") or "").strip():
            print("Approval is waiting for target_group_id. Not sent.")
            return 0

        report_date = pending["date"]
        rows = [row for row in read_rows(config) if row.row_number in set(pending["row_numbers"])]
        send_report(config, report_date, pending["markdown"])
        mark_sent(config, rows)
        pending["status"] = "sent"
        pending["sent_at"] = now_shanghai()
        save_state(config, state)
        send_review_message(
            config,
            f"AI 视频日报已发送｜{report_date}",
            "目标群已配置，已将之前确认通过的日报发送到正式群，并已回写表格播报状态。",
        )
        print(f"Sent approved report row(s) for {report_date}.")
        return 0

    if pending.get("status") != "pending":
        print("No pending approval.")
        return 0

    messages = filter_messages_for_approval(
        read_approval_messages(config, pending["requested_at"]),
        pending["requested_at"],
        str(config.get("review_user_open_dingtalk_id") or "").strip(),
    )
    action, text = classify_reply(messages)
    if not action:
        print("No approval reply yet.")
        return 0

    if action == "feedback":
        pending["status"] = "needs_revision"
        pending["feedback"] = text
        pending["feedback_at"] = now_shanghai()
        save_state(config, state)
        send_review_message(
            config,
            f"AI 视频日报已暂停｜{pending['date']}",
            "收到修改意见，已暂停发送到群。\n\n"
            f"你的意见：{text}\n\n"
            "我会按意见调整后，再重新发你确认。",
        )
        print("Approval paused for revision.")
        return 0

    if action == "reject":
        pending["status"] = "rejected"
        pending["rejected_at"] = now_shanghai()
        pending["reply"] = text
        save_state(config, state)
        send_review_message(
            config,
            f"AI 视频日报已取消｜{pending['date']}",
            f"收到 `{text}`，本次播报已取消，不会发送到群。",
        )
        print("Approval rejected.")
        return 0

    report_date = pending["date"]
    if not str(config.get("target_group_id") or "").strip():
        pending["status"] = "approved_waiting_target"
        pending["approved_at"] = now_shanghai()
        pending["reply"] = text
        save_state(config, state)
        send_review_message(
            config,
            f"AI 视频日报已确认｜{report_date}",
            f"收到 `{text}`，已确认通过。\n\n"
            "但当前还没有配置目标播报群，所以没有发送到正式群。\n"
            "请先确认目标群后再启用正式发送。",
        )
        print("Approval OK, but target_group_id is not configured. Not sent.")
        return 0

    rows = [row for row in read_rows(config) if row.row_number in set(pending["row_numbers"])]
    send_report(config, report_date, pending["markdown"])
    mark_sent(config, rows)
    pending["status"] = "sent"
    pending["sent_at"] = now_shanghai()
    pending["reply"] = text
    save_state(config, state)
    send_review_message(
        config,
        f"AI 视频日报已发送｜{report_date}",
        f"收到 `{text}`，已发送到目标群，并已回写表格播报状态。",
    )
    print(f"Approval OK. Sent {len(rows)} report row(s) for {report_date}.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Read DingTalk Sheet AI video report rows and broadcast them.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to config JSON.")
    parser.add_argument("--date", help="Report date, e.g. 2026-07-08. Defaults to today in config timezone.")
    parser.add_argument("--yesterday", action="store_true", help="Use yesterday in config timezone as report date.")
    parser.add_argument(
        "--previous-report-day",
        action="store_true",
        help="Use workday report date: Monday uses last Friday; other days use yesterday.",
    )
    parser.add_argument("--send", action="store_true", help="Actually send to DingTalk. Default is dry-run preview.")
    parser.add_argument("--request-approval", action="store_true", help="Send preview to reviewer instead of group.")
    parser.add_argument("--check-approval", action="store_true", help="Check reviewer reply. OK sends to group.")
    parser.add_argument("--force-approval", action="store_true", help="Resend approval preview even if one is pending.")
    parser.add_argument("--include-sent", action="store_true", help="Include rows already marked as sent.")
    parser.add_argument("--no-mark-sent", action="store_true", help="Do not update sent status after a successful send.")
    args = parser.parse_args()

    config_path = Path(args.config)
    config = json.loads(config_path.read_text(encoding="utf-8"))

    if args.check_approval:
        return check_approval(config)

    if args.date:
        report_date = normalize_date(args.date)
    elif args.previous_report_day:
        report_date = previous_report_date_for_timezone(config.get("timezone", "Asia/Shanghai"))
    elif args.yesterday:
        report_date = date_for_timezone(config.get("timezone", "Asia/Shanghai"), offset_days=-1)
    else:
        report_date = today_for_timezone(config.get("timezone", "Asia/Shanghai"))

    rows = pick_rows(read_rows(config), report_date, include_sent=args.include_sent)
    if not rows:
        print(
            f"No confirmed unsent report rows found for {report_date}. "
            "Check 日期、播报确认、是否已播报 columns.",
            file=sys.stderr,
        )
        if args.request_approval:
            return 0
        return 2

    markdown = render_report(report_date, rows)
    print(markdown)

    if args.request_approval:
        return request_approval(config, report_date, rows, markdown, force=args.force_approval)

    if not args.send:
        print("\n[DRY-RUN] Not sent. Add --send after preview is correct.", file=sys.stderr)
        return 0

    send_report(config, report_date, markdown)
    if not args.no_mark_sent:
        mark_sent(config, rows)
    print(f"\nSent {len(rows)} report row(s) for {report_date}.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
