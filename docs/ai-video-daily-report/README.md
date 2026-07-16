# AI 视频日报自动播报

这个模块用于每天从钉钉在线表格读取 AI 视频制作台账，自动整理一版日报，先发给审核人确认；审核人回复 `OK` 后，再由机器人发到正式群。

## 流程

1. 同事按固定表头填写当天或上一个工作日的台账。
2. 定时任务在工作日 10:30 读取需要播报的日期；周一读取上周五，其他工作日读取前一天。
3. 脚本生成简洁日报，并发送到审核群或审核人。
4. 审核人回复 `OK` 后，脚本把日报发送到正式群，并把表格中的播报状态更新为已播报。
5. 审核人回复 `修改：...` 时，只记录修改意见，不自动发送正式群。
6. 审核人回复 `不发` 时，跳过本次正式播报。

## 关键文件

- `scripts/ai_video_daily_report_bot.py`：读取表格、生成日报、发送审批消息和正式群消息。
- `config/ai_video_daily_report.example.json`：公开版配置样例，真实配置不要提交到仓库。
- `deploy/systemd/ai-video-daily-report-request.*`：Linux 服务器 10:30 发起审批的 systemd 模板。
- `deploy/systemd/ai-video-daily-report-check.*`：Linux 服务器每 5 分钟检查审批回复的 systemd 模板。
- `launchd/com.vipthink.ai-video-daily-report*.plist.template`：macOS 本地定时任务模板。
- `docs/ai-video-daily-report/table-template.md`：钉钉表格字段和填写规则。
- `docs/ai-video-daily-report/colleague-codex-prompt.md`：发给同事 Codex 的自动填写提示词。

## 配置原则

真实配置文件应命名为：

```text
config/ai_video_daily_report.json
```

这个文件必须只放在运行环境里，不提交到公开仓库。需要配置的字段包括钉钉表格 node、sheet id、审批群、正式播报群、机器人 robotCode、审核人 userId 等。

## 本地试跑

```bash
python3 scripts/ai_video_daily_report_bot.py --previous-report-day --dry-run
```

能成功读取表格并生成日报文本，说明表头和配置基本正常。
