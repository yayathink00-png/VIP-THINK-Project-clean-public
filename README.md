# 钉钉供应商群对账机器人 MVP

这个项目把供应商钉钉群里明确需要入账的消息，自动解析成钉钉在线表格的一行。Excel/CSV 只作为本地排错备份，正式结果写入钉钉表。

## 群内发送格式

推荐完整格式：

```text
下单 2026/7/6 Yanina 待确认 2026/4/2 混剪 3 周家高混剪 90 270
```

字段顺序固定：

```text
下单 下单时间 下单人 所属部门 交付时间 类型 数量 具体内容 单价 总价
```

也支持带字段名的写法：

```text
下单 下单时间:2026/7/6 下单人:Yanina 所属部门:待确认 交付时间:2026/4/2 类型:混剪 数量:3 具体内容:周家高混剪 单价:90 总价:270
```

写入字段：

```text
下单时间,下单人,所属部门,交付时间,类型,数量,具体内容,单价,总价
```

## 主要文件

- `scripts/parse_order_messages.py`：解析群消息为 9 个固定字段。
- `scripts/poll_dingtalk_group_orders.py`：轮询指定钉钉群消息，写入钉钉在线表格，并可发确认消息。
- `scripts/dingtalk_sheet_writer.py`：追加写入钉钉表，并把新增行设置为居中。
- `scripts/run_dingtalk_stream.py`：Stream 模式接收 @ 机器人消息。
- `config/people_departments.csv`：下单人到部门的映射。
- `config/prices.csv`：类型到单价的映射。
- `examples/messages.txt`：本地测试消息。
- `deploy/systemd/dingtalk-order-poller.service`：服务器常驻轮询服务模板。

## AI 视频日报自动播报

新增的 AI 视频日报链路位于仓库根目录下的通用目录中：

- `scripts/ai_video_daily_report_bot.py`：读取钉钉台账、生成日报、发起人工确认、确认后发正式群。
- `config/ai_video_daily_report.example.json`：公开配置样例；真实配置文件不要提交。
- `docs/ai-video-daily-report/`：台账模板、同事 Codex 提示词、部署和操作 SOP。
- `deploy/systemd/ai-video-daily-report-*.service`：Linux 服务器定时任务模板。
- `launchd/com.vipthink.ai-video-daily-report*.plist.template`：macOS launchd 定时任务模板。

## 本地测试

```bash
python3 scripts/parse_order_messages.py examples/messages.txt --output output/orders.csv
```

成功后会生成：

```text
output/orders.csv
```

## 轮询模式

群里不需要 @ 机器人，直接发送完整 9 字段：

```text
下单 2026/7/6 Yanina 待确认 2026/4/2 混剪 3 周家高混剪 90 270
```

单次轮询：

```bash
.venv/bin/python scripts/poll_dingtalk_group_orders.py --once
```

持续轮询：

```bash
.venv/bin/python scripts/poll_dingtalk_group_orders.py --interval 30 --reply
```

## 钉钉在线表格

正式对账表是钉钉在线表格：

```text
https://alidocs.dingtalk.com/i/nodes/dpYLaezmVNLNb7NNtP3nOjpx8rMqPxX6
```

`.env` 中这两个配置控制写入位置：

```text
DINGTALK_SHEET_NODE_ID=
DINGTALK_SHEET_ID=
```

## 服务器运行

服务器 env 文件建议放在：

```text
/etc/vipthink/dingtalk-order-bot.env
```

服务模板：

```text
deploy/systemd/dingtalk-order-poller.service
```

服务每 30 秒轮询一次，最多拉取 100 条消息。只有符合完整 9 字段格式的消息才会写入钉钉在线表格。

## 安全说明

- `.env` 不提交。
- 真实 DingTalk client secret、机器人 secret、webhook、token 不进入仓库。
- `output/`、日志、缓存、本地运行状态不提交。
