# 09_batch_window · 同批次冲突 + 用户允许窗口

- 输入：`examples/inputs/09_batch_window.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/09_batch_window.json --provider deepseek --store .runtime/s09.json`
- 模型：`deepseek-chat`；模型轮次 6/15；工具调用 8/40；finish 被退回 0 次
- 任务状态：**needs_confirmation**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-E0F7B21A", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M09"} | ✅ 找到 M09《桌面收纳改造》，license=有 | 请求要求为 M09 排期，先读取素材元数据以确认基本信息。 | get_material |
| 2 | 1 | `get_material` | {"material_id": "M10"} | ✅ 找到 M10《城市夜跑路线推荐》，license=有 | 请求要求为 M10 排期，先读取素材元数据以确认基本信息。 | check_rules |
| 3 | 2 | `check_rules` | {"material_id": "M09", "publish_at": "2026-11-05T20:00"} | ✅ M09 审核 pass | M09 元数据完整，按请求时段 2026-11-05T20:00 执行审核规则检查。 | check_rules |
| 4 | 2 | `check_rules` | {"material_id": "M10", "publish_at": "2026-11-05T20:00"} | ✅ M10 审核 pass | M10 元数据完整，按请求时段 2026-11-05T20:00 执行审核规则检查。 | query_slots |
| 5 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-05T20:00"} | ✅ douyin 2026-11-05T20:00 free | M09 与 M10 均要求 douyin 2026-11-05T20:00，需确认该时段是否可用及备选时段。 | query_slots |
| 6 | 4 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-05T20:00", "also_taken": [{"channel": "douyin", "slot": "2026-11-05T20:00"}]} | ✅ douyin 2026-11-05T20:00 planned_in_batch（本批次已规划给其他素材）；备选 21:00、22:00、18:00、23:00 | 20:00 已规划给 M09，需为 M10 查询同渠道其他可用时段（M10 允许窗口 18:00–22:00）。 | save_schedule_draft |
| 7 | 5 | `save_schedule_draft` | {"items": [{"material_id": "M09", "channel": "douyin", "slot": "2026-11-05T20:00", "confirmation_status": "not_required"}, {"material_id": "M10", "channel": "douyin", "slot": "2026-11-05T21:00", "confirmation_status": "not_required", "note": "原请求 20:00 与 M09 冲突，改到 21:00，落在其允许窗口 18:00–22:00 内"}]} | ✅ 草稿 D-E0F7B21A created（修订 1，2 条，未发布） | 两素材均审核通过；M09 按请求 20:00，M10 因同渠道同时段冲突改到允许窗口内的 21:00，保存为草稿。 | finish |
| 8 | 6 | `finish` | {"items": [{"material_id": "M09", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-05T20:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}, {"material_id": "M10", "review_status": "pass", "risk_reasons": ["原请求 douyin 2026-11-05T20:00 与 M09 同渠道同时段冲突，已改到允许窗口 18:00–22:00 内的 21:00"], "suggested_channel": "douyin", "suggested_slot": "2026-11-05T21:00", "confirmation_status": "not_required", "pending_items": ["M10 时段由 20:00 调整为 21:00（落在其 acceptable_window 内），如需保留 20:00 请调整 M09 或另行指定"], "in_draft": true}], "summary": "M09、M10 均通过审核（pass）。两者原请求同为 douyin 2026-11-05T20:00，存在同渠道同时段冲突：M09 保留 20:00，M10 调整到其允许窗口 18:00–22:00 内的 21:00。已合并保存为排期草稿 D-E0F7B21A（revision 1），仅为草稿，未发布。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M09 | pass | — | — | douyin 2026-11-05T20:00 | douyin 2026-11-05T20:00 | not_required | — | saved |
| M10 | pass | ["原请求 douyin 2026-11-05T20:00 与 M09 同渠道同时段冲突，已改到允许窗口 18:00–22:00 内的 21:00"] | — | douyin 2026-11-05T20:00（可接受 18:00–22:00） | douyin 2026-11-05T21:00 | not_required | ["M10 时段由 20:00 调整为 21:00（落在其 acceptable_window 内），如需保留 20:00 请调整 M09 或另行指定"] | saved |

**模型总结**：M09、M10 均通过审核（pass）。两者原请求同为 douyin 2026-11-05T20:00，存在同渠道同时段冲突：M09 保留 20:00，M10 调整到其允许窗口 18:00–22:00 内的 21:00。已合并保存为排期草稿 D-E0F7B21A（revision 1），仅为草稿，未发布。
