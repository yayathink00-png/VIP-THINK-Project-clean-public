# AI 视频日报自动播报 SOP

## 每日机制

- 定时：工作日 10:30。
- 日期：周一读取上周五；其他工作日读取前一天。
- 发送：先发审核，不直接进正式群。
- 审核：审核人回复 `OK` 后才发正式群。

## 审核回复

| 回复 | 系统动作 |
| --- | --- |
| `OK` | 确认通过，发送到正式群，并回写表格播报状态。 |
| `修改：...` | 记录修改意见，不发送正式群。 |
| `不发` | 标记本次不发送。 |

## Linux 部署

1. 把项目放到服务器，例如 `/opt/vipthink/ai-video-daily-report`。
2. 复制 `config/ai_video_daily_report.example.json` 为 `config/ai_video_daily_report.json`，填入真实钉钉配置。
3. 确认服务器能运行 `dws`，必要时在 service 里配置 `DWS_BIN`。
4. 安装 systemd 服务：

```bash
sudo cp deploy/systemd/ai-video-daily-report-*.service /etc/systemd/system/
sudo cp deploy/systemd/ai-video-daily-report-*.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ai-video-daily-report-request.timer
sudo systemctl enable --now ai-video-daily-report-check.timer
```

## 手动试跑

生成预览，不发送：

```bash
python3 scripts/ai_video_daily_report_bot.py --previous-report-day --dry-run
```

发起审核：

```bash
python3 scripts/ai_video_daily_report_bot.py --previous-report-day --request-approval
```

检查审核回复：

```bash
python3 scripts/ai_video_daily_report_bot.py --check-approval
```

## 安全要求

- 不提交真实 `config/ai_video_daily_report.json`。
- 不提交 `state/`、`logs/`、导出的 CSV、截图、视频素材。
- 不把真实群号、openConversationId、userId、robotCode 写进公开文档。
