# SOP：AI 视频安全生产流 V0.3

## 0. Dreamina Dialogue Gate

新片启动时，不要要求用户先提供 Dreamina 对话名。新对话刚创建时通常没有名称。

正确顺序：

1. 打开 Dreamina，创建这个视频项目的新对话。
2. 放入一条安全占位/启动内容，让新对话出现在历史记录里。
3. 把新对话重命名成项目专属名称。
4. 确认重命名后的对话被选中。
5. 再把这个对话名和 session id/url 绑定到本地 Name Gate。

推荐命名：

```text
yy_<核心题材>_<口音>_<文字体系>_<画幅>_<年月>
```

示例：

```text
yy_三位数计算_台湾腔_繁体_720x1280_202605
```

## 1. New Run Gate

输入：

- 源视频
- 成片名
- 已重命名的 Dreamina 对话名
- Dreamina session id/url
- 用户硬要求

必须写入：

- `gate_status.json`
- `creative_requirements.json`
- `segments.json`
- Name Gate 绑定信息

## 2. Requirement Gate

生成脚本前必须确认：

| 项目 | 示例 |
|---|---|
| 表现形式 | 真人 |
| 口音 | 台湾腔 |
| 文字体系 | 繁体 |
| 画幅 | 竖版 720x1280 |
| 生成方式 | 文生视频 / 图生视频 / 混合 |
| 源视频用途 | 仅分析 / 作为参考 / 直接视频参考 |
| 字幕/Logo/CTA | 模型生成或后期添加 |
| 人物连续性 | 是否需要同一个老师/主角连续 |

如果用户中途修改要求，必须把相关段落提示词标记为需修改，不允许继续沿用旧 prompt。

## 3. Source Breakdown Gate

拆解源视频：

- 分段时间
- 剧情功能
- 台词
- 人物关系
- 场景和道具
- 景别和运镜
- 结尾状态
- 可复用结构
- 需规避的版权/平台风险

源视频只用于分析时，不上传为生成参考。

## 4. Full Prompt Review Gate

给用户看全片方案：

- 总段数
- 每段目标
- 每段台词
- 每段生成模式
- 参考图策略
- 预计积分
- 风险点

用户确认整体方向后，才进入单段 prompt。

## 5. Segment Prompt Gate

每段提交前都给用户看：

```text
段落：Segment XX
模式：text2video / image2video
参考素材：无 / 某张参考图
时长：10s
比例：9:16
模型：seedance2.0fast_vip
口音：台湾腔
旁白/对白：完整台词
确认语：确认生成 Segment XX
```

提示词写法：

- 默认短提示词。
- 第一优先级写最重要目标。
- 不堆长串“不要/禁止/不准”。
- 口音按用户原话写，例如“台湾腔”。
- CTA 词尽量只放在台词里，不在画面描述里反复出现。
- 人物连续段要写清参考图锚点。

## 6. Continuity Gate

每段人工通过后：

1. 提取尾帧。
2. 如有固定老师/主角，截取清晰人物参考图。
3. 裁掉 AI 标识、水印和边角干扰。
4. 后续同人物段默认优先 image2video。

模式选择：

| 场景 | 推荐模式 |
|---|---|
| 新开场，人物不必连续 | text2video |
| 同一个老师/主角继续出现 | image2video |
| 承接上一段结尾 | image2video + 尾帧 |
| 精准 CTA 台词 | 不加音频参考 |

## 7. Cost Gate

每次扣点前，显示：

| 项目 | 内容 |
|---|---|
| 已采用积分 | 当前累计 |
| 试错积分 | 当前累计 |
| 本次预计积分 | 通常 110 |
| 是否重跑 | 是/否 |
| 失败原因 | 如适用 |

记录时分开统计：

- 最终采用积分
- 试错积分
- 本地失败不计积分

## 8. Submit Gate

提交前自动/人工确认：

- 用户已回复明确确认语。
- Prompt 已审核。
- Name Gate 正确。
- Dreamina 对话正确。
- 模型、比例、时长正确。
- 参考素材存在。
- 素材路径已转绝对路径。
- 风险审计没有 blocking。

提交后记录：

- submit_id
- credit_count
- 模式
- 参考素材
- prompt
- 提交时间
- 本地报告

提交后只查询该 submit_id，不自动重提。

## 9. Query Gate

| 返回状态 | 动作 |
|---|---|
| querying / Generating | 继续等待同一个 submit_id |
| pre-TNS fail | 记录失败，回到提示词修正 |
| upload/path fail | 修正路径，通常不算有效生成 |
| success | 下载并进入 Stable File Gate |

## 10. Stable File Gate

成功返回后复制成稳定文件：

```text
returned/Segment01.mp4
returned/Segment02.mp4
returned/Segment03.mp4
returned/Segment04.mp4
```

UUID 原文件保留，方便回溯。

## 11. Safe Review Gate

自动复核包含：

- 语音转写
- 必含词检查
- 相似度
- 画面文字/Logo/水印风险
- 抽帧和裁切图

复核分层：

| 层级 | 含义 |
|---|---|
| pass | 自动检查较干净 |
| needs_human_listen | 需要人工听 |
| asr_similarity_blocked_required_terms_hit | 相似度低，但关键词命中 |
| hard_fail_missing_required_terms | 核心词缺失，建议重跑 |
| visual warning | 画面需人工看 |

自动复核不等于最终通过。

## 12. Human Review Gate

用户只能用三种判断：

```text
Segment XX 可进入下一段
Segment XX 建议重跑
Segment XX 必须重跑
```

处理：

- 可进入下一段：记录通过，提取尾帧。
- 建议重跑：记录问题，准备重跑 prompt。
- 必须重跑：阻断后续段落，先重跑当前段。

## 13. Rerun Gate

重跑前先分类：

| 标签 | 修复方向 |
|---|---|
| PRE_TNS_FAIL | 精简提示词，减少促销/否定词 |
| CHARACTER_DRIFT | 加人物参考图，改 image2video |
| VO_ERROR | 缩短台词，强化唯一旁白 |
| TEXT_ARTIFACT | 减少平板/卡片文字描述 |
| PATH_ERROR | 改绝对路径 |
| REFERENCE_OVERLOAD | 减少参考素材 |
| PROCESS_BREAK | 修状态，不扣点 |

重跑必须重新展示 prompt，并再次等待用户确认。

## 14. Final Gate

所有段落人工通过后：

- 不再准备不存在的下一段。
- 合成完整 MP4。
- 检查时长、分辨率、音频。
- 无官方 Logo 时输出无 Logo 版，并注明。
- 保留每段原文件。

## 15. Report Gate

最终交付：

- 完整成片
- 分段文件
- 可读复盘文档
- 明细版复盘备份
- 积分统计
- submit_id 清单
- 最终提示词
- 失败原因和经验
