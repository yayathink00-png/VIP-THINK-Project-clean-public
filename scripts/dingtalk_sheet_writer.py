#!/usr/bin/env python3
"""Append parsed order rows to a DingTalk online sheet."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from dws_util import resolve_dws_path
from parse_order_messages import OUTPUT_FIELDS, output_row


ROOT = Path(__file__).resolve().parents[1]


def run_dws(args: list[str]) -> dict:
    completed = subprocess.run(
        [resolve_dws_path(), *args, "--format", "json"],
        cwd=str(ROOT),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stdout or completed.stderr)
    return json.loads(completed.stdout)


def append_order_to_sheet(row: dict[str, str]) -> bool:
    node_id = os.getenv("DINGTALK_SHEET_NODE_ID", "").strip()
    sheet_id = os.getenv("DINGTALK_SHEET_ID", "").strip()
    if not node_id or not sheet_id:
        return False

    projected = output_row(row)
    values = [[projected.get(field, "") for field in OUTPUT_FIELDS]]
    payload = run_dws(
        [
            "sheet",
            "append",
            "--node",
            node_id,
            "--sheet-id",
            sheet_id,
            "--values",
            json.dumps(values, ensure_ascii=False),
        ]
    )
    apply_center_style(node_id, sheet_id, payload.get("a1Notation", ""))
    return True


def apply_center_style(node_id: str, sheet_id: str, a1_notation: str) -> None:
    if not a1_notation:
        return
    run_dws(
        [
            "sheet",
            "range",
            "set-style",
            "--node",
            node_id,
            "--sheet-id",
            sheet_id,
            "--range",
            a1_notation,
            "--h-align",
            "center",
            "--v-align",
            "middle",
        ]
    )
