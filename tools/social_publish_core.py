#!/usr/bin/env python3
import json
import mimetypes
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(ROOT))

from tools.cloudinary_upload_server import cloudinary_config, missing_config, upload_to_cloudinary
from tools.image_to_youtube_video import download_image, ffmpeg_available, make_video_from_image, save_uploaded_image
from tools.meta_publish_server import accounts, publish_facebook, publish_instagram, token as meta_token
from tools.publish_records import log_publish_record, recent_publish_records
from tools.youtube_publish import upload_video, youtube_available


ACCOUNT_PRESETS = {
    "hk": {
        "label": "HK",
        "page_ids": ["332404978089672"],
        "ig_user_ids": ["17841475031302059"],
    },
    "global": {
        "label": "Global",
        "page_ids": ["472909179237589"],
        "ig_user_ids": ["17841475491235920"],
    },
    "both": {
        "label": "HK + Global",
        "page_ids": ["332404978089672", "472909179237589"],
        "ig_user_ids": ["17841475031302059", "17841475491235920"],
    },
}

TRIAL_LINKS = {
    "hk": {
        "facebook": "https://vip-think.com/maliang/popularize-60839.html",
        "instagram": "https://vip-think.com/maliang/popularize-59548.html",
        "youtube": "https://vip-think.com/maliang/popularize-62177.html",
    },
    "global": {
        "facebook": "https://vip-think.com/maliang/popularize-60808.html",
        "instagram": "https://vip-think.com/maliang/popularize-65748.html",
        "youtube": "https://vip-think.com/maliang/popularize-62110.html",
    },
}

DEFAULT_HK_CAPTION = """【🍧暑假差倍問題重難點挑戰🔥】
尾後加 0 速算小捷徑🔢｜搵出隱藏原數💯

⌛暑期係思維養成黃金階段，差倍題最容易睇漏倍數關係😵‍💫
🐢逐個試數又慢又易錯，遇到大數字更加容易計亂失分❌

📌吃透「多出嚟嗰幾份」核心邏輯，複雜數字都可以一步步化簡✨
📊訓練抽象推理能力，答題效率自然提升🏆

✅今日例題【差倍思維強化訓練🧮】
一個數尾後加 0 之後，比原數增加 1107，請問原數係幾多？🤔

✔ 尾後加 0，即係新數變成原數嘅 10 倍
✔ 新數比原數多出 9 份
✔ 9 份 = 1107，所以 1 份 = 123 ✅

💡解題小貼士：唔好急住除大數，先搵清楚「差值」對應幾多份🔎
💬可以同小朋友一齊試做，再留言分享你嘅解題步驟！

👉想體驗更多趣味數學題，系統提升兒童數學思維？
👩🏻‍🏫免費體驗鏈接： https://vip-think.com/maliang/popularize-60839.html
官網：https://vipthink.hk/
YT：@VIP THINK - HK
IG：@vipthink.hk
FB：@VIP THINK - hk

#暑期數學思維 #小學差倍問題 #兒童邏輯訓練 #VIPTHINK #每日數學題 #親子數學"""

DEFAULT_GLOBAL_CAPTION = """【🍧暑假差倍问题重难点挑战🔥】
尾后加 0 速算小捷径🔢｜找出隐藏原数💯

⌛暑期是思维养成黄金阶段，差倍题最容易看漏倍数关系😵‍💫
🐢逐个试数又慢又容易错，遇到大数字更容易算乱丢分❌

📌吃透“多出来的几份”核心逻辑，复杂数字也可以一步步化简✨
📊训练抽象推理能力，答题效率自然提升🏆

✅今日例题【差倍思维强化训练🧮】
一个数尾后加 0 之后，比原数增加 1107，请问原数是多少？🤔

✔ 尾后加 0，就是新数变成原数的 10 倍
✔ 新数比原数多出 9 份
✔ 9 份 = 1107，所以 1 份 = 123 ✅

💡解题小贴士：不要急着除大数，先找清楚“差值”对应几份🔎
💬可以和孩子一起试做，再留言分享你的解题步骤！

👉想体验更多趣味数学题，系统提升儿童数学思维？
👩🏻‍🏫免费体验链接： https://vip-think.com/maliang/popularize-60839.html
官网｜https://global.vip-think.com/
IG｜@vipthink.global
YT｜@VIP THINK - Global
FB｜@VIP THINK - Global

#暑期数学思维 #小学差倍问题 #儿童逻辑训练 #VIPTHINK #每日数学题 #亲子数学"""

DEFAULT_HK_YOUTUBE_TITLE = "暑假差倍問題挑戰｜尾後加 0 點樣快速算？"
DEFAULT_HK_YOUTUBE_DESCRIPTION = """尾後加 0 的差倍題，關鍵係先搵清楚「多出嚟嗰幾份」。

今次用一條例題，帶小朋友理解倍數關係同差值對應。

免費體驗鏈接：
https://vip-think.com/maliang/popularize-60839.html

#小學數學 #差倍問題 #數學思維 #VIPTHINK"""

DEFAULT_GLOBAL_YOUTUBE_TITLE = "暑假差倍问题挑战｜尾后加 0 怎么快速算？"
DEFAULT_GLOBAL_YOUTUBE_DESCRIPTION = """尾后加 0 的差倍题，关键是先找清楚“多出来的几份”。

这次用一道例题，带孩子理解倍数关系和差值对应。

免费体验链接：
https://vip-think.com/maliang/popularize-60839.html

#小学数学 #差倍问题 #数学思维 #VIPTHINK"""


def is_url(value):
    return value.startswith("http://") or value.startswith("https://")


def region_for_page_id(page_id):
    if page_id in ACCOUNT_PRESETS["global"]["page_ids"]:
        return "global"
    return "hk"


def region_for_ig_user_id(ig_user_id):
    if ig_user_id in ACCOUNT_PRESETS["global"]["ig_user_ids"]:
        return "global"
    return "hk"


def trial_link(region, platform):
    return TRIAL_LINKS[region][platform]


def apply_platform_trial_link(text, region, platform):
    url = trial_link(region, platform)
    pattern = r"https://vip-think\.com/maliang/popularize-\d+\.html"
    if re.search(pattern, text):
        return re.sub(pattern, url, text)
    label = "免費體驗鏈接" if region == "hk" else "免费体验链接"
    return text.rstrip() + f"\n\n👩🏻‍🏫{label}： {url}"


def platform_captions(captions):
    return {
        region: {
            "facebook": apply_platform_trial_link(caption, region, "facebook"),
            "instagram": apply_platform_trial_link(caption, region, "instagram"),
        }
        for region, caption in captions.items()
    }


def links_from_results(results):
    links = []
    image_url = results.get("image_url")
    if image_url:
        links.append({"label": "Cloudinary 图片链接", "url": image_url})
    for item_result in results.get("facebook", []):
        result = item_result.get("result", {})
        if result.get("photo_url"):
            links.append({"label": f"Facebook {item_result.get('region', '')} 图片链接", "url": result["photo_url"]})
        if result.get("possible_post_url"):
            links.append({"label": f"Facebook {item_result.get('region', '')} 帖子链接", "url": result["possible_post_url"]})
    for item_result in results.get("instagram", []):
        result = item_result.get("result", {})
        if result.get("permalink"):
            links.append({"label": f"Instagram {item_result.get('region', '')} 链接", "url": result["permalink"]})
    youtube = results.get("youtube") or {}
    if youtube.get("result", {}).get("watch_url"):
        links.append({"label": f"YouTube {youtube.get('region', '')} 链接", "url": youtube["result"]["watch_url"]})
    return links


def prepare_image(image):
    if not image:
        raise ValueError("请提供本地图片路径或 https 图片链接。")
    if is_url(image):
        return image, download_image(image)

    path = Path(image).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"图片不存在：{path}")
    data = path.read_bytes()
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    saved_path = save_uploaded_image(path.name, data)
    upload_result = upload_to_cloudinary(path.name, content_type, data)
    image_url = upload_result.get("secure_url")
    if not image_url:
        raise RuntimeError("Cloudinary 上传成功但没有返回 secure_url：" + json.dumps(upload_result, ensure_ascii=False))
    return image_url, saved_path


def status_report():
    cloudinary = cloudinary_config()
    missing_cloudinary = missing_config(cloudinary)
    report = {
        "cloudinary": {
            "ok": not missing_cloudinary,
            "cloud_name": cloudinary.get("cloud_name") or "",
            "folder": cloudinary.get("folder") or "",
            "missing": missing_cloudinary,
        },
        "meta": {
            "ok": bool(meta_token()),
            "accounts": [],
        },
        "youtube": {
            "ok": youtube_available(),
        },
        "ffmpeg": {
            "ok": ffmpeg_available(),
        },
    }
    if report["meta"]["ok"]:
        data = accounts()
        if "error" in data:
            report["meta"]["ok"] = False
            report["meta"]["error"] = data["error"]
        else:
            for item in data.get("data", []):
                ig = item.get("instagram_business_account") or {}
                report["meta"]["accounts"].append(
                    {
                        "facebook_page": item.get("name"),
                        "page_id": item.get("id"),
                        "instagram": ig.get("username") or ig.get("name") or "",
                        "ig_user_id": ig.get("id") or "",
                    }
                )
    return report


def publish_image_bundle(
    *,
    preset,
    image,
    hk_caption=None,
    global_caption=None,
    publish_facebook_enabled=True,
    publish_instagram_enabled=True,
    publish_youtube_enabled=False,
    youtube_privacy="private",
    youtube_publish_at=None,
    hk_youtube_title=None,
    hk_youtube_description=None,
    global_youtube_title=None,
    global_youtube_description=None,
    dry_run=True,
):
    if preset not in ACCOUNT_PRESETS:
        raise ValueError("preset 必须是 hk、global 或 both。")

    captions = {
        "hk": (hk_caption or DEFAULT_HK_CAPTION).strip(),
        "global": (global_caption or DEFAULT_GLOBAL_CAPTION).strip(),
    }
    captions_by_platform = platform_captions(captions)
    youtube_titles = {
        "hk": (hk_youtube_title or DEFAULT_HK_YOUTUBE_TITLE).strip(),
        "global": (global_youtube_title or DEFAULT_GLOBAL_YOUTUBE_TITLE).strip(),
    }
    youtube_descriptions = {
        "hk": apply_platform_trial_link(
            (hk_youtube_description or DEFAULT_HK_YOUTUBE_DESCRIPTION).strip(),
            "hk",
            "youtube",
        ),
        "global": apply_platform_trial_link(
            (global_youtube_description or DEFAULT_GLOBAL_YOUTUBE_DESCRIPTION).strip(),
            "global",
            "youtube",
        ),
    }

    targets = ACCOUNT_PRESETS[preset]
    page_ids = targets["page_ids"] if publish_facebook_enabled else []
    ig_user_ids = targets["ig_user_ids"] if publish_instagram_enabled else []
    youtube_region = "global" if preset == "global" else "hk"

    plan = {
        "preset": preset,
        "facebook_page_ids": page_ids,
        "instagram_user_ids": ig_user_ids,
        "publish_youtube": publish_youtube_enabled,
        "youtube_region": youtube_region if publish_youtube_enabled else "",
        "youtube_privacy": youtube_privacy if publish_youtube_enabled else "",
        "youtube_publish_at": youtube_publish_at or "",
    }
    if dry_run:
        return {
            "dry_run": True,
            "message": "这是预览，没有发布。真正发布需要 --yes。",
            "plan": plan,
            "base_captions": captions,
            "captions": captions_by_platform,
            "youtube": {
                "title": youtube_titles[youtube_region],
                "description": youtube_descriptions[youtube_region],
            }
            if publish_youtube_enabled
            else None,
        }

    image_url, source_image_path = prepare_image(image)
    results = {
        "image_url": image_url,
        "facebook": [],
        "instagram": [],
        "youtube": None,
    }
    for page_id in page_ids:
        region = region_for_page_id(page_id)
        caption = captions_by_platform[region]["facebook"]
        results["facebook"].append(
            {
                "page_id": page_id,
                "region": region,
                "caption_used": caption,
                "result": publish_facebook(page_id, image_url, caption),
            }
        )
    for ig_user_id in ig_user_ids:
        region = region_for_ig_user_id(ig_user_id)
        caption = captions_by_platform[region]["instagram"]
        results["instagram"].append(
            {
                "ig_user_id": ig_user_id,
                "region": region,
                "caption_used": caption,
                "result": publish_instagram(ig_user_id, image_url, caption),
            }
        )
    if publish_youtube_enabled:
        video_path = make_video_from_image(
            source_image_path,
            size="720x1280",
            duration=7.5,
            title_prefix=f"youtube-image-video-{youtube_region}",
        )
        youtube_result = upload_video(
            video_path,
            title=youtube_titles[youtube_region],
            description=youtube_descriptions[youtube_region],
            privacy=youtube_privacy,
            publish_at=youtube_publish_at,
        )
        results["youtube"] = {
            "region": youtube_region,
            "source_image": str(source_image_path),
            "video_path": str(video_path),
            "result": youtube_result,
        }

    links = links_from_results(results)
    record = log_publish_record(
        {
            "preset": preset,
            "caption": captions["global"] if preset == "global" else captions["hk"],
            "hk_caption": captions["hk"],
            "global_caption": captions["global"],
            "captions_by_platform": captions_by_platform,
            "page_ids": page_ids,
            "ig_user_ids": ig_user_ids,
            "publish_youtube": publish_youtube_enabled,
            "youtube_privacy": youtube_privacy if publish_youtube_enabled else "",
            "youtube_publish_at": youtube_publish_at or "",
            "links": links,
            "results": results,
        }
    )
    return {
        "dry_run": False,
        "plan": plan,
        "links": links,
        "record": record,
        "results": results,
    }


def recent_records(limit=10):
    return recent_publish_records(limit)
