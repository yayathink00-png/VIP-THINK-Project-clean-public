#!/usr/bin/env python3
import cgi
import html
import json
import mimetypes
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.cloudinary_upload_server import (
    cloudinary_config,
    missing_config,
    save_config as save_cloudinary_config,
    upload_to_cloudinary,
)
from tools.meta_publish_server import (
    accounts,
    publish_facebook,
    publish_instagram,
    token as meta_token,
    upsert_env,
)
from tools.image_to_youtube_video import (
    download_image,
    ffmpeg_available,
    make_video_from_image,
    save_uploaded_image,
)
from tools.publish_records import log_publish_record, recent_publish_records
from tools.youtube_publish import upload_video, youtube_available


PORT = int(os.environ.get("SOCIAL_PUBLISHER_PORT", "4060"))
DEFAULT_IMAGE_URL = "https://res.cloudinary.com/jckpq8dp/image/upload/v1783305952/social-auto-publish/1-1-1783305950.jpg"
DEFAULT_HK_CAPTION = """【🔥小學期末數學最易失分？差倍題一定要刷熟🔥】

尾後加 0、倍數關係、相差幾多，好多小朋友一見到就亂。
其實只要掌握固定解題步驟，題型就會清晰好多。

✅ 看懂題目關係
✅ 掌握差倍解題步驟
✅ 減少期末考試失分
✅ 訓練數學思維

想拎更多同類題型練習，留言「差倍」📩

🔗 免費體驗連結：
https://vip-think.com/maliang/popularize-60839.html
官網：https://vipthink.hk/
YT：@VIP THINK - HK
IG：@vipthink.hk
FB：@VIP THINK - HK

#親子數學 #小學數學 #期末溫習 #差倍問題 #數學思維 #VIPTHINK"""
DEFAULT_GLOBAL_CAPTION = """【🔥小学期末数学最容易丢分？差倍题一定要刷熟🔥】

尾后加 0、倍数关系、相差多少，很多孩子一看到就容易乱。
其实只要掌握固定解题步骤，题型就会清晰很多。

✅ 看懂题目关系
✅ 掌握差倍解题步骤
✅ 减少期末考试失分
✅ 训练数学思维

想要更多同类题型练习，留言「差倍」📩

🔗 免费体验链接：
https://vip-think.com/maliang/popularize-60839.html
官网｜https://global.vip-think.com/
IG｜@vipthink.global
YT｜@VIP THINK - Global
FB｜@VIP THINK - Global

#亲子数学 #小学数学 #期末复习 #差倍问题 #数学思维 #VIPTHINK"""
DEFAULT_HK_YOUTUBE_TITLE = "小學數學差倍題必刷｜期末衝刺解題技巧"
DEFAULT_HK_YOUTUBE_DESCRIPTION = """這條影片示範小學常見差倍問題，幫助孩子看清題目關係，掌握解題步驟，減少期末考試失分。

適合小三至小六學生期末前溫習，也適合家長陪孩子一起做暑假數學練習。

免費體驗連結：
https://vip-think.com/maliang/popularize-60839.html

#小學數學 #差倍問題 #期末溫習 #數學思維 #VIPTHINK"""
DEFAULT_GLOBAL_YOUTUBE_TITLE = "小学数学差倍题必刷｜期末冲刺解题技巧"
DEFAULT_GLOBAL_YOUTUBE_DESCRIPTION = """这条视频示范小学常见差倍问题，帮助孩子看清题目关系，掌握解题步骤，减少期末考试失分。

适合小三至小六学生期末前复习，也适合家长陪孩子一起做暑假数学练习。

免费体验链接：
https://vip-think.com/maliang/popularize-60839.html

#小学数学 #差倍问题 #期末复习 #数学思维 #VIPTHINK"""
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


def page(title, body):
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f8fafc; color: #0f172a; }}
    header {{ background: #0f172a; color: white; padding: 18px 28px; }}
    main {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}
    section {{ background: white; border: 1px solid #e2e8f0; padding: 20px; margin-bottom: 18px; border-radius: 8px; }}
    h1 {{ margin: 0; font-size: 24px; }}
    h2 {{ margin-top: 0; font-size: 18px; }}
    input, textarea, select {{ width: 100%; box-sizing: border-box; padding: 9px; margin: 6px 0 14px; border: 1px solid #cbd5e1; border-radius: 6px; }}
    textarea {{ min-height: 110px; }}
    button {{ padding: 10px 16px; border: 0; border-radius: 6px; background: #2563eb; color: white; cursor: pointer; }}
    a.button {{ display: inline-block; padding: 10px 16px; border-radius: 6px; background: #e2e8f0; color: #0f172a; text-decoration: none; }}
    pre {{ background: #f1f5f9; padding: 14px; white-space: pre-wrap; overflow-wrap: anywhere; border-radius: 6px; }}
    .ok {{ color: #065f46; background: #ecfdf5; padding: 10px; border-radius: 6px; }}
    .warn {{ color: #92400e; background: #fffbeb; padding: 10px; border-radius: 6px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; }}
    img.preview {{ max-width: 320px; max-height: 320px; border: 1px solid #e2e8f0; display: block; margin-top: 12px; }}
    .inline {{ display: inline-flex; align-items: center; gap: 8px; margin: 6px 0 14px; }}
    .inline input {{ width: auto; margin: 0; }}
  </style>
</head>
<body>
<header><h1>社媒自动发布</h1></header>
<main>{body}</main>
</body>
</html>"""


def parse_form(handler):
    return cgi.FieldStorage(
        fp=handler.rfile,
        headers=handler.headers,
        environ={
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": handler.headers.get("Content-Type"),
        },
    )


def account_sections():
    current_token = meta_token()
    if not current_token:
        return [], [], '<div class="warn">Meta token 未配置。请先配置 token。</div>'
    data = accounts()
    if "error" in data:
        return [], [], f'<div class="warn">读取 Meta 账号失败。</div><pre>{html.escape(json.dumps(data, ensure_ascii=False, indent=2))}</pre>'

    page_options = []
    ig_options = []
    lines = []
    for item in data.get("data", []):
        page_id = item.get("id", "")
        page_name = item.get("name", page_id)
        page_options.append(f'<option value="{html.escape(page_id)}">{html.escape(page_name)} ({html.escape(page_id)})</option>')
        lines.append(f"Facebook Page: {page_name} ({page_id})")
        ig = item.get("instagram_business_account")
        if ig:
            ig_id = ig.get("id", "")
            ig_name = ig.get("username") or ig.get("name") or ig_id
            ig_options.append(f'<option value="{html.escape(ig_id)}">{html.escape(ig_name)} ({html.escape(ig_id)})</option>')
            lines.append(f"  Instagram: {ig_name} ({ig_id})")
        else:
            lines.append("  Instagram: none")
    body = f'<pre>{html.escape(chr(10).join(lines) or "none")}</pre>'
    return page_options, ig_options, body


def selected_values(form, name):
    value = form[name] if name in form else []
    if isinstance(value, list):
        return [(item.value or "").strip() for item in value if (item.value or "").strip()]
    if getattr(value, "value", ""):
        return [value.value.strip()]
    return []


def selected_labels(options_html, selected_ids):
    # The current app only needs IDs for publishing; labels are rendered by Meta results.
    return selected_ids


def links_from_results(results):
    links = []
    image_url = results.get("image_url")
    if image_url:
        links.append({"label": "Cloudinary 图片链接", "url": image_url})
    for item_result in results.get("facebook", []):
        result = item_result.get("result", {})
        if result.get("photo_url"):
            links.append({"label": "Facebook 图片链接", "url": result["photo_url"]})
        if result.get("possible_post_url"):
            links.append({"label": "Facebook 帖子链接", "url": result["possible_post_url"]})
    for item_result in results.get("instagram", []):
        result = item_result.get("result", {})
        if result.get("permalink"):
            links.append({"label": "Instagram 链接", "url": result["permalink"]})
    youtube = results.get("youtube") or {}
    if youtube.get("result", {}).get("watch_url"):
        links.append({"label": "YouTube 链接", "url": youtube["result"]["watch_url"]})
    return links


def render_link_list(links):
    return "".join(
        f'<p><a href="{html.escape(item["url"])}" target="_blank">{html.escape(item["label"])}</a></p>'
        for item in links
    )


def render_recent_records(limit=8):
    records = recent_publish_records(limit)
    if not records:
        return '<div class="warn">还没有发布记录。</div>'
    items = []
    for record in records:
        record_links = record.get("links", [])
        link_html = " ".join(
            f'<a href="{html.escape(item.get("url", ""))}" target="_blank">{html.escape(item.get("label", "link"))}</a>'
            for item in record_links
            if item.get("url")
        )
        items.append(
            "<li>"
            f"<strong>{html.escape(record.get('created_at', ''))}</strong> "
            f"{html.escape(record.get('preset', 'custom'))} "
            f"{html.escape(record.get('caption', '')[:60])}"
            f"<br />{link_html}"
            "</li>"
        )
    return "<ul>" + "".join(items) + "</ul>"


def region_for_page_id(page_id):
    if page_id in ACCOUNT_PRESETS["hk"]["page_ids"]:
        return "hk"
    if page_id in ACCOUNT_PRESETS["global"]["page_ids"]:
        return "global"
    return "hk"


def region_for_ig_user_id(ig_user_id):
    if ig_user_id in ACCOUNT_PRESETS["hk"]["ig_user_ids"]:
        return "hk"
    if ig_user_id in ACCOUNT_PRESETS["global"]["ig_user_ids"]:
        return "global"
    return "hk"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def send_html(self, title, body, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page(title, body).encode("utf-8"))

    def do_GET(self):
        if self.path.startswith("/setup/cloudinary"):
            config = cloudinary_config()
            body = f"""
<section>
  <h2>Cloudinary 配置</h2>
  <form method="post" action="/setup/cloudinary">
    <label>Cloud name</label>
    <input name="cloud_name" value="{html.escape(config['cloud_name'])}" required />
    <label>API key</label>
    <input name="api_key" value="{html.escape(config['api_key'])}" required />
    <label>API secret</label>
    <input name="api_secret" type="password" required />
    <label>Folder</label>
    <input name="folder" value="{html.escape(config['folder'])}" />
    <button type="submit">保存</button>
    <a class="button" href="/">返回</a>
  </form>
</section>
"""
            self.send_html("Cloudinary 配置", body)
            return

        if self.path.startswith("/setup/meta"):
            body = """
<section>
  <h2>Meta Token 配置</h2>
  <form method="post" action="/setup/meta">
    <label>Facebook/Instagram System User token</label>
    <textarea name="token" required></textarea>
    <button type="submit">保存</button>
    <a class="button" href="/">返回</a>
  </form>
</section>
"""
            self.send_html("Meta Token 配置", body)
            return

        page_options, ig_options, account_body = account_sections()
        cloudinary_missing = missing_config(cloudinary_config())
        cloudinary_status = (
            '<div class="ok">Cloudinary 已配置。</div>'
            if not cloudinary_missing
            else f'<div class="warn">Cloudinary 缺配置：{html.escape(", ".join(cloudinary_missing))}</div>'
        )
        meta_status = (
            '<div class="ok">Meta token 已配置。</div>'
            if meta_token()
            else '<div class="warn">Meta token 未配置。</div>'
        )
        youtube_status = (
            '<div class="ok">YouTube OAuth 已配置。</div>'
            if youtube_available()
            else '<div class="warn">YouTube OAuth 未配置。</div>'
        )
        ffmpeg_status = (
            '<div class="ok">FFmpeg 可用。</div>'
            if ffmpeg_available()
            else '<div class="warn">FFmpeg 不可用，图片转视频会失败。</div>'
        )
        image_url = DEFAULT_IMAGE_URL
        recent_body = render_recent_records()
        body = f"""
<div class="grid">
  <section>
    <h2>状态</h2>
    {cloudinary_status}
    <p><a class="button" href="/setup/cloudinary">配置 Cloudinary</a></p>
    {meta_status}
    <p><a class="button" href="/setup/meta">配置 Meta token</a></p>
    {youtube_status}
    {ffmpeg_status}
  </section>
  <section>
    <h2>已识别账号</h2>
    {account_body}
  </section>
</div>
<section>
  <h2>一键发布</h2>
  <form method="post" action="/quick-publish" enctype="multipart/form-data">
    <label>快捷账号组</label>
    <select name="preset">
      <option value="custom">手动选择</option>
      <option value="hk">HK：fb-hk + ins-hk</option>
      <option value="global">Global：fb-global + ins-global</option>
      <option value="both">HK + Global：四个账号一起发</option>
    </select>
    <label>本地图片</label>
    <input type="file" name="file" accept="image/png,image/jpeg,image/webp" />
    <label>或者直接使用图片 URL</label>
    <input name="image_url" value="{html.escape(image_url)}" />
    <label>发布到 Facebook Page（可多选）</label>
    <select name="page_ids" multiple size="4">{''.join(page_options)}</select>
    <label>发布到 Instagram（可多选）</label>
    <select name="ig_user_ids" multiple size="4">{''.join(ig_options)}</select>
    <label class="inline"><input type="checkbox" name="publish_youtube" value="1" /> 同时把图片转成视频并上传 YouTube</label>
    <label>HK YouTube 标题（粤语/繁体）</label>
    <input name="hk_youtube_title" value="{html.escape(DEFAULT_HK_YOUTUBE_TITLE)}" />
    <label>HK YouTube 描述（粤语/繁体）</label>
    <textarea name="hk_youtube_description">{html.escape(DEFAULT_HK_YOUTUBE_DESCRIPTION)}</textarea>
    <label>Global YouTube 标题（普通话/简体）</label>
    <input name="global_youtube_title" value="{html.escape(DEFAULT_GLOBAL_YOUTUBE_TITLE)}" />
    <label>Global YouTube 描述（普通话/简体）</label>
    <textarea name="global_youtube_description">{html.escape(DEFAULT_GLOBAL_YOUTUBE_DESCRIPTION)}</textarea>
    <label>YouTube 可见性</label>
    <select name="youtube_privacy">
      <option value="private">private 私密测试</option>
      <option value="unlisted">unlisted 不公开链接</option>
      <option value="public">public 公开</option>
    </select>
    <label>HK FB / INS 文案（粤语/繁体）</label>
    <textarea name="hk_caption">{html.escape(DEFAULT_HK_CAPTION)}</textarea>
    <label>Global FB / INS 文案（普通话/简体）</label>
    <textarea name="global_caption">{html.escape(DEFAULT_GLOBAL_CAPTION)}</textarea>
    <button type="submit">上传并发布</button>
  </form>
</section>
<section>
  <h2>最近发布记录</h2>
  {recent_body}
</section>
<section>
  <h2>单独上传图片</h2>
  <form method="post" action="/upload" enctype="multipart/form-data">
    <input type="file" name="file" accept="image/png,image/jpeg,image/webp" required />
    <button type="submit">上传到 Cloudinary</button>
  </form>
</section>
<section>
  <h2>使用已有图片链接发布</h2>
  <form method="post" action="/publish">
    <label>平台</label>
    <select name="platform">
      <option value="facebook">Facebook Page</option>
      <option value="instagram">Instagram</option>
    </select>
    <label>Facebook Page</label>
    <select name="page_id">{''.join(page_options)}</select>
    <label>Instagram 账号</label>
    <select name="ig_user_id">{''.join(ig_options)}</select>
    <label>图片 URL</label>
    <input name="image_url" value="{html.escape(image_url)}" required />
    <label>文案</label>
    <textarea name="caption">{html.escape(DEFAULT_HK_CAPTION)}</textarea>
    <button type="submit">发布</button>
  </form>
</section>
"""
        self.send_html("社媒自动发布", body)

    def do_POST(self):
        form = parse_form(self)
        if self.path.startswith("/setup/cloudinary"):
            try:
                save_cloudinary_config(form)
            except Exception as exc:
                self.send_html("配置失败", f"<section><h2>配置失败</h2><pre>{html.escape(str(exc))}</pre></section>", status=400)
                return
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
            return

        if self.path.startswith("/setup/meta"):
            new_token = (form.getfirst("token") or "").strip()
            if not new_token:
                self.send_html("配置失败", "<section><h2>token 不能为空</h2></section>", status=400)
                return
            upsert_env({"META_ACCESS_TOKEN": new_token})
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
            return

        if self.path.startswith("/upload"):
            item = form["file"] if "file" in form else None
            if item is None or not getattr(item, "filename", ""):
                self.send_html("上传失败", "<section><h2>没有选择文件</h2></section>", status=400)
                return
            data = item.file.read()
            content_type = item.type or mimetypes.guess_type(item.filename)[0] or "application/octet-stream"
            try:
                result = upload_to_cloudinary(item.filename, content_type, data)
            except Exception as exc:
                self.send_html("上传失败", f"<section><h2>上传失败</h2><pre>{html.escape(str(exc))}</pre></section>", status=500)
                return
            url = result.get("secure_url", "")
            page_options, ig_options, account_body = account_sections()
            body = f"""
<section>
  <h2>上传成功</h2>
  <pre>{html.escape(url)}</pre>
  <img class="preview" src="{html.escape(url)}" alt="uploaded image" />
</section>
<section>
  <h2>直接发布这张图</h2>
  <form method="post" action="/publish">
    <label>平台</label>
    <select name="platform">
      <option value="facebook">Facebook Page</option>
      <option value="instagram">Instagram</option>
    </select>
    <label>Facebook Page</label>
    <select name="page_id">{''.join(page_options)}</select>
    <label>Instagram 账号</label>
    <select name="ig_user_id">{''.join(ig_options)}</select>
    <label>图片 URL</label>
    <input name="image_url" value="{html.escape(url)}" required />
    <label>文案</label>
    <textarea name="caption"></textarea>
    <button type="submit">发布</button>
    <a class="button" href="/">返回首页</a>
  </form>
</section>
"""
            self.send_html("上传成功", body)
            return

        if self.path.startswith("/quick-publish"):
            image_url = (form.getfirst("image_url") or "").strip()
            item = form["file"] if "file" in form else None
            upload_result = None
            source_image_path = None
            if item is not None and getattr(item, "filename", ""):
                data = item.file.read()
                source_image_path = save_uploaded_image(item.filename, data)
                content_type = item.type or mimetypes.guess_type(item.filename)[0] or "application/octet-stream"
                try:
                    upload_result = upload_to_cloudinary(item.filename, content_type, data)
                except Exception as exc:
                    self.send_html("发布失败", f"<section><h2>图片上传失败</h2><pre>{html.escape(str(exc))}</pre></section>", status=500)
                    return
                image_url = upload_result.get("secure_url", "")
            if not image_url:
                self.send_html("发布失败", "<section><h2>请上传图片，或填写图片 URL</h2></section>", status=400)
                return
            if source_image_path is None:
                try:
                    source_image_path = download_image(image_url)
                except Exception:
                    source_image_path = None

            hk_caption = (form.getfirst("hk_caption") or DEFAULT_HK_CAPTION).strip()
            global_caption = (form.getfirst("global_caption") or DEFAULT_GLOBAL_CAPTION).strip()
            captions = {"hk": hk_caption, "global": global_caption}
            page_ids = selected_values(form, "page_ids")
            ig_user_ids = selected_values(form, "ig_user_ids")
            preset = (form.getfirst("preset") or "custom").strip()
            if preset in ACCOUNT_PRESETS:
                page_ids = ACCOUNT_PRESETS[preset]["page_ids"]
                ig_user_ids = ACCOUNT_PRESETS[preset]["ig_user_ids"]
            publish_youtube = (form.getfirst("publish_youtube") or "").strip() == "1"
            if not page_ids and not ig_user_ids and not publish_youtube:
                self.send_html("发布失败", "<section><h2>请至少选择一个 Facebook Page、Instagram 账号或 YouTube 上传</h2></section>", status=400)
                return

            results = {
                "image_url": image_url,
                "facebook": [],
                "instagram": [],
                "youtube": None,
            }
            for page_id in page_ids:
                region = region_for_page_id(page_id)
                results["facebook"].append({
                    "page_id": page_id,
                    "region": region,
                    "caption_used": captions[region],
                    "result": publish_facebook(page_id, image_url, captions[region]),
                })
            for ig_user_id in ig_user_ids:
                region = region_for_ig_user_id(ig_user_id)
                results["instagram"].append({
                    "ig_user_id": ig_user_id,
                    "region": region,
                    "caption_used": captions[region],
                    "result": publish_instagram(ig_user_id, image_url, captions[region]),
                })
            if publish_youtube:
                youtube_region = "global" if preset == "global" else "hk"
                youtube_title = (
                    form.getfirst(f"{youtube_region}_youtube_title")
                    or form.getfirst("hk_youtube_title")
                    or "YouTube upload"
                ).strip()
                youtube_description = (
                    form.getfirst(f"{youtube_region}_youtube_description")
                    or form.getfirst("hk_youtube_description")
                    or captions[youtube_region]
                    or ""
                ).strip()
                youtube_privacy = (form.getfirst("youtube_privacy") or "private").strip()
                try:
                    if source_image_path is None:
                        raise RuntimeError("Could not prepare source image for video conversion")
                    video_path = make_video_from_image(
                        source_image_path,
                        size="720x1280",
                        duration=7.5,
                        title_prefix="youtube-image-video",
                    )
                    youtube_result = upload_video(
                        video_path,
                        title=youtube_title,
                        description=youtube_description,
                        privacy=youtube_privacy,
                    )
                    results["youtube"] = {
                        "region": youtube_region,
                        "source_image": str(source_image_path),
                        "video_path": str(video_path),
                        "result": youtube_result,
                    }
                except Exception as exc:
                    results["youtube"] = {"error": str(exc)}

            links = links_from_results(results)
            log_publish_record(
                {
                    "preset": preset,
                    "caption": hk_caption if preset != "global" else global_caption,
                    "hk_caption": hk_caption,
                    "global_caption": global_caption,
                    "page_ids": page_ids,
                    "ig_user_ids": ig_user_ids,
                    "publish_youtube": publish_youtube,
                    "youtube_privacy": (form.getfirst("youtube_privacy") or "").strip(),
                    "links": links,
                    "results": results,
                }
            )

            body = f"""
<section>
  <h2>一键发布结果</h2>
  {render_link_list(links)}
  <pre>{html.escape(json.dumps(results, ensure_ascii=False, indent=2))}</pre>
  <p><a class="button" href="/">返回首页</a></p>
</section>
"""
            self.send_html("一键发布结果", body)
            return

        if self.path.startswith("/publish"):
            platform = (form.getfirst("platform") or "").strip()
            image_url = (form.getfirst("image_url") or "").strip()
            caption = (form.getfirst("caption") or "").strip()
            if platform == "facebook":
                result = publish_facebook((form.getfirst("page_id") or "").strip(), image_url, caption)
            elif platform == "instagram":
                result = publish_instagram((form.getfirst("ig_user_id") or "").strip(), image_url, caption)
            else:
                result = {"error": {"message": "Unknown platform"}}
            links = []
            if result.get("photo_url"):
                links.append(f'<p><a href="{html.escape(result["photo_url"])}" target="_blank">Facebook 图片链接</a></p>')
            if result.get("possible_post_url"):
                links.append(f'<p><a href="{html.escape(result["possible_post_url"])}" target="_blank">Facebook 帖子链接</a></p>')
            publish = result.get("publish") or {}
            if publish.get("id"):
                media = json.dumps(result, ensure_ascii=False, indent=2)
            else:
                media = json.dumps(result, ensure_ascii=False, indent=2)
            body = f"""
<section>
  <h2>发布结果</h2>
  {''.join(links)}
  <pre>{html.escape(media)}</pre>
  <p><a class="button" href="/">返回首页</a></p>
</section>
"""
            self.send_html("发布结果", body)
            return

        self.send_html("Not Found", "<section><h2>Not Found</h2></section>", status=404)


if __name__ == "__main__":
    print(f"Social publisher: http://localhost:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
