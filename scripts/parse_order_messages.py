#!/usr/bin/env python3
"""Parse DingTalk order messages into a reconciliation CSV."""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PEOPLE_PATH = ROOT / "config" / "people_departments.csv"
PRICES_PATH = ROOT / "config" / "prices.csv"

OUTPUT_FIELDS = [
    "下单时间",
    "下单人",
    "所属部门",
    "交付时间",
    "类型",
    "数量",
    "具体内容",
    "单价",
    "总价",
]

INTERNAL_FIELDS = [
    "原始消息",
    "解析状态",
    "缺失字段",
]

FIELD_ALIASES = {
    "下单时间": "下单时间",
    "下单人": "下单人",
    "所属部门": "所属部门",
    "部门": "所属部门",
    "交付时间": "交付时间",
    "交付日期": "交付时间",
    "类型": "类型",
    "数量": "数量",
    "具体内容": "具体内容",
    "内容": "具体内容",
    "单价": "单价",
    "总价": "总价",
    "金额": "总价",
    "总金额": "总价",
}


@dataclass
class ParsedEnvelope:
    order_time: str
    sender: str
    message: str


def load_people(path: Path) -> dict[str, str]:
    people: dict[str, str] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            people[row["下单人"].strip()] = row["所属部门"].strip()
    return people


def load_prices(path: Path) -> dict[str, float]:
    prices: dict[str, float] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            item_type = row["类型"].strip()
            raw_price = row["单价"].strip()
            if item_type and raw_price:
                prices[item_type] = float(raw_price)
    return prices


def normalize_date(raw: str, fallback_year: int | None = None) -> str:
    value = raw.strip()
    value = re.sub(r"\s+\d{1,2}:\d{2}(:\d{2})?$", "", value)
    value = value.replace("-", "/")

    parts = value.split("/")
    try:
        if len(parts) == 3:
            year, month, day = [int(x) for x in parts]
        elif len(parts) == 2 and fallback_year:
            year = fallback_year
            month, day = [int(x) for x in parts]
        else:
            return raw.strip()
        return f"{year}/{month}/{day}"
    except ValueError:
        return raw.strip()


def parse_envelope(line: str) -> ParsedEnvelope:
    parts = [part.strip() for part in line.split("|", 2)]
    if len(parts) == 3:
        order_time = normalize_date(parts[0])
        return ParsedEnvelope(order_time=order_time, sender=parts[1], message=parts[2])
    return ParsedEnvelope(order_time="", sender="", message=line.strip())


def detect_type(message: str, prices: dict[str, float]) -> str:
    for item_type in sorted(prices, key=len, reverse=True):
        if item_type in message:
            return item_type

    explicit = re.search(r"类型\s*[:：]\s*([\w\u4e00-\u9fff]+)", message)
    return explicit.group(1).strip() if explicit else ""


def detect_quantity(message: str) -> int | None:
    with_unit = re.search(r"(?<![/\d])(\d+)\s*(条|个|张|套|份|支|版)(?![\w])", message)
    if with_unit:
        return int(with_unit.group(1))

    explicit = re.search(r"数量\s*[:：]?\s*(\d+)", message)
    if explicit:
        return int(explicit.group(1))

    return None


def detect_delivery_date(message: str, order_time: str) -> str:
    fallback_year = None
    order_parts = order_time.split("/")
    if len(order_parts) == 3 and order_parts[0].isdigit():
        fallback_year = int(order_parts[0])

    match = re.search(
        r"(交付|完成|截止|ddl|DDL)\s*[:：]?\s*"
        r"(\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}[/-]\d{1,2})",
        message,
    )
    if not match:
        return ""
    return normalize_date(match.group(2), fallback_year=fallback_year)


def clean_content(message: str, item_type: str) -> str:
    text = message
    text = re.sub(r"@\S*机器人", " ", text)
    text = re.sub(r"<@[^>]+>", " ", text)
    text = re.sub(r"\b下单\b|下单", " ", text)
    text = re.sub(r"(?<![/\d])\d+\s*(条|个|张|套|份|支|版)(?![\w])", " ", text)
    text = re.sub(
        r"(交付|完成|截止|ddl|DDL)\s*[:：]?\s*"
        r"(\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}[/-]\d{1,2})",
        " ",
        text,
    )
    text = re.sub(r"[，,。；;]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    if item_type:
        text = re.sub(rf"^{re.escape(item_type)}\s+", "", text.strip(), count=1)
    return text.strip()


def parse_order(line: str, people: dict[str, str], prices: dict[str, float]) -> dict[str, str] | None:
    envelope = parse_envelope(line)
    return parse_order_envelope(envelope, people, prices)


def parse_order_envelope(
    envelope: ParsedEnvelope,
    people: dict[str, str],
    prices: dict[str, float],
) -> dict[str, str] | None:
    if "下单" not in envelope.message:
        return None
    if re.search(r"(不是|无需|不用|不需要|取消).{0,4}下单", envelope.message):
        return None

    labeled = parse_labeled_order_message(envelope, people, prices)
    if labeled is not None:
        return labeled

    structured = parse_structured_order_row(envelope, people, prices)
    if structured is not None:
        return structured

    return None


def parse_labeled_order_message(
    envelope: ParsedEnvelope,
    people: dict[str, str],
    prices: dict[str, float],
) -> dict[str, str] | None:
    labels = sorted(FIELD_ALIASES, key=len, reverse=True)
    pattern = re.compile(
        r"(?:^|[\s,，;；])"
        rf"(?P<label>{'|'.join(re.escape(label) for label in labels)})"
        r"\s*[:：=]\s*"
    )

    text = re.sub(r"^.*?下单\s*", "", envelope.message.strip(), count=1)
    matches = list(pattern.finditer(text))
    if not matches:
        return None

    row = {field: "" for field in OUTPUT_FIELDS}
    for index, match in enumerate(matches):
        label = FIELD_ALIASES[match.group("label")]
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        value = text[match.end() : end]
        row[label] = clean_labeled_value(value)

    return finalize_structured_row(row, envelope, people, prices)


def parse_structured_order_row(
    envelope: ParsedEnvelope,
    people: dict[str, str],
    prices: dict[str, float],
) -> dict[str, str] | None:
    """Support a full sheet row after "下单", separated by tabs or spaces."""
    text = re.sub(r"^.*?下单\s*", "", envelope.message.strip(), count=1)
    if "\t" in text:
        columns = [column.strip() for column in text.split("\t")]
    else:
        columns = re.split(r"\s+", text)
    columns = [column for column in columns if column]
    if not columns:
        return None
    columns[0] = re.sub(r"^下单\s*", "", columns[0]).strip()

    if len(columns) != len(OUTPUT_FIELDS):
        return None

    row = dict(zip(OUTPUT_FIELDS, columns))
    return finalize_structured_row(row, envelope, people, prices)


def clean_labeled_value(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^[,，;；\s]+|[,，;；\s]+$", "", value)
    return value.strip()


def finalize_structured_row(
    row: dict[str, str],
    envelope: ParsedEnvelope,
    people: dict[str, str],
    prices: dict[str, float],
) -> dict[str, str]:
    row = {field: (row.get(field, "") or "").strip() for field in OUTPUT_FIELDS}

    if not row["下单时间"]:
        row["下单时间"] = envelope.order_time
    else:
        row["下单时间"] = normalize_date(row["下单时间"])

    if not row["下单人"]:
        row["下单人"] = envelope.sender

    if not row["所属部门"]:
        row["所属部门"] = people.get(row["下单人"]) or people.get(envelope.sender) or people.get("默认", "待确认")

    fallback_year = None
    order_parts = row["下单时间"].split("/")
    if len(order_parts) == 3 and order_parts[0].isdigit():
        fallback_year = int(order_parts[0])
    if row["交付时间"]:
        row["交付时间"] = normalize_date(row["交付时间"], fallback_year=fallback_year)

    quantity_match = re.search(r"\d+", row["数量"])
    if quantity_match:
        row["数量"] = quantity_match.group(0)

    if not row["单价"] and row["类型"] in prices:
        row["单价"] = format_number(prices[row["类型"]])
    if not row["总价"]:
        row["总价"] = calculate_amount(row["单价"], row["数量"])

    missing = [field for field in OUTPUT_FIELDS if not row.get(field)]
    return {
        **row,
        "原始消息": envelope.message,
        "解析状态": "OK" if not missing else "待补充",
        "缺失字段": "、".join(missing),
    }


def calculate_amount(unit_price: str, quantity: str) -> str:
    try:
        price = float(unit_price)
        count = float(quantity)
    except ValueError:
        return ""
    return format_number(price * count)


def parse_order_fields(
    order_time: str,
    sender: str,
    message: str,
    people: dict[str, str] | None = None,
    prices: dict[str, float] | None = None,
) -> dict[str, str] | None:
    people = people if people is not None else load_people(PEOPLE_PATH)
    prices = prices if prices is not None else load_prices(PRICES_PATH)
    envelope = ParsedEnvelope(
        order_time=normalize_date(order_time),
        sender=sender.strip(),
        message=message.strip(),
    )
    return parse_order_envelope(envelope, people, prices)


def format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def output_row(row: dict[str, str]) -> dict[str, str]:
    projected = {field: row.get(field, "") for field in OUTPUT_FIELDS}
    if not projected["总价"] and row.get("金额"):
        projected["总价"] = row["金额"]
    return projected


def normalize_output_csv(path: Path) -> None:
    if not path.exists() or path.stat().st_size == 0:
        return

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames == OUTPUT_FIELDS:
            return
        rows = [output_row(row) for row in reader]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def parse_file(input_path: Path, output_path: Path) -> tuple[int, int]:
    people = load_people(PEOPLE_PATH)
    prices = load_prices(PRICES_PATH)

    rows: list[dict[str, str]] = []
    skipped = 0

    with input_path.open("r", encoding="utf-8-sig") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            row = parse_order(line, people, prices)
            if row is None:
                skipped += 1
            else:
                rows.append(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(output_row(row) for row in rows)

    return len(rows), skipped


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse supplier order messages into a CSV file.")
    parser.add_argument("input", help="Input text file. One message per line.")
    parser.add_argument("--output", default="output/orders.csv", help="Output CSV path.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    parsed, skipped = parse_file(input_path, output_path)
    print(f"parsed={parsed} skipped={skipped} output={output_path}")


if __name__ == "__main__":
    main()
