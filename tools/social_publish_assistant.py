#!/usr/bin/env python3
import argparse
import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(ROOT))

from tools.social_publish_core import publish_image_bundle, recent_records, status_report
from tools.youtube_publish import exchange_auth_code, token_info, upload_video, youtube_auth_url, youtube_paths


def print_json(payload):
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def read_text_arg(value):
    if not value:
        return None
    if value.startswith("@"):
        return Path(value[1:]).expanduser().read_text(encoding="utf-8")
    return value


def normalize_publish_at(value):
    if not value:
        return None
    cleaned = value.strip()
    if cleaned.endswith("Z"):
        return cleaned
    if "T" not in cleaned and " " in cleaned:
        cleaned = cleaned.replace(" ", "T", 1)
    parsed = dt.datetime.fromisoformat(cleaned)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    return parsed.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def cmd_status(_args):
    print_json(status_report())


def cmd_recent(args):
    print_json(recent_records(args.limit))


def cmd_publish_image(args):
    result = publish_image_bundle(
        preset=args.region,
        image=args.image,
        hk_caption=read_text_arg(args.hk_caption),
        global_caption=read_text_arg(args.global_caption),
        publish_facebook_enabled=not args.no_facebook,
        publish_instagram_enabled=not args.no_instagram,
        publish_youtube_enabled=args.youtube,
        youtube_privacy=args.youtube_privacy,
        youtube_publish_at=normalize_publish_at(args.youtube_publish_at),
        hk_youtube_title=read_text_arg(args.hk_youtube_title),
        hk_youtube_description=read_text_arg(args.hk_youtube_description),
        global_youtube_title=read_text_arg(args.global_youtube_title),
        global_youtube_description=read_text_arg(args.global_youtube_description),
        dry_run=not args.yes,
    )
    print_json(result)


def cmd_publish_video(args):
    publish_at = normalize_publish_at(args.youtube_publish_at)
    plan = {
        "video": args.video,
        "title": read_text_arg(args.title) or Path(args.video).stem,
        "description": read_text_arg(args.description) or "",
        "privacy": "private" if publish_at else args.youtube_privacy,
        "publish_at": publish_at or "",
        "tags": args.tag or ["VIP THINK", "auto-publish"],
    }
    if not args.yes:
        print_json({"dry_run": True, "message": "这是预览，没有上传。真正上传需要 --yes。", "plan": plan})
        return
    result = upload_video(
        args.video,
        title=plan["title"],
        description=plan["description"],
        privacy=plan["privacy"],
        tags=plan["tags"],
        category_id=args.category_id,
        publish_at=publish_at,
    )
    print_json({"dry_run": False, "plan": plan, "result": result})


def cmd_youtube_token_info(_args):
    info = token_info()
    print_json(
        {
            "scope": info.get("scope", ""),
            "has_full_youtube_scope": info.get("has_full_youtube_scope", False),
            "expires_in": info.get("expires_in", ""),
            "audience": info.get("aud", ""),
        }
    )


def cmd_youtube_auth_url(args):
    print_json({"url": youtube_auth_url(args.redirect_uri), "required_scope": "https://www.googleapis.com/auth/youtube"})


def cmd_youtube_exchange_code(args):
    result = exchange_auth_code(args.code, args.redirect_uri)
    saved_to = ""
    if args.save and result.get("refresh_token"):
        refresh_path = youtube_paths()["refresh_token"]
        refresh_path.parent.mkdir(parents=True, exist_ok=True)
        refresh_path.write_text(result["refresh_token"].strip() + "\n", encoding="utf-8")
        saved_to = str(refresh_path)
    safe = {key: value for key, value in result.items() if key not in {"access_token", "refresh_token", "id_token"}}
    safe["has_refresh_token"] = bool(result.get("refresh_token"))
    safe["saved_to"] = saved_to
    print_json(safe)


def build_parser():
    parser = argparse.ArgumentParser(
        description="VIP THINK 社媒发布小助手。默认只预览；真正发布必须加 --yes。",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="检查 Cloudinary、Meta、YouTube、FFmpeg 配置")
    status.set_defaults(func=cmd_status)

    recent = sub.add_parser("recent", help="查看最近发布记录")
    recent.add_argument("--limit", type=int, default=10)
    recent.set_defaults(func=cmd_recent)

    publish = sub.add_parser("publish-image", help="发布图片到 FB/INS，可选转视频上传 YouTube")
    publish.add_argument("--region", choices=["hk", "global", "both"], required=True)
    publish.add_argument("--image", required=True, help="本地图片路径或 https 图片链接")
    publish.add_argument("--hk-caption", help="HK 文案。可直接写文本，或用 @/path/caption.txt")
    publish.add_argument("--global-caption", help="Global 文案。可直接写文本，或用 @/path/caption.txt")
    publish.add_argument("--youtube", action="store_true", help="把图片转成视频并上传 YouTube")
    publish.add_argument("--youtube-privacy", choices=["private", "unlisted", "public"], default="private")
    publish.add_argument("--youtube-publish-at", help="YouTube 定时公开时间。可用 UTC，如 2026-07-06T08:45:00Z；也可用本地时间，如 2026-07-06 16:45")
    publish.add_argument("--hk-youtube-title")
    publish.add_argument("--hk-youtube-description")
    publish.add_argument("--global-youtube-title")
    publish.add_argument("--global-youtube-description")
    publish.add_argument("--no-facebook", action="store_true")
    publish.add_argument("--no-instagram", action="store_true")
    publish.add_argument("--yes", action="store_true", help="确认真正发布。没有这个参数时只预览不发布。")
    publish.set_defaults(func=cmd_publish_image)

    video = sub.add_parser("publish-video", help="直接上传本地视频到 YouTube，可设置定时公开")
    video.add_argument("--video", required=True, help="本地 mp4 路径")
    video.add_argument("--title", required=True, help="标题。可直接写文本，或用 @/path/title.txt")
    video.add_argument("--description", default="", help="描述。可直接写文本，或用 @/path/description.txt")
    video.add_argument("--youtube-privacy", choices=["private", "unlisted", "public"], default="private")
    video.add_argument("--youtube-publish-at", help="YouTube 定时公开时间。可用 UTC 或 Asia/Shanghai 本地时间")
    video.add_argument("--tag", action="append", help="YouTube 标签，可重复传入")
    video.add_argument("--category-id", default="27")
    video.add_argument("--yes", action="store_true", help="确认真正上传。没有这个参数时只预览不上传。")
    video.set_defaults(func=cmd_publish_video)

    yt_info = sub.add_parser("youtube-token-info", help="检查当前 YouTube token 权限范围")
    yt_info.set_defaults(func=cmd_youtube_token_info)

    yt_auth = sub.add_parser("youtube-auth-url", help="生成重新授权 YouTube 完整权限的链接")
    yt_auth.add_argument("--redirect-uri", default="https://developers.google.com/oauthplayground")
    yt_auth.set_defaults(func=cmd_youtube_auth_url)

    yt_exchange = sub.add_parser("youtube-exchange-code", help="用 Google 授权码换取 token；结果不会打印 token 明文")
    yt_exchange.add_argument("--code", required=True)
    yt_exchange.add_argument("--redirect-uri", default="https://developers.google.com/oauthplayground")
    yt_exchange.add_argument("--save", action="store_true", help="保存新的 refresh token 到当前配置文件。不会打印 token 明文。")
    yt_exchange.set_defaults(func=cmd_youtube_exchange_code)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
