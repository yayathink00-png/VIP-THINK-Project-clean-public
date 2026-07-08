# VIP THINK 发布小助手用法

主入口不是网页，而是在 Codex 里对话。

你可以直接这样说：

- `帮我发 HK：图片 /path/to/image.jpg，文案按默认风格，YouTube 先 private`
- `帮我发 Global：图片 /path/to/image.jpg，普通话文案我贴给你，同时发 FB、INS、YouTube`
- `帮我同时发 HK 和 Global：图片 /path/to/image.jpg，HK 用粤语，Global 用普通话，YouTube 先 private`
- `查看最近 10 条发布记录`
- `先预览这次会发到哪些账号，不要真的发`

为了保证文案质量，推荐你这样说：

```text
帮我发 HK 和 Global。
图片是 /path/to/image.jpg。
主题：小學期末差倍題，尾後加 0。
目标：引导家长留言领取练习 / 免费体验课。
先给我看文案，不要发布。
```

如果你只给图片、不写主题，我会先看图内容，再按 VIP THINK 风格写 HK/Global 两版文案，确认后再发布。

后台实际执行的是：

```bash
cd /Users/yangyi/Documents/自动化发布
python3 tools/social_publish_assistant.py status
```

真正发布图片到 HK 的 FB/INS，并把图片转视频上传 YouTube 私密测试：

```bash
cd /Users/yangyi/Documents/自动化发布
python3 tools/social_publish_assistant.py publish-image \
  --region hk \
  --image "/absolute/path/to/image.jpg" \
  --youtube \
  --youtube-privacy private \
  --yes
```

图片转 YouTube 视频并设置定时公开：

```bash
cd /Users/yangyi/Documents/自动化发布
python3 tools/social_publish_assistant.py publish-image \
  --region hk \
  --image "/absolute/path/to/image.jpg" \
  --youtube \
  --youtube-publish-at "2026-07-07 18:00" \
  --no-facebook \
  --no-instagram \
  --yes
```

直接上传已有 mp4 到 YouTube 并设置定时公开：

```bash
cd /Users/yangyi/Documents/自动化发布
python3 tools/social_publish_assistant.py publish-video \
  --video "/absolute/path/video.mp4" \
  --title "影片標題" \
  --description "@/absolute/path/youtube-description.txt" \
  --youtube-publish-at "2026-07-07 18:00" \
  --tag "VIP THINK" \
  --tag "數學思維" \
  --yes
```

同时发布 HK 和 Global：

```bash
cd /Users/yangyi/Documents/自动化发布
python3 tools/social_publish_assistant.py publish-image \
  --region both \
  --image "/absolute/path/to/image.jpg" \
  --youtube \
  --youtube-privacy private \
  --yes
```

没有 `--yes` 时只会预览，不会真的发布。

当前账号映射：

- HK：Facebook `VIP THINK - HK`，Instagram `vipthink.hk`
- Global：Facebook `VIP THINK - Global`，Instagram `vipthink.global`
- YouTube：目前只有一个 OAuth 上传通道；当前通道已验证对应 `VIP THINK-HK`。要区分 `YouTube-hk` 和 `YouTube-global`，需要再授权第二个 YouTube Channel。

YouTube 权限检查：

```bash
cd /Users/yangyi/Documents/自动化发布
python3 tools/social_publish_assistant.py youtube-token-info
```

如果 `has_full_youtube_scope` 是 `false`，说明当前 token 只能上传，不能查询、修改或删除视频。重新授权完整权限时先生成授权链接：

```bash
cd /Users/yangyi/Documents/自动化发布
python3 tools/social_publish_assistant.py youtube-auth-url
```

拿到 Google 授权码后保存新 refresh token：

```bash
cd /Users/yangyi/Documents/自动化发布
python3 tools/social_publish_assistant.py youtube-exchange-code --code "PASTE_CODE_HERE" --save
```
