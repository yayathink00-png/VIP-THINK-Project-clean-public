#!/usr/bin/env python3
"""
Fast Xiaohongshu content automation MVP.

Default mode uses local templates so it runs immediately with no dependencies.
AI mode can be enabled with --ai when OPENAI_API_KEY is available.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import random
import re
import sys
import textwrap
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = ROOT / "xhs_config.json"


TOPIC_BANK = [
    {
        "type": "家长痛点",
        "topic": "孩子上课听懂了，回家还是不会做",
        "cover": "孩子不是笨，是没学会拆题",
        "angle": "把答案导向改成思路导向",
        "keyword": "拆题",
    },
    {
        "type": "学习方法",
        "topic": "CPA数学启蒙：先实物，再图形，最后算式",
        "cover": "数学启蒙别急着刷题",
        "angle": "先理解数量关系，再进入抽象计算",
        "keyword": "CPA",
    },
    {
        "type": "误区纠正",
        "topic": "家长只盯答案，孩子会越来越怕数学",
        "cover": "别只盯答案",
        "angle": "用提问替代催促",
        "keyword": "讲题",
    },
    {
        "type": "家长痛点",
        "topic": "孩子一遇难题就说不会",
        "cover": "一遇难题就放弃？",
        "angle": "先帮孩子找到第一小步",
        "keyword": "难题",
    },
    {
        "type": "学习方法",
        "topic": "家长在家用3个问题训练孩子表达思路",
        "cover": "这样问，孩子更愿意思考",
        "angle": "让孩子说出条件、步骤和理由",
        "keyword": "提问",
    },
    {
        "type": "误区纠正",
        "topic": "编程启蒙不是越早写代码越好",
        "cover": "编程启蒙先练逻辑",
        "angle": "先练顺序、分类、条件和分解任务",
        "keyword": "编程",
    },
    {
        "type": "学习方法",
        "topic": "在家用小游戏训练逻辑思维",
        "cover": "在家练逻辑的3个小游戏",
        "angle": "把找规律、分类、讲顺序变成亲子练习",
        "keyword": "游戏",
    },
    {
        "type": "资料领取",
        "topic": "4-12岁孩子数学思维自查",
        "cover": "数学思维自查表",
        "angle": "用读题、表达、迁移、抗挫四项观察孩子",
        "keyword": "自查",
    },
    {
        "type": "案例故事",
        "topic": "孩子从猜答案到愿意讲思路",
        "cover": "会讲思路更重要",
        "angle": "奖励思考过程，而不是只奖励正确答案",
        "keyword": "思路",
    },
    {
        "type": "资料领取",
        "topic": "孩子数学思维和编程启蒙怎么选",
        "cover": "先判断，再选课",
        "angle": "按孩子当前卡点选择训练方向",
        "keyword": "判断",
    },
]


TITLE_PATTERNS = [
    "{pain}，问题可能不在努力",
    "{cover}",
    "很多家长忽略了：{angle}",
    "{topic}，先试试这个方法",
    "别急着报课，先看懂这个信号",
]


BODY_TEMPLATES = {
    "家长痛点": (
        "很多家长看到孩子{short_topic}，第一反应是着急纠正，甚至会忍不住说“你上课不是听懂了吗”。"
        "但这个问题背后，常常不是孩子不努力，而是缺少可执行的方法。"
        "可以先做一个小动作：让孩子把题目里的条件圈出来，再用自己的话说一遍“题目要我求什么”。"
        "如果这一步说不清，先别急着算。等孩子能讲出条件、问题和第一步，后面的练习才更有效。"
    ),
    "学习方法": (
        "{topic}，关键不是让孩子一下子做很多题，而是把方法变成孩子能理解的步骤。"
        "比如先用积木、水果、路线图这类看得见的东西讲清楚，再让孩子画图表达，最后才进入题目练习。"
        "家长陪练时可以少讲答案，多问一句“你为什么这样分”。"
        "孩子能说出自己的判断依据，说明他不是在背题，而是在建立思考路径。"
    ),
    "误区纠正": (
        "很多家庭在学习上最容易踩的坑，是只看结果，不看过程。"
        "{topic}就是典型例子。家长可以把“你怎么又错了”换成“你刚才是怎么想的”。"
        "再追问一步：“你是从哪句话判断出来的？”这个问题能帮孩子回到题目本身。"
        "这个变化很小，但能让孩子从害怕被批评，转向愿意表达。先保护思考意愿，再训练方法，学习才更容易持续。"
    ),
    "案例故事": (
        "我们经常看到一种情况：孩子不是完全不会，而是习惯猜答案。"
        "遇到{short_topic}时，如果只纠正对错，孩子下次还是容易卡住。"
        "更好的做法是让孩子复述题目、说出条件、讲清第一步。比如他说“我不知道怎么算”，家长可以先问“你觉得这题在问数量、顺序，还是比较”。"
        "刚开始说得慢也没关系，能表达思路，本身就是更稳定的开始。"
    ),
    "资料领取": (
        "{topic}，可以先不用急着下结论。家长可以观察几个点：孩子能不能读懂题，"
        "能不能说出思路，能不能把旧方法用到新题里，遇到难题会不会直接放弃。"
        "这些表现比单次分数更能反映学习状态。建议先用一张观察表记录一周，再判断孩子更需要读题训练、逻辑训练，还是表达训练。"
    ),
}


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def risk_check(text: str, config: dict[str, Any]) -> tuple[str, str, str]:
    red_words = config["risk_rules"]["red_words"]
    yellow_words = config["risk_rules"]["yellow_words"]

    hit_red = [word for word in red_words if word in text]
    if hit_red:
        return "red", f"命中高风险词：{', '.join(hit_red)}", "reject"

    hit_yellow = [word for word in yellow_words if word in text]
    if hit_yellow:
        return "yellow", f"命中需复核词：{', '.join(hit_yellow)}", "review"

    return "green", "未命中主要风险词，仍需检查事实和错别字", "publish"


def quality_check(draft: dict[str, Any], config: dict[str, Any]) -> tuple[int, str, str]:
    body = str(draft.get("body", ""))
    cover = str(draft.get("cover_text", ""))
    titles = " ".join(draft.get("title_options", []))
    carousel = draft.get("carousel_pages", [])
    cta = str(draft.get("cta", ""))
    risk = str(draft.get("risk_level", "green"))
    text = "\n".join([cover, titles, body, cta])

    score = 0
    reasons: list[str] = []

    if 180 <= len(body) <= 420:
        score += 15
        reasons.append("正文长度适合小红书")
    else:
        reasons.append("正文长度需要调整")

    concrete_words = ["孩子", "家长", "题目", "条件", "思路", "步骤", "先", "再", "比如"]
    concrete_hits = [word for word in concrete_words if word in text]
    score += min(len(concrete_hits), 6) * 4
    if len(concrete_hits) >= 4:
        reasons.append("场景和对象比较具体")
    else:
        reasons.append("场景还不够具体")

    action_words = ["问", "圈", "画", "说", "记录", "观察", "分类", "复述", "练"]
    action_hits = [word for word in action_words if word in text]
    score += min(len(action_hits), 5) * 5
    if len(action_hits) >= 3:
        reasons.append("包含可执行动作")
    else:
        reasons.append("可执行动作偏少")

    if 5 <= len(carousel) <= 7:
        score += 15
        reasons.append("轮播页数合理")
    else:
        reasons.append("轮播结构需要补齐")

    if 6 <= len(cover) <= 18:
        score += 8
        reasons.append("封面文案长度合适")
    else:
        reasons.append("封面文案可能太长或太短")

    if any(mark in titles for mark in ["？", "别", "先", "不是", "为什么"]):
        score += 8
        reasons.append("标题有明确钩子")
    else:
        reasons.append("标题钩子不够强")

    if cta and any(word in cta for word in ["评论", "收藏", "清单", "观察表"]):
        score += 8
        reasons.append("CTA明确且较轻")
    else:
        reasons.append("CTA不够清楚")

    if risk == "green":
        score += 10
    elif risk == "yellow":
        score -= 5
        reasons.append("有需人工复核风险")
    else:
        score = min(score, 45)
        reasons.append("高风险内容不进入发布")

    score = max(0, min(100, score))
    gate = config.get("quality_gate", {})
    excellent_min = int(gate.get("excellent_min_score", 85))
    publish_min = int(gate.get("publish_min_score", 78))
    review_min = int(gate.get("review_min_score", 65))

    if score >= excellent_min:
        level = "excellent"
    elif score >= publish_min:
        level = "publishable"
    elif score >= review_min:
        level = "needs_edit"
    else:
        level = "weak"

    return score, level, "；".join(reasons)


def final_recommendation(risk: str, quality_score: int, quality_level: str, config: dict[str, Any]) -> str:
    gate = config.get("quality_gate", {})
    publish_min = int(gate.get("publish_min_score", 78))
    review_min = int(gate.get("review_min_score", 65))
    if risk == "red":
        return "reject"
    if risk == "yellow" or quality_level == "needs_edit":
        return "review"
    if quality_score >= publish_min:
        return "publish"
    if quality_score >= review_min:
        return "review"
    return "reject"


def clean_short_topic(topic: str) -> str:
    topic = re.sub(r"^孩子", "", topic)
    return topic[:18]


def make_titles(item: dict[str, Any]) -> list[str]:
    custom_titles = item.get("title_options")
    if isinstance(custom_titles, list) and custom_titles:
        return [str(title) for title in custom_titles[:3]]
    pain = item["topic"].replace("孩子", "孩子")
    values = {
        "pain": pain,
        "cover": item["cover"],
        "angle": item["angle"],
        "topic": item["topic"],
    }
    titles = [pattern.format(**values) for pattern in TITLE_PATTERNS]
    return titles[:3]


def make_carousel(item: dict[str, Any]) -> list[str]:
    custom_pages = item.get("carousel_pages")
    if isinstance(custom_pages, list) and 5 <= len(custom_pages) <= 7:
        return [str(page) for page in custom_pages]

    steps = item.get("steps")
    if isinstance(steps, list) and len(steps) >= 3:
        return [
            item["cover"],
            f"家长常遇到：{item['topic']}。",
            f"卡点不是只看结果，而是：{item['angle']}。",
            f"第1步：{steps[0]}",
            f"第2步：{steps[1]}",
            f"第3步：{steps[2]}",
            f"想要清单，可以评论“{item['keyword']}”。",
        ]
    return [
        item["cover"],
        f"很多家长会遇到：{item['topic']}。",
        f"真正要处理的不是情绪，而是：{item['angle']}。",
        "先把问题拆成孩子能完成的一小步。",
        "再让孩子说出自己的想法和理由。",
        "最后用练习巩固，而不是直接追求速度。",
        f"想要清单，可以评论“{item['keyword']}”。",
    ]


def make_body(item: dict[str, Any]) -> str:
    custom_body = item.get("body")
    if isinstance(custom_body, str) and custom_body.strip():
        return custom_body.strip()

    steps = item.get("steps")
    example = str(item.get("example", ""))
    if isinstance(steps, list) and len(steps) >= 3:
        step_text = "；".join(str(step) for step in steps[:3])
        if item["type"] == "家长痛点":
            return (
                f"孩子出现“{clean_short_topic(item['topic'])}”时，先别急着把答案讲出来。"
                f"很多时候，孩子卡住不是不会算，而是还没把题目的信息变成自己的思路。"
                f"家长可以按这三个动作陪一遍：{step_text}。"
                f"{example}"
                "整个过程只需要几分钟，但重点是让孩子说出判断依据，而不是替他完成题目。"
            )
        if item["type"] == "学习方法":
            return (
                f"{item['topic']}，重点不是增加练习量，而是让孩子看见每一步为什么这样做。"
                f"可以按这个顺序练：{step_text}。"
                f"{example}"
                "当孩子能说出条件、方法和理由，才说明他正在建立可迁移的思考路径。"
            )
        if item["type"] == "误区纠正":
            return (
                f"“{item['topic']}”很常见，但只催结果通常会让孩子更不愿意表达。"
                f"可以换成三个具体动作：{step_text}。"
                f"{example}"
                "先让孩子保有尝试的空间，再回到方法本身，学习更容易持续。"
            )
        if item["type"] == "案例故事":
            return (
                f"当孩子出现“{clean_short_topic(item['topic'])}”的变化时，真正值得保留的不是一句夸奖，而是过程。"
                f"家长可以观察：{step_text}。"
                f"{example}"
                "用过程记录替代一次对错，才能看见孩子是否真的在形成自己的解题模型。"
            )
        return (
            f"{item['topic']}，建议先用一周时间记录，而不是凭一次作业就给孩子下结论。"
            f"重点看这三件事：{step_text}。"
            f"{example}"
            "观察清楚之后，再判断孩子更需要读题、表达还是逻辑训练。"
        )

    return BODY_TEMPLATES[item["type"]].format(
        topic=item["topic"],
        short_topic=clean_short_topic(item["topic"]),
    )


def make_local_draft(
    item: dict[str, str],
    config: dict[str, Any],
    index: int,
    content_id_prefix: str = "XHS",
) -> dict[str, Any]:
    """Create one validated draft from a supplied topic seed.

    The daily loop uses this entry point to inject product, performance, and
    competitor-informed topic seeds without duplicating the local draft rules.
    """
    content_type = item["type"]
    body = make_body(item)
    cta = f"评论“{item['keyword']}”，我整理一份相关练习/观察清单。"
    full_text = "\n".join([item["cover"], body, cta])
    risk, reason, recommendation = risk_check(full_text, config)
    draft: dict[str, Any] = {
        "content_id": f"{content_id_prefix}-{index:03d}",
        "content_type": content_type,
        "topic": item["topic"],
        "title_options": make_titles(item),
        "cover_text": item["cover"],
        "carousel_pages": make_carousel(item),
        "body": body,
        "hashtags": [
            "#数学思维",
            "#少儿编程",
            "#家长必看",
            "#学习方法",
            "#在线教育",
            "#思维训练",
        ],
        "cta": cta,
        "risk_level": risk,
        "risk_reason": reason,
    }
    quality_score, quality_level, quality_reason = quality_check(draft, config)
    draft["quality_score"] = quality_score
    draft["quality_level"] = quality_level
    draft["quality_reason"] = quality_reason
    draft["publish_recommendation"] = final_recommendation(risk, quality_score, quality_level, config)
    if recommendation == "reject":
        draft["publish_recommendation"] = "reject"
    return draft


def make_local_drafts(config: dict[str, Any], count: int) -> list[dict[str, Any]]:
    bank = TOPIC_BANK.copy()
    random.shuffle(bank)
    selected = [bank[i % len(bank)] for i in range(count)]
    return [make_local_draft(item, config, index) for index, item in enumerate(selected, start=1)]


def build_ai_prompt(config: dict[str, Any], count: int) -> str:
    competitors = "、".join(config["competitors"])
    content_types = "、".join(config["content_types"])
    red_words = "、".join(config["risk_rules"]["red_words"])
    return textwrap.dedent(
        f"""
        你是小红书在线教育内容运营。

        品牌信息：
        - 品类：{config['brand']['category']}
        - 用户：{config['brand']['audience']}
        - 转化目标：{config['brand']['conversion']}

        竞品灵感来源：{competitors}
        内容类型只能从这里选：{content_types}

        生成 {count} 条小红书图文笔记草稿。

        每条必须包含这些字段：
        content_id, content_type, topic, title_options(3个), cover_text,
        carousel_pages(5-7页), body(180-350字), hashtags(6-10个), cta,
        risk_level(green/yellow/red), risk_reason,
        quality_score(0-100), quality_level(excellent/publishable/needs_edit/weak),
        quality_reason, publish_recommendation(publish/review/reject)

        高质量标准：
        - 痛点必须具体到一个家长日常场景，不要泛泛说“学习不好”
        - 正文必须给出可执行动作，例如怎么问、怎么拆题、怎么观察
        - 轮播图要有递进：钩子 -> 痛点 -> 原因 -> 方法 -> 例子 -> CTA
        - 标题和封面必须一眼看懂，不能像课程广告
        - 每条都要有保存价值，读完能马上用
        - 宁可少写，也不要输出空泛鸡汤

        禁止：
        - 复制竞品原文
        - 贬低竞品
        - 使用这些高风险词：{red_words}
        - 承诺具体提分或保证效果
        - 使用真实孩子身份信息

        输出严格 JSON，格式为：
        {{"drafts":[...]}}
        """
    ).strip()


def call_openai(prompt: str, model: str) -> dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    payload = {
        "model": model,
        "input": prompt,
        "temperature": 0.7,
        "max_output_tokens": 9000,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = json.loads(resp.read().decode("utf-8"))

    text = raw.get("output_text")
    if not text:
        pieces: list[str] = []
        for item in raw.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"}:
                    pieces.append(content.get("text", ""))
        text = "\n".join(pieces).strip()

    if not text:
        raise RuntimeError("OpenAI response did not contain text")

    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def normalize_ai_drafts(payload: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    raw_drafts = payload.get("drafts")
    if not isinstance(raw_drafts, list):
        raise RuntimeError("AI response JSON must contain drafts list")

    drafts: list[dict[str, Any]] = []
    for index, draft in enumerate(raw_drafts, start=1):
        text_parts = [
            str(draft.get("cover_text", "")),
            str(draft.get("body", "")),
            str(draft.get("cta", "")),
        ]
        risk, reason, recommendation = risk_check("\n".join(text_parts), config)
        draft["content_id"] = draft.get("content_id") or f"XHS-{index:03d}"
        draft["risk_level"] = risk if risk == "red" else draft.get("risk_level", risk)
        draft["risk_reason"] = reason if risk != "green" else draft.get("risk_reason", reason)
        quality_score, quality_level, quality_reason = quality_check(draft, config)
        draft["quality_score"] = quality_score
        draft["quality_level"] = quality_level
        draft["quality_reason"] = quality_reason
        draft["publish_recommendation"] = final_recommendation(risk, quality_score, quality_level, config)
        if recommendation == "reject":
            draft["publish_recommendation"] = "reject"
        drafts.append(draft)
    return drafts


def write_markdown(drafts: list[dict[str, Any]], output_path: Path, generated_at: str) -> None:
    lines = [
        f"# Xiaohongshu Auto Batch",
        "",
        f"Generated at: {generated_at}",
        "",
        "## Summary",
        "",
        "| ID | Type | Topic | Cover | Quality | Risk | Recommendation |",
        "|---|---|---|---|---:|---|---|",
    ]
    for draft in drafts:
        lines.append(
            "| {content_id} | {content_type} | {topic} | {cover_text} | {quality_score} | {risk_level} | {publish_recommendation} |".format(
                **draft
            )
        )

    for draft in drafts:
        lines.extend(
            [
                "",
                f"## {draft['content_id']} - {draft.get('topic', '')}",
                "",
                f"Type: {draft.get('content_type', '')}",
                "",
                "Title options:",
            ]
        )
        for title in draft.get("title_options", []):
            lines.append(f"- {title}")
        lines.extend(["", f"Cover: {draft.get('cover_text', '')}", "", "Carousel:"])
        for i, page in enumerate(draft.get("carousel_pages", []), start=1):
            lines.append(f"{i}. {page}")
        lines.extend(
            [
                "",
                "Body:",
                "",
                str(draft.get("body", "")),
                "",
                "Hashtags:",
                " ".join(draft.get("hashtags", [])),
                "",
                f"CTA: {draft.get('cta', '')}",
                "",
                f"Risk: {draft.get('risk_level', '')}",
                "",
                f"Risk reason: {draft.get('risk_reason', '')}",
                "",
                f"Quality: {draft.get('quality_score', '')} / {draft.get('quality_level', '')}",
                "",
                f"Quality reason: {draft.get('quality_reason', '')}",
                "",
                f"Recommendation: {draft.get('publish_recommendation', '')}",
            ]
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(drafts: list[dict[str, Any]], output_path: Path) -> None:
    fields = [
        "content_id",
        "content_type",
        "topic",
        "title_1",
        "title_2",
        "title_3",
        "cover_text",
        "body",
        "hashtags",
        "cta",
        "quality_score",
        "quality_level",
        "quality_reason",
        "risk_level",
        "risk_reason",
        "publish_recommendation",
    ]
    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for draft in drafts:
            titles = list(draft.get("title_options", []))[:3]
            titles += [""] * (3 - len(titles))
            writer.writerow(
                {
                    "content_id": draft.get("content_id", ""),
                    "content_type": draft.get("content_type", ""),
                    "topic": draft.get("topic", ""),
                    "title_1": titles[0],
                    "title_2": titles[1],
                    "title_3": titles[2],
                    "cover_text": draft.get("cover_text", ""),
                    "body": draft.get("body", ""),
                    "hashtags": " ".join(draft.get("hashtags", [])),
                    "cta": draft.get("cta", ""),
                    "quality_score": draft.get("quality_score", ""),
                    "quality_level": draft.get("quality_level", ""),
                    "quality_reason": draft.get("quality_reason", ""),
                    "risk_level": draft.get("risk_level", ""),
                    "risk_reason": draft.get("risk_reason", ""),
                    "publish_recommendation": draft.get("publish_recommendation", ""),
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Xiaohongshu draft batch.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to config JSON")
    parser.add_argument("--count", type=int, default=10, help="Number of drafts to generate")
    parser.add_argument("--out-dir", default=str(ROOT / "outputs"), help="Output directory")
    parser.add_argument("--ai", action="store_true", help="Use OpenAI API instead of local templates")
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"))
    args = parser.parse_args()

    config = load_config(Path(args.config))
    generated_at = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.ai:
        prompt = build_ai_prompt(config, args.count)
        try:
            payload = call_openai(prompt, args.model)
            drafts = normalize_ai_drafts(payload, config)
        except (RuntimeError, urllib.error.URLError, json.JSONDecodeError) as exc:
            print(f"AI generation failed, using local templates instead: {exc}", file=sys.stderr)
            drafts = make_local_drafts(config, args.count)
    else:
        drafts = make_local_drafts(config, args.count)

    md_path = out_dir / f"xhs_batch_{stamp}.md"
    csv_path = out_dir / f"xhs_batch_{stamp}.csv"
    write_markdown(drafts, md_path, generated_at)
    write_csv(drafts, csv_path)

    latest_md = out_dir / "latest.md"
    latest_csv = out_dir / "latest.csv"
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_csv.write_text(csv_path.read_text(encoding="utf-8-sig"), encoding="utf-8-sig")

    print(f"Generated {len(drafts)} drafts")
    print(f"Markdown: {md_path}")
    print(f"CSV: {csv_path}")
    print(f"Latest: {latest_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
