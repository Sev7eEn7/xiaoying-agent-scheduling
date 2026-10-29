# 09_batch_window · 同批次冲突 + 用户允许窗口

- 输入：`examples/inputs/09_batch_window.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/09_batch_window.json --provider deepseek --store .runtime/s09.json`
- 模型：`deepseek-flash`；模型轮次 6/15；工具调用 9/40；finish 被退回 0 次
- 任务状态：**completed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-E0F7B21A", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M09"} | ✅ 找到 M09《桌面收纳改造》，license=有 | 请求中两个素材需先确认元数据是否存在及是否含版权信息。 | get_material |
| 2 | 1 | `get_material` | {"material_id": "M10"} | ✅ 找到 M10《城市夜跑路线推荐》，license=有 | 请求中两个素材需先确认元数据是否存在及是否含版权信息。 | check_rules |
| 3 | 2 | `check_rules` | {"material_id": "M09", "publish_at": "2026-11-05T20:00"} | ✅ M09 审核 pass | M09 元数据齐全，按其请求的 2026-11-05T20:00 校验审核规则与授权有效期。 | check_rules |
| 4 | 2 | `check_rules` | {"material_id": "M10", "publish_at": "2026-11-05T20:00"} | ✅ M10 审核 pass | M10 元数据齐全（含肖像授权），按其请求的 2026-11-05T20:00 校验审核规则与授权有效期。 | query_slots |
| 5 | 2 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-05T20:00"} | ✅ douyin 2026-11-05T20:00 free | 两个素材都请求抖音 2026-11-05T20:00，需确认该时段占用情况。 | query_slots |
| 6 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-05T21:00", "also_taken": [{"channel": "douyin", "slot": "2026-11-05T20:00"}]} | ✅ douyin 2026-11-05T21:00 free | M09 无允许窗口需保留 20:00，为有 18:00–22:00 窗口的 M10 查询不早于原要求的最近空闲时段（20:00 已规划给 M09）。 | check_rules |
| 7 | 4 | `check_rules` | {"material_id": "M10", "publish_at": "2026-11-05T21:00"} | ✅ M10 审核 pass | M10 拟改到窗口内的 21:00，重新校验该时段下的审核规则。 | save_schedule_draft |
| 8 | 5 | `save_schedule_draft` | {"items": [{"material_id": "M09", "channel": "douyin", "slot": "2026-11-05T20:00", "confirmation_status": "not_required"}, {"material_id": "M10", "channel": "douyin", "slot": "2026-11-05T21:00", "confirmation_status": "not_required", "note": "与 M09 争同一时段，按用户给出的 acceptable_window 18:00–22:00 调整到 21:00"}]} | ✅ 草稿 D-E0F7B21A created（修订 1，2 条，未发布） | 两个素材 check_rules 均为 pass，20:00 已规划给无窗口的 M09，M10 改到其允许窗口内的 21:00（已确认空闲且重新检查通过）。 | finish |
| 9 | 6 | `finish` | {"items": [{"material_id": "M09", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-05T20:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}, {"material_id": "M10", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-05T21:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}], "summary": "M09、M10 审核均 pass（原创素材、音乐授权至 2027-09-30、M10 已有肖像授权，无风险项）。两者原本都要求抖音 2026-11-05 20:00，冲突：M09 无允许窗口，保留 20:00；M10 改到其 acceptable_window（18:00–22:00）内的 21:00，且该时段空闲、重新检查通过，属于用户已授权的可调整范围，无需额外确认。两个素材已合并保存为排期草稿 D-E0F7B21A（修订 1，state=draft），未发布也未上线，请内容团队在草稿中复核后再走发布流程。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M09 | pass | — | — | douyin 2026-11-05T20:00 | douyin 2026-11-05T20:00 | not_required | — | saved |
| M10 | pass | — | — | douyin 2026-11-05T20:00（可接受 18:00–22:00） | douyin 2026-11-05T21:00 | not_required | — | saved |

**模型总结**：M09、M10 审核均 pass（原创素材、音乐授权至 2027-09-30、M10 已有肖像授权，无风险项）。两者原本都要求抖音 2026-11-05 20:00，冲突：M09 无允许窗口，保留 20:00；M10 改到其 acceptable_window（18:00–22:00）内的 21:00，且该时段空闲、重新检查通过，属于用户已授权的可调整范围，无需额外确认。两个素材已合并保存为排期草稿 D-E0F7B21A（修订 1，state=draft），未发布也未上线，请内容团队在草稿中复核后再走发布流程。
