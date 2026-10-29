# 09_batch_window · 同批次冲突 + 用户允许窗口

- 输入：`examples/inputs/09_batch_window.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/09_batch_window.json --provider deepseek --store .runtime/s09.json`
- 模型：`deepseek-chat`；模型轮次 7/15；工具调用 9/40；finish 被退回 0 次
- 任务状态：**completed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-E0F7B21A", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M09"} | ✅ 找到 M09《桌面收纳改造》，license=有 | 需要读取 M09 元数据以进行审核与排期 | get_material |
| 2 | 1 | `get_material` | {"material_id": "M10"} | ✅ 找到 M10《城市夜跑路线推荐》，license=有 | 需要读取 M10 元数据以进行审核与排期 | check_rules |
| 3 | 2 | `check_rules` | {"material_id": "M09", "publish_at": "2026-11-05T20:00"} | ✅ M09 审核 pass | M09 元数据完整，按请求时段 2026-11-05T20:00 检查审核规则 | check_rules |
| 4 | 2 | `check_rules` | {"material_id": "M10", "publish_at": "2026-11-05T20:00"} | ✅ M10 审核 pass | M10 元数据完整，按请求时段 2026-11-05T20:00 检查审核规则 | query_slots |
| 5 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-05T20:00"} | ✅ douyin 2026-11-05T20:00 free | M09 与 M10 都要求抖音 2026-11-05T20:00，需确认该时段是否可用 | query_slots |
| 6 | 4 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-05T21:00", "also_taken": [{"channel": "douyin", "slot": "2026-11-05T20:00"}]} | ✅ douyin 2026-11-05T21:00 free | M09 保留 20:00，M10 需在 18:00–22:00 窗口内找不早于原要求的最近空闲时段，先查 21:00 | check_rules |
| 7 | 5 | `check_rules` | {"material_id": "M10", "publish_at": "2026-11-05T21:00"} | ✅ M10 审核 pass | M10 时段调整为 21:00，需按新时段重新检查审核规则 | save_schedule_draft |
| 8 | 6 | `save_schedule_draft` | {"items": [{"material_id": "M09", "channel": "douyin", "slot": "2026-11-05T20:00", "confirmation_status": "not_required"}, {"material_id": "M10", "channel": "douyin", "slot": "2026-11-05T21:00", "confirmation_status": "not_required"}]} | ✅ 草稿 D-E0F7B21A created（修订 1，2 条，未发布） | 两素材均通过审核；M09 保留原时段 20:00，M10 因时段冲突调整到其允许窗口内的 21:00，均无需额外确认 | finish |
| 9 | 7 | `finish` | {"items": [{"material_id": "M09", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-05T20:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}, {"material_id": "M10", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-05T21:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}], "summary": "M09、M10 均通过审核（无风险项）。两者原都要求抖音 2026-11-05T20:00，同一渠道同一时段冲突；M10 有 18:00–22:00 允许窗口，故将其调整到窗口内不早于原要求的最近空闲时段 21:00（已按新时段重新检查规则，仍 pass），M09 保留原时段 20:00。两份素材已合并保存为排期草稿 D-E0F7B21A（revision 1），仅为草稿，未发布。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M09 | pass | — | — | douyin 2026-11-05T20:00 | douyin 2026-11-05T20:00 | not_required | — | saved |
| M10 | pass | — | — | douyin 2026-11-05T20:00（可接受 18:00–22:00） | douyin 2026-11-05T21:00 | not_required | — | saved |

**模型总结**：M09、M10 均通过审核（无风险项）。两者原都要求抖音 2026-11-05T20:00，同一渠道同一时段冲突；M10 有 18:00–22:00 允许窗口，故将其调整到窗口内不早于原要求的最近空闲时段 21:00（已按新时段重新检查规则，仍 pass），M09 保留原时段 20:00。两份素材已合并保存为排期草稿 D-E0F7B21A（revision 1），仅为草稿，未发布。
