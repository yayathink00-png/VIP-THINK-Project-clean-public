# 钉钉供应商群对账机器人 MVP

这个版本先解决一件事：把供应商群里明确需要入账的消息，稳定解析成钉钉在线表格的一行。Excel/CSV 不是正式结果，只作为本地排错备份。

## 推荐群内规则

外部供应商群不建议静默抓取全部聊天。稳定做法是：需要入账的消息固定包含 `下单`，并且一次发完整 9 个字段。字段完整才写入钉钉表；缺字段或格式不对，机器人只提醒补发，不写入正式表。

推荐完整格式：

```text
下单 2026/7/6 Yanina 待确认 2026/4/2 混剪 3 周家高混剪 90 270
```

字段顺序固定：

```text
下单 下单时间 下单人 所属部门 交付时间 类型 数量 具体内容 单价 总价
```

更稳的写法是带字段名，内容里即使有空格也不容易错：

```text
下单 下单时间:2026/7/6 下单人:Yanina 所属部门:待确认 交付时间:2026/4/2 类型:混剪 数量:3 具体内容:周家高混剪 单价:90 总价:270
```

会解析成：

| 下单时间 | 下单人 | 所属部门 | 交付时间 | 类型 | 数量 | 具体内容 | 单价 | 总价 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026/4/2 | 郭鑫月 | 投放 | 2026/4/2 | 混剪 | 3 | 周家高混剪 | 90 | 270 |

## 当前文件

- `config/people_departments.csv`：下单人到部门的映射。
- `config/prices.csv`：类型到单价的映射。
- `examples/messages.txt`：本地测试用的群消息。
- `scripts/parse_order_messages.py`：把消息解析成 9 个固定字段。
- `scripts/poll_dingtalk_group_orders.py`：不 @ 机器人时，轮询群消息并写入钉钉在线表格。
- `scripts/run_dingtalk_stream.py`：@ 机器人时，通过 Stream 接收并写入钉钉在线表格。
- `output/`：本地排错输出目录，不作为正式对账表。

## 本地测试

运行位置：

```bash
cd /Users/yangyi/Documents/对账
```

运行命令：

```bash
python3 scripts/parse_order_messages.py examples/messages.txt --output output/orders.csv
```

成功后会看到类似：

```text
parsed=2 skipped=1 output=output/orders.csv
```

打开 `output/orders.csv`，可以看到对账表字段：

```text
下单时间,下单人,所属部门,交付时间,类型,数量,具体内容,单价,总价
```

## 常见失败情况

- 没写 `下单`：脚本会跳过，不入账。
- 没写数量：会入账但标记 `待补充`。
- 没写交付时间：会入账但标记 `待补充`。
- 类型不在 `config/prices.csv`：单价为空，总价为空，需要先补价格表。
- 下单人不在 `config/people_departments.csv`：部门会标记为 `待确认`。

## 下一步接钉钉

接钉钉时需要准备：

1. 群主或管理员允许添加机器人。
2. 机器人页面选择 `Stream模式`。
3. 在 `.env` 填入 `DINGTALK_CLIENT_ID` 和 `DINGTALK_CLIENT_SECRET`。
4. 把机器人加入供应商群。

如果供应商不方便每次 `@内容机器人`，就使用轮询模式；群里直接发完整字段的 `下单 ...` 即可。

## 启动真实接收

运行位置：

```bash
cd /Users/yangyi/Documents/对账
```

启动命令：

```bash
.venv/bin/python scripts/run_dingtalk_stream.py
```

看到下面内容表示 Stream 连接已启动：

```text
DingTalk Stream 已启动。请在群里发送：@内容机器人 下单 混剪 3条 周家高混剪 交付4/2
```

再到供应商群里发：

```text
@内容机器人 下单 2026/7/6 Yanina 待确认 2026/4/2 混剪 3 周家高混剪 90 270
```

成功后会写入钉钉在线表格，并生成或追加本地备份：

- `output/dingtalk_events.jsonl`：钉钉原始消息事件，排错用。
- `output/orders_live.csv`：真实群消息生成的对账表。

如果群成员里没有 `内容机器人`，程序可以连接钉钉，但收不到群消息。需要先在群设置里添加机器人，或用有群管理权限的账号把机器人加入群。

## 不 @ 机器人也抓取

如果不想每条都 `@内容机器人`，使用轮询模式。群里按完整 9 字段直接发：

```text
下单 2026/7/6 Yanina 待确认 2026/4/2 混剪 3 周家高混剪 90 270
```

运行：

```bash
cd /Users/yangyi/Documents/对账
.venv/bin/python scripts/poll_dingtalk_group_orders.py --once
```

持续运行：

```bash
.venv/bin/python scripts/poll_dingtalk_group_orders.py --interval 30
```

如果希望机器人在群里回复“已记录”，加 `--reply`：

```bash
.venv/bin/python scripts/poll_dingtalk_group_orders.py --interval 30 --reply
```

成功后会写入钉钉在线表格，并生成本地排错文件：

- `output/orders_poll.csv`：轮询抓到的对账表。
- `output/dingtalk_poll_events.jsonl`：轮询抓到的原始消息。
- `output/poll_state.json`：已处理消息 ID，防止重复入账。

## 钉钉在线表格

当前正式对账表是钉钉在线表格，不是 Excel 文件：

```text
https://alidocs.dingtalk.com/i/nodes/dpYLaezmVNLNb7NNtP3nOjpx8rMqPxX6
```

表头固定为：

```text
下单时间,下单人,所属部门,交付时间,类型,数量,具体内容,单价,总价
```

`.env` 中的这两个配置控制写入位置：

```text
DINGTALK_SHEET_NODE_ID=dpYLaezmVNLNb7NNtP3nOjpx8rMqPxX6
DINGTALK_SHEET_ID=kgqie6hm
```

## 服务器常驻运行

正式使用建议放到服务器，用 systemd 常驻：

```bash
cd /opt/vipthink/dingtalk-order-bot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

服务器 env 文件建议放在 `/etc/vipthink/dingtalk-order-bot.env`，必须包含：

```text
DINGTALK_ROBOT_NAME=内容机器人
DINGTALK_ROBOT_CODE=dingminyjddewbb48v4x
DINGTALK_GROUP_ID=cidmRksPl9NGN3Wv6Vt46M+Jg==
DINGTALK_POLL_START_TIME=2026-07-06 15:00:00
DINGTALK_SHEET_NODE_ID=dpYLaezmVNLNb7NNtP3nOjpx8rMqPxX6
DINGTALK_SHEET_ID=kgqie6hm
DINGTALK_OUTPUT_DIR=/var/lib/vipthink-dingtalk-order-bot
DWS_PATH=/usr/local/bin/dws
HOME=/root
```

服务模板在：

```text
deploy/systemd/dingtalk-order-poller.service
```

启动后会每 30 秒轮询一次，最多拉取 100 条消息，符合完整 9 字段格式才写入钉钉在线表格。

这个轮询服务不需要 nginx，也不需要占用公网端口；它只主动访问钉钉和钉钉在线表格。不要复用 `ad-assistant-token-keeper` 或 `payment-shortlink` 的端口、目录、env 文件。
