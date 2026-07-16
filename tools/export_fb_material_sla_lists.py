#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import importlib.util
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


DEFAULT_SOURCE = Path("/Users/yangyi/Desktop/03 批量上FB广告/fb_robot_broadcast.py")
DEFAULT_DB = Path("/Users/yangyi/Desktop/03 批量上FB广告/fb_new_creative_monitor.sqlite3")
DEFAULT_OUT = Path("/Users/yangyi/Documents/机器人播报")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export FB material-level SLA lists.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--since", default="2026-06-25")
    parser.add_argument("--until", default="2026-07-08")
    parser.add_argument("--future-until", default="2026-07-22")
    parser.add_argument("--sla-days", type=int, default=7)
    parser.add_argument("--account-aliases", default="7,8,9,27,18,23")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--image-library-root", default="/Volumes/海外投放素材库/图片素材/思维")
    parser.add_argument("--image-library-start-month", default="2026-07")
    parser.add_argument("--disable-image-library", action="store_true")
    return parser.parse_args()


def load_source(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("fb_robot_broadcast", path)
    if not spec or not spec.loader:
        raise RuntimeError(f"Cannot load source: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_day(value: str) -> date:
    year, month, day = [int(part) for part in value.split("-")]
    return date(year, month, day)


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def csv_row(row: dict[str, Any], source: Any) -> dict[str, Any]:
    material_date = row.get("material_date")
    base_date = source.comparison_date(row)
    library_final_date = row.get("library_final_date")
    library_production_date = row.get("library_production_date")
    first_action_date = row.get("first_action_date")
    created_date = row.get("created_date")
    adset_start_date = row.get("adset_start_date")
    return {
        "素材唯一键": row.get("material_group_key") or row.get("creative_key") or "",
        "判定结果": row.get("sla_status") or "",
        "用时天数": row.get("days_to_first_action"),
        "素材制作日期": material_date.isoformat() if material_date else "",
        "考核日期": base_date.isoformat() if base_date else "",
        "考核依据": row.get("sla_base_source") or "",
        "素材库状态": row.get("library_status") or "",
        "素材库制作日期": library_production_date.isoformat() if library_production_date else "",
        "素材库定稿日期": library_final_date.isoformat() if library_final_date else "",
        "素材库批次": row.get("library_batch_name") or "",
        "素材库文件": row.get("library_file_path") or "",
        "首次上线或排期日期": first_action_date.isoformat() if first_action_date else "",
        "首次动作类型": row.get("first_action_source") or "",
        "首次广告创建日期": created_date.isoformat() if created_date else "",
        "首次广告组排期日期": adset_start_date.isoformat() if adset_start_date else "",
        "账户": row.get("account_name") or "",
        "素材出现账户数": row.get("material_account_count") or "",
        "素材出现账户": row.get("material_accounts") or "",
        "同素材广告数": row.get("material_ad_count") or 1,
        "地区": row.get("region") or "",
        "素材类型": row.get("material_type") or "",
        "状态": row.get("effective_status") or "",
        "广告ID": row.get("ad_id") or "",
        "素材Key": row.get("creative_key") or "",
        "广告名称": row.get("ad_name") or "",
        "广告组名称": row.get("adset_name") or "",
        "广告系列名称": row.get("campaign_name") or "",
    }


def main() -> int:
    args = parse_args()
    source = load_source(Path(args.source))
    since = parse_day(args.since)
    until = parse_day(args.until)
    future_until = parse_day(args.future_until)
    selected_accounts = source.parse_account_filter(args.account_aliases)
    image_library_root = None if args.disable_image_library else Path(args.image_library_root)
    rows = source.load_rows(
        Path(args.db),
        since,
        until,
        future_until,
        False,
        args.sla_days,
        selected_accounts,
        image_library_root,
        args.image_library_start_month,
    )
    ok = [r for r in rows if str(r.get("sla_status") or "").startswith("达标")]
    over = [r for r in rows if str(r.get("sla_status") or "").startswith("超时")]
    pending_violation = [r for r in rows if str(r.get("sla_status") or "").startswith("违规")]
    early = [r for r in rows if "早于" in str(r.get("sla_status") or "")]
    base = Path(args.out_dir) / f"fb_new_creative_material_sla_lists_image_final_{since:%Y%m%d}_{until:%Y%m%d}"
    base.mkdir(parents=True, exist_ok=True)

    columns = [
        "素材唯一键",
        "判定结果",
        "用时天数",
        "素材制作日期",
        "考核日期",
        "考核依据",
        "素材库状态",
        "素材库制作日期",
        "素材库定稿日期",
        "素材库批次",
        "素材库文件",
        "首次上线或排期日期",
        "首次动作类型",
        "首次广告创建日期",
        "首次广告组排期日期",
        "账户",
        "素材出现账户数",
        "素材出现账户",
        "同素材广告数",
        "地区",
        "素材类型",
        "状态",
        "广告ID",
        "素材Key",
        "广告名称",
        "广告组名称",
        "广告系列名称",
    ]
    write_csv(base / f"达标素材名单_{len(ok)}.csv", [csv_row(r, source) for r in ok], columns)
    write_csv(base / f"超时素材名单_{len(over)}.csv", [csv_row(r, source) for r in over], columns)
    write_csv(base / f"待确认违规名单_{len(pending_violation)}.csv", [csv_row(r, source) for r in pending_violation], columns)
    write_csv(base / f"早于考核日期名单_{len(early)}.csv", [csv_row(r, source) for r in early], columns)
    write_csv(base / f"全部素材名单_{len(rows)}.csv", [csv_row(r, source) for r in rows], columns)

    by_account = Counter(r.get("account_name") or "未识别" for r in rows)
    by_region = Counter(r.get("region") or "未识别" for r in rows)
    by_type = Counter(r.get("material_type") or "未识别" for r in rows)
    by_sla = Counter(r.get("sla_status") or "未识别" for r in rows)
    by_library = Counter(r.get("library_status") or "未识别" for r in rows)
    readme = [
        f"# FB新制作素材名单｜{since.isoformat()} 至 {until.isoformat()}",
        "",
        f"- 新制作素材：{len(rows)} 个",
        f"- 达标：{len(ok)} 个",
        f"- 超时：{len(over)} 个",
        f"- 待确认违规：{len(pending_violation)} 个",
        f"- 早于考核日期：{len(early)} 个",
        f"- 涉及广告：{sum(int(r.get('material_ad_count') or 1) for r in rows)} 条",
        "",
        "## 口径",
        "",
        "- 新制作素材：广告名称里的完整素材制作日期落在本期窗口内。",
        "- 同一个素材：优先按广告名称去重；因为同一素材复投/复制广告时，Meta creative_key 可能变化。",
        "- 兜底规则：没有广告名称时，再用 Meta creative_key；还没有时，用账户、素材日期、广告系列和广告组兜底。",
        "- 6月制作素材：仍按广告名称/文件名里的制作日期计算 7 天。",
        "- 图片素材：从 2026-07-01 制作日期开始优先匹配素材库；匹配到定稿日期后，按定稿日期计算 7 天。",
        "- 视频素材：不走图片素材库，继续按广告名称/文件名里的日期计算。",
        "- 待确认素材：如果已经在 Meta 创建或排期，单独标为违规。",
        f"- 达标：首次上线或排期在考核日期后 {args.sla_days} 天内。",
        f"- 超时：首次上线或排期超过考核日期后 {args.sla_days} 天。",
        "",
        "## 文件",
        "",
        f"- 达标素材名单_{len(ok)}.csv",
        f"- 超时素材名单_{len(over)}.csv",
        f"- 待确认违规名单_{len(pending_violation)}.csv",
        f"- 早于考核日期名单_{len(early)}.csv",
        f"- 全部素材名单_{len(rows)}.csv",
        "",
        "## 汇总",
        "",
        "按账户：" + "；".join(f"{k} {v}" for k, v in by_account.most_common()),
        "按地区：" + "；".join(f"{k} {v}" for k, v in by_region.most_common()),
        "按素材类型：" + "；".join(f"{k} {v}" for k, v in by_type.most_common()),
        "按判定：" + "；".join(f"{k} {v}" for k, v in by_sla.most_common()),
        "按素材库：" + "；".join(f"{k} {v}" for k, v in by_library.most_common()),
        "",
    ]
    (base / "名单说明.md").write_text("\n".join(readme), encoding="utf-8")
    print(base)
    print(f"ok {len(ok)} over {len(over)} pending {len(pending_violation)} early {len(early)} all {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
