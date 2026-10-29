# 09_batch_window · 同批次冲突 + 用户允许窗口

- 输入：`examples/inputs/09_batch_window.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/09_batch_window.json --provider deepseek --store .runtime/s09.json`
- 模型：`deepseek-flash`；模型轮次 5/15；工具调用 8/40；finish 被退回 0 次
- 任务状态：**completed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-E0F7B21A", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M09"} | ✅ 找到 M09《桌面收纳改造》，license=有 | 需要先了解 M09 的基本元数据以判断能否审核与排期。 | get_material |
| 2 | 1 | `get_material` | {"material_id": "M10"} | ✅ 找到 M10《城市夜跑路线推荐》，license=有 | 需要先了解 M10 的基本元数据以判断能否审核与排期。 | check_rules |
| 3 | 2 | `check_rules` | {"material_id": "M09", "publish_at": "2026-11-05T20:00"} | ✅ M09 审核 pass | 按请求时段 2026-11-05T20:00 校验 M09 的审核规则与授权有效期。 | check_rules |
| 4 | 2 | `check_rules` | {"material_id": "M10", "publish_at": "2026-11-05T20:00"} | ✅ M10 审核 pass | 按请求时段 2026-11-05T20:00 校验 M10 的审核规则与授权有效期。 | query_slots |
| 5 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-05T20:00"} | ✅ douyin 2026-11-05T20:00 free | M09 无窗口、保留原时段，需确认 douyin 2026-11-05T20:00 是否可用于排期。 | query_slots |
| 6 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-05T21:00", "also_taken": [{"channel": "douyin", "slot": "2026-11-05T20:00"}]} | ✅ douyin 2026-11-05T21:00 free | M10 需在 18:00–22:00 窗口内改期，优先查不早于原要求的最近时段 21:00 是否空闲（已排除规划给 M09 的 20:00）。 | save_schedule_draft |
| 7 | 4 | `save_schedule_draft` | {"items": [{"material_id": "M09", "channel": "douyin", "slot": "2026-11-05T20:00", "confirmation_status": "not_required"}, {"material_id": "M10", "channel": "douyin", "slot": "2026-11-05T21:00", "confirmation_status": "not_required", "note": "与原请求的 M09 同为 20:00 冲突，已顺延至 acceptable_window(18:00-22:00) 内的 21:00"}]} | ✅ 草稿 D-E0F7B21A created（修订 1，2 条，未发布） | 两个素材 check_rules 均为 pass，且 20:00 与 21:00 均空闲，按冲突解决规则保存为一份草稿（仅草稿，不发布）。 | finish |
| 8 | 5 | `finish` | {"items": [{"material_id": "M09", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-05T20:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}, {"material_id": "M10", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-05T21:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}], "summary": "REQ-09 处理完毕：M09、M10 审核均为 pass（无 risk findings，音乐授权分别到 2027-09-30，M10 肖像授权已具备）。二者原请求同为 douyin 2026-11-05T20:00，存在同渠道同时段冲突；按“最小改动硬性要求”原则，保留无窗口的 M09 在 20:00，把有 acceptable_window 的 M10 顺延至窗口内最近空闲时段 21:00（该时段在 18:00–22:00 窗口内，无需额外确认）。已合并保存为一份排期草稿：draft_id D-E0F7B21A（revision 1，state=draft，2 个素材）。仅为草稿，未发布、未上线。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M09 | pass | — | — | douyin 2026-11-05T20:00 | douyin 2026-11-05T20:00 | not_required | — | saved |
| M10 | pass | — | — | douyin 2026-11-05T20:00（可接受 18:00–22:00） | douyin 2026-11-05T21:00 | not_required | — | saved |

**模型总结**：REQ-09 处理完毕：M09、M10 审核均为 pass（无 risk findings，音乐授权分别到 2027-09-30，M10 肖像授权已具备）。二者原请求同为 douyin 2026-11-05T20:00，存在同渠道同时段冲突；按“最小改动硬性要求”原则，保留无窗口的 M09 在 20:00，把有 acceptable_window 的 M10 顺延至窗口内最近空闲时段 21:00（该时段在 18:00–22:00 窗口内，无需额外确认）。已合并保存为一份排期草稿：draft_id D-E0F7B21A（revision 1，state=draft，2 个素材）。仅为草稿，未发布、未上线。
