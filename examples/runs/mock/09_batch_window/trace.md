# 09_batch_window · 同批次冲突 + 用户允许窗口

- 输入：`examples/inputs/09_batch_window.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/09_batch_window.json --provider mock --store .runtime/s09.json`
- 模型：`mock-rule-policy`；模型轮次 8/15；工具调用 8/40；finish 被退回 0 次
- 任务状态：**completed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-E0F7B21A", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M09"} | ✅ 找到 M09《桌面收纳改造》，license=有 | 先读取素材元数据 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M09", "publish_at": "2026-11-05T20:00"} | ✅ M09 审核 pass | 读取成功，按发布时间做规则检查 | query_slots |
| 3 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-05T20:00", "also_taken": []} | ✅ douyin 2026-11-05T20:00 free | 审核可排期，查询目标时段 | get_material |
| 4 | 4 | `get_material` | {"material_id": "M10"} | ✅ 找到 M10《城市夜跑路线推荐》，license=有 | 先读取素材元数据 | check_rules |
| 5 | 5 | `check_rules` | {"material_id": "M10", "publish_at": "2026-11-05T20:00"} | ✅ M10 审核 pass | 读取成功，按发布时间做规则检查 | query_slots |
| 6 | 6 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-05T20:00", "also_taken": [{"channel": "douyin", "slot": "2026-11-05T20:00"}]} | ✅ douyin 2026-11-05T20:00 planned_in_batch（本批次已规划给其他素材）；备选 21:00、22:00、18:00、23:00 | 审核可排期，查询目标时段 | save_schedule_draft |
| 7 | 7 | `save_schedule_draft` | {"items": [{"material_id": "M09", "channel": "douyin", "slot": "2026-11-05T20:00", "confirmation_status": "not_required", "note": ""}, {"material_id": "M10", "channel": "douyin", "slot": "2026-11-05T21:00", "confirmation_status": "not_required", "note": ""}]} | ✅ 草稿 D-E0F7B21A created（修订 1，2 条，未发布） | 所有素材处理完毕，保存可排期条目为草稿 | finish |
| 8 | 8 | `finish` | {"items": [{"material_id": "M09", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-05T20:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}, {"material_id": "M10", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-05T21:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}], "summary": "共 2 个素材，2 个已保存为草稿；未发布任何内容。"} | ✅ finish 通过工具记录核对 | 全部素材已处理 | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M09 | pass | — | — | douyin 2026-11-05T20:00 | douyin 2026-11-05T20:00 | not_required | — | saved |
| M10 | pass | — | — | douyin 2026-11-05T20:00（可接受 18:00–22:00） | douyin 2026-11-05T21:00 | not_required | — | saved |

**模型总结**：共 2 个素材，2 个已保存为草稿；未发布任何内容。
