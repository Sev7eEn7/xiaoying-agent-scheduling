# 09_batch_window · 同批次冲突 + 用户允许窗口

- 输入：`examples/inputs/09_batch_window.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/09_batch_window.json --provider deepseek --store .runtime/s09.json`
- 模型：`deepseek-flash`；模型轮次 7/15；工具调用 9/40；finish 被退回 0 次
- 任务状态：**completed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-E0F7B21A", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M09"} | ✅ 找到 M09《桌面收纳改造》，license=有 | 先读取 M09 元数据以确认审核所需信息 | get_material |
| 2 | 1 | `get_material` | {"material_id": "M10"} | ✅ 找到 M10《城市夜跑路线推荐》，license=有 | 先读取 M10 元数据以确认审核所需信息 | check_rules |
| 3 | 2 | `check_rules` | {"material_id": "M09", "publish_at": "2026-11-05T20:00"} | ✅ M09 审核 pass | M09 元数据完整，按用户要求的抖音 2026-11-05T20:00 检查审核规则与授权有效期 | check_rules |
| 4 | 2 | `check_rules` | {"material_id": "M10", "publish_at": "2026-11-05T20:00"} | ✅ M10 审核 pass | M10 元数据完整，按用户要求的抖音 2026-11-05T20:00 检查审核规则与授权有效期 | query_slots |
| 5 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-05T20:00"} | ✅ douyin 2026-11-05T20:00 free | 两个素材都要求抖音同一时段 2026-11-05T20:00，需确认该时段本身是否可用 | query_slots |
| 6 | 4 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-05T21:00", "also_taken": [{"channel": "douyin", "slot": "2026-11-05T20:00"}]} | ✅ douyin 2026-11-05T21:00 free | M09 保留 20:00，M10 需在其 18:00–22:00 窗口内找不早于原要求的最近空闲时段，先试 21:00 | check_rules |
| 7 | 5 | `check_rules` | {"material_id": "M10", "publish_at": "2026-11-05T21:00"} | ✅ M10 审核 pass | M10 的时段调整为 2026-11-05T21:00，按实际排定时段再核验一次授权与规则 | save_schedule_draft |
| 8 | 6 | `save_schedule_draft` | {"items": [{"material_id": "M09", "channel": "douyin", "slot": "2026-11-05T20:00", "confirmation_status": "not_required"}, {"material_id": "M10", "channel": "douyin", "slot": "2026-11-05T21:00", "confirmation_status": "not_required"}]} | ✅ 草稿 D-E0F7B21A created（修订 1，2 条，未发布） | 两素材均 check_rules=pass；M09 无窗口保留原时段 20:00，M10 冲突改到其 acceptable_window 内的 21:00，均与用户要求/许可窗口一致 | finish |
| 9 | 7 | `finish` | {"items": [{"material_id": "M09", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-05T20:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}, {"material_id": "M10", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-05T21:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}], "summary": "M09、M10 均通过审核（check_rules=pass，无 findings；原创、音乐授权至 2027-09-30、人物肖像授权齐备）。两素材原要求同为抖音 2026-11-05T20:00，冲突处理：保留无窗口的 M09 原时段 20:00，把有 18:00–22:00 窗口的 M10 调整到最近的空闲整点 21:00（在窗口内，故无需确认）。已合并保存为一份排期草稿 D-E0F7B21A（revision 1，仅草稿，未发布）。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M09 | pass | — | — | douyin 2026-11-05T20:00 | douyin 2026-11-05T20:00 | not_required | — | saved |
| M10 | pass | — | — | douyin 2026-11-05T20:00（可接受 18:00–22:00） | douyin 2026-11-05T21:00 | not_required | — | saved |

**模型总结**：M09、M10 均通过审核（check_rules=pass，无 findings；原创、音乐授权至 2027-09-30、人物肖像授权齐备）。两素材原要求同为抖音 2026-11-05T20:00，冲突处理：保留无窗口的 M09 原时段 20:00，把有 18:00–22:00 窗口的 M10 调整到最近的空闲整点 21:00（在窗口内，故无需确认）。已合并保存为一份排期草稿 D-E0F7B21A（revision 1，仅草稿，未发布）。
