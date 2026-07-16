#!/usr/bin/env python3
"""Daily, evidence-backed Xiaohongshu content loop for VIPTHINK.

This is intentionally a small local workflow. It reads brand facts, product
updates, performance exports, competitor watchlists, and an optional asset
index, then produces a daily demand brief and a ranked publish package.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from xhs_auto_generator import load_config, make_local_draft


ROOT = Path(__file__).resolve().parent
INPUTS = ROOT / "inputs"
RUNS = ROOT / "runs"
MEMORY = ROOT / "memory"

FIELD_ALIASES = {
    "content_type": ["content_type", "内容类型", "类型", "内容形式"],
    "topic": ["topic", "选题", "内容主题", "内容方向"],
    "title": ["title", "标题", "笔记标题", "广告名称", "素材名称"],
    "views": ["views", "曝光", "阅读", "浏览量", "展示", "展现", "impressions"],
    "likes": ["likes", "点赞"],
    "comments": ["comments", "评论"],
    "shares": ["shares", "分享", "转发"],
    "saves": ["saves", "收藏"],
    "follows_gained": ["follows_gained", "涨粉", "新增粉丝"],
    "leads": ["leads", "线索", "约课", "报名", "转化"],
    "cost": ["cost", "消耗", "花费"],
}


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_markdown_files(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return [
        {"name": item.stem, "text": item.read_text(encoding="utf-8", errors="replace").strip()}
        for item in sorted(path.glob("*.md"))
        if item.name != "README.md"
    ]


def read_product_updates(path: Path) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    if not path.exists():
        return updates
    for item in sorted(path.glob("*.json")):
        payload = read_json(item, {})
        if isinstance(payload, list):
            updates.extend(entry for entry in payload if isinstance(entry, dict))
        elif isinstance(payload, dict):
            updates.append(payload)
    for item in read_markdown_files(path):
        updates.append({"name": item["name"], "priority": "medium", "facts": [item["text"]]})
    return updates


def matching_value(row: dict[str, str], aliases: list[str]) -> str:
    lowered = {key.strip().lower(): value for key, value in row.items() if key}
    for alias in aliases:
        if alias.lower() in lowered:
            return lowered[alias.lower()] or ""
    return ""


def as_number(value: str) -> float:
    text = str(value or "").replace(",", "").replace("%", "").strip()
    try:
        return float(text)
    except ValueError:
        return 0.0


def performance_rows(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not path.exists():
        return rows, warnings
    for file_path in sorted(path.glob("*.csv")):
        if file_path.name == "performance_template.csv":
            continue
        try:
            with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                for raw in reader:
                    normalized = {field: matching_value(raw, aliases) for field, aliases in FIELD_ALIASES.items()}
                    if not any(normalized.values()):
                        continue
                    for field in ("views", "likes", "comments", "shares", "saves", "follows_gained", "leads", "cost"):
                        normalized[field] = as_number(normalized[field])
                    normalized["source"] = file_path.name
                    normalized["source_level"] = str(raw.get("source_level") or "")
                    rows.append(normalized)
        except (OSError, csv.Error) as exc:
            warnings.append(f"无法读取 {file_path.name}: {exc}")
    return rows, warnings


def summarize_performance(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"state": "no_data", "post_count": 0, "by_type": [], "by_topic": []}

    groups: dict[str, list[float]] = defaultdict(list)
    topics: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        views = max(row["views"], 1.0)
        engagement = (row["likes"] + row["comments"] + row["shares"] + row["saves"]) / views
        save_rate = row["saves"] / views
        lead_rate = row["leads"] / views
        follow_rate = row["follows_gained"] / views
        # Value and conversion matter more than raw exposure for this content loop.
        score = engagement * 0.35 + save_rate * 0.35 + lead_rate * 0.2 + follow_rate * 0.1
        label = row["content_type"] or "未标注类型"
        topic = row["topic"] or row["title"] or "未标注选题"
        groups[label].append(score)
        topics[topic].append(score)

    def ranked(source: dict[str, list[float]], field: str) -> list[dict[str, Any]]:
        values = [
            {field: name, "samples": len(scores), "score": round(statistics.mean(scores), 5)}
            for name, scores in source.items()
        ]
        return sorted(values, key=lambda item: (item["score"], item["samples"]), reverse=True)

    return {
        "state": "usable" if len(rows) >= 5 else "limited",
        "post_count": len(rows),
        "by_type": ranked(groups, "content_type"),
        "by_topic": ranked(topics, "topic")[:10],
    }


def format_signal(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expose aggregate format evidence without treating it as post-level data."""
    signals: list[dict[str, Any]] = []
    for row in rows:
        if row.get("source_level") != "素材类型汇总":
            continue
        cost = max(float(row.get("cost") or 0), 1.0)
        signals.append({
            "format": row.get("content_type") or "未标注",
            "leads": int(float(row.get("leads") or 0)),
            "lead_cost": round(cost / max(float(row.get("leads") or 0), 1.0), 2),
        })
    return sorted(signals, key=lambda item: (item["lead_cost"], -item["leads"]))


def type_bonus(content_type: str, summary: dict[str, Any]) -> tuple[int, str]:
    ranked = summary.get("by_type", [])
    if summary.get("state") != "usable" or not ranked:
        return 0, "暂无足够自有表现数据，按品牌内容支柱做均衡探索"
    for position, item in enumerate(ranked[:3], start=1):
        if item["content_type"] == content_type:
            bonus = {1: 18, 2: 10, 3: 5}[position]
            return bonus, f"自有数据中“{content_type}”表现位列第{position}"
    return 0, "自有数据尚未证明该类型优先"


def select_seeds(seeds: list[dict[str, Any]], count: int, performance: dict[str, Any], products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    active_facts = " ".join(
        str(value)
        for product in products
        for value in [product.get("name", ""), product.get("audience", ""), *product.get("facts", [])]
    )
    scored: list[dict[str, Any]] = []
    for seed in seeds:
        bonus, reason = type_bonus(str(seed["type"]), performance)
        product_bonus = 0
        if active_facts and any(term in active_facts for term in (seed.get("pillar", ""), seed.get("keyword", ""))):
            product_bonus = 12
        entry = dict(seed)
        entry["strategy_score"] = int(seed.get("priority", 70)) + bonus + product_bonus
        entry["strategy_reason"] = reason if not product_bonus else f"{reason}；匹配当前新品或推广重点"
        scored.append(entry)

    # Keep the daily package varied: no more than three pieces of one type.
    selected: list[dict[str, Any]] = []
    type_counts: Counter[str] = Counter()
    for seed in sorted(scored, key=lambda item: item["strategy_score"], reverse=True):
        if type_counts[seed["type"]] >= 3:
            continue
        selected.append(seed)
        type_counts[seed["type"]] += 1
        if len(selected) >= count:
            break
    return selected


def asset_matches(asset_index: dict[str, Any], tags: Iterable[str]) -> list[str]:
    wanted = {str(tag) for tag in tags}
    scored: list[tuple[int, str]] = []
    for item in asset_index.get("items", []):
        item_tags = set(item.get("tags", []))
        if "竞品广告" in item_tags:
            continue
        overlap = wanted & item_tags
        if overlap:
            # Prefer the most specifically tagged asset, then use the path as a
            # stable tie-breaker so each run is reproducible.
            scored.append((len(overlap), str(item.get("path", ""))))
    return [path for _, path in sorted(scored, key=lambda item: (-item[0], item[1]))[:3]]


def top_publish_drafts(drafts: list[dict[str, Any]], publish_count: int) -> list[dict[str, Any]]:
    """Return high-scoring candidates while keeping the package type-diverse."""
    eligible = [draft for draft in drafts if draft["publish_recommendation"] != "reject"]
    ranked = sorted(eligible, key=lambda item: item["overall_score"], reverse=True)
    selected: list[dict[str, Any]] = []
    used_types: set[str] = set()
    for draft in ranked:
        if draft["content_type"] in used_types:
            continue
        selected.append(draft)
        used_types.add(draft["content_type"])
        if len(selected) >= publish_count:
            return selected
    for draft in ranked:
        if draft in selected:
            continue
        selected.append(draft)
        if len(selected) >= publish_count:
            break
    return selected


def write_input_summary(path: Path, brand_rules: dict[str, Any], products: list[dict[str, Any]], performance: dict[str, Any], watchlist: dict[str, Any], asset_index: dict[str, Any], warnings: list[str]) -> None:
    lines = [
        "# Input Summary",
        "",
        f"Brand: {brand_rules.get('brand_name', 'VIPTHINK')}",
        f"Product updates read: {len(products)}",
        f"Performance rows read: {performance.get('post_count', 0)} ({performance.get('state', 'no_data')})",
        f"Competitors watched: {len(watchlist.get('competitors', []))}",
        f"Indexed visual assets: {asset_index.get('item_count', 0)}",
        "",
        "## Product Updates",
    ]
    if products:
        for product in products:
            lines.append(f"- {product.get('name', '未命名重点')} ({product.get('priority', 'medium')})")
    else:
        lines.append("- 未提供新品资料，使用品牌长期内容支柱。")
    if warnings:
        lines.extend(["", "## Warnings", *[f"- {warning}" for warning in warnings]])
    signals = performance.get("format_signals", [])
    if signals:
        lines.extend(["", "## Format Signals", ""])
        lines.extend(f"- {item['format']}: {item['leads']} leads, lead cost {item['lead_cost']}" for item in signals)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_content_demand(path: Path, selected: list[dict[str, Any]], performance: dict[str, Any], products: list[dict[str, Any]], watchlist: dict[str, Any]) -> None:
    mix = Counter(seed["type"] for seed in selected)
    lines = [
        "# Daily Content Demand",
        "",
        "## Today’s Objective",
        "",
        "用具体家长场景和可执行方法建立收藏价值；在不夸大效果的前提下，为直播小班和思维训练建立理解。",
        "",
        "## Demand Mix",
        "",
        *[f"- {content_type}: {count}篇" for content_type, count in mix.items()],
        "",
        "## Why This Mix",
        "",
        f"- 自有数据状态：{performance.get('state', 'no_data')}，已读取{performance.get('post_count', 0)}条记录。",
        f"- 竞品监控：{len(watchlist.get('competitors', []))}个核心账号，按周刷新。",
        f"- 新品/活动重点：{len(products)}条。",
    ]
    signals = performance.get("format_signals", [])
    if signals:
        lines.extend(["", "## 素材形式信号", "", "以下为素材类型汇总，不等同于单条内容归因。"])
        lines.extend(f"- {item['format']}: {item['leads']}个约课，约课成本 {item['lead_cost']}" for item in signals)
    lines.extend(["", "## Ranked Topics", ""])
    for position, seed in enumerate(selected, start=1):
        lines.append(f"{position}. {seed['topic']}（{seed['type']}，策略分 {seed['strategy_score']}）")
        lines.append(f"   - {seed['strategy_reason']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_candidates_csv(path: Path, drafts: list[dict[str, Any]]) -> None:
    fields = [
        "content_id", "content_type", "topic", "title_1", "title_2", "title_3", "cover_text", "quality_score",
        "risk_level", "publish_recommendation", "strategy_score", "overall_score", "strategy_reason", "evidence", "asset_paths",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for draft in drafts:
            titles = list(draft.get("title_options", [])) + ["", "", ""]
            writer.writerow(
                {
                    "content_id": draft["content_id"],
                    "content_type": draft["content_type"],
                    "topic": draft["topic"],
                    "title_1": titles[0],
                    "title_2": titles[1],
                    "title_3": titles[2],
                    "cover_text": draft["cover_text"],
                    "quality_score": draft["quality_score"],
                    "risk_level": draft["risk_level"],
                    "publish_recommendation": draft["publish_recommendation"],
                    "strategy_score": draft["strategy_score"],
                    "overall_score": draft["overall_score"],
                    "strategy_reason": draft["strategy_reason"],
                    "evidence": " | ".join(draft.get("evidence", [])),
                    "asset_paths": " | ".join(draft.get("asset_paths", [])),
                }
            )


def write_drafts_json(path: Path, drafts: list[dict[str, Any]]) -> None:
    path.write_text(json.dumps({"drafts": drafts}, ensure_ascii=False, indent=2), encoding="utf-8")


def write_publish_pack(path: Path, drafts: list[dict[str, Any]], visual: dict[str, Any], publish_count: int) -> None:
    top = top_publish_drafts(drafts, publish_count)
    lines = [
        "# VIPTHINK Xiaohongshu Publish Pack",
        "",
        "只发布经过事实确认且风险为 green 的内容；yellow 内容必须人工复核后才能使用。",
        "",
        "## Visual Rules",
        "",
        f"- Canvas: {visual['canvas']['xiaohongshu_width']}x{visual['canvas']['xiaohongshu_height']}",
        f"- Primary: {visual['colors']['primary_green']} | Accent: {visual['colors']['accent_yellow']} | Background: {visual['colors']['background_gray']}",
        f"- Font: {visual['typography']['preferred']} (fallback: {visual['typography']['fallback']})",
        f"- Logo: {visual['logo_rules']['corner_badge']}",
    ]
    if not top:
        lines.extend(["", "没有通过基础质量与风险门槛的候选内容。"])
    for position, draft in enumerate(top, start=1):
        lines.extend(
            [
                "",
                f"## {position}. {draft['content_id']} | {draft['topic']}",
                "",
                f"Overall score: {draft['overall_score']} | Quality: {draft['quality_score']} | Risk: {draft['risk_level']}",
                "",
                "Title options:",
                *[f"- {title}" for title in draft["title_options"]],
                "",
                f"Cover: {draft['cover_text']}",
                "",
                "Carousel:",
                *[f"{number}. {page}" for number, page in enumerate(draft["carousel_pages"], start=1)],
                "",
                "Body:",
                "",
                draft["body"],
                "",
                f"Hashtags: {' '.join(draft['hashtags'])}",
                f"CTA: {draft['cta']}",
                "",
                f"Strategy: {draft['strategy_reason']}",
                f"Evidence: {' | '.join(draft['evidence'])}",
                f"Visual asset candidates: {' | '.join(draft['asset_paths']) if draft['asset_paths'] else '请先运行 xhs_asset_index.py'}",
                f"Rendered images: {' | '.join(draft.get('image_paths', [])) if draft.get('image_paths') else '本次未生成PNG'}",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_feedback_template(path: Path) -> None:
    fields = ["content_id", "publish_date", "publish_url", "views_day_1", "likes_day_1", "comments_day_1", "shares_day_1", "saves_day_1", "follows_day_1", "leads_day_1", "notes"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        csv.DictWriter(handle, fieldnames=fields).writeheader()


def parse_date(value: str) -> str:
    if value == "today":
        return dt.date.today().isoformat()
    return dt.date.fromisoformat(value).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the VIPTHINK daily Xiaohongshu content loop.")
    parser.add_argument("--date", default="today", help="YYYY-MM-DD or today")
    parser.add_argument("--count", type=int, default=10, help="Candidate draft count")
    parser.add_argument("--publish-count", type=int, default=3, help="Number of ranked publish candidates")
    parser.add_argument("--render-images", action="store_true", help="Render PNG slides for the ranked publish candidates")
    args = parser.parse_args()

    run_date = parse_date(args.date)
    run_dir = RUNS / run_date
    run_dir.mkdir(parents=True, exist_ok=True)

    config = load_config(ROOT / "xhs_config.json")
    brand_rules = read_json(INPUTS / "brand" / "brand_rules.json", {})
    visual = read_json(INPUTS / "brand" / "visual_guidelines.json", {})
    seeds = read_json(INPUTS / "content_seeds.json", [])
    watchlist = read_json(INPUTS / "competitor_data" / "competitor_watchlist.json", {})
    asset_index = read_json(MEMORY / "asset_index.json", {"item_count": 0, "items": []})
    products = read_product_updates(INPUTS / "product_updates")
    rows, warnings = performance_rows(INPUTS / "performance_data")
    performance = summarize_performance(rows)
    performance["format_signals"] = format_signal(rows)

    selected = select_seeds(seeds, max(args.count, 1), performance, products)
    drafts: list[dict[str, Any]] = []
    for index, seed in enumerate(selected, start=1):
        draft = make_local_draft(seed, config, index, content_id_prefix=f"XHS-{run_date.replace('-', '')}")
        draft["strategy_score"] = seed["strategy_score"]
        draft["strategy_reason"] = seed["strategy_reason"]
        draft["evidence"] = seed.get("evidence", [])
        draft["asset_paths"] = asset_matches(asset_index, seed.get("asset_tags", []))
        draft["overall_score"] = round(draft["quality_score"] * 0.65 + draft["strategy_score"] * 0.35, 1)
        drafts.append(draft)

    write_input_summary(run_dir / "input_summary.md", brand_rules, products, performance, watchlist, asset_index, warnings)
    write_content_demand(run_dir / "content_demand.md", selected, performance, products, watchlist)
    if args.render_images:
        from xhs_image_renderer import render_drafts

        rendered = render_drafts(drafts, visual, asset_index, run_dir / "images", args.publish_count)
        for draft in drafts:
            draft["image_paths"] = rendered.get(draft["content_id"], [])
    write_candidates_csv(run_dir / "candidates.csv", drafts)
    write_drafts_json(run_dir / "drafts.json", drafts)
    write_publish_pack(run_dir / "publish_pack.md", drafts, visual, args.publish_count)
    write_feedback_template(run_dir / "feedback.csv")

    print(f"Generated daily loop for {run_date}")
    print(f"Run folder: {run_dir}")
    print(f"Publish pack: {run_dir / 'publish_pack.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
