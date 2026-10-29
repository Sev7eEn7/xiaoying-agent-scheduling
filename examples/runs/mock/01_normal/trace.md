# 01_normal · 正常排期

- 输入：`examples/inputs/01_normal.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/01_normal.json --provider mock --store .runtime/s01.json`
- 模型：`mock-rule-policy`；模型轮次 8/15；工具调用 8/40；finish 被退回 0 次
- 任务状态：**completed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-6FDF3501", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M02"} | ✅ 找到 M02《秋季通勤三套穿搭》，license=有 | 先读取素材元数据 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M02", "publish_at": "2026-11-04T12:00"} | ✅ M02 审核 pass | 读取成功，按发布时间做规则检查 | query_slots |
| 3 | 3 | `query_slots` | {"channel": "xiaohongshu", "publish_at": "2026-11-04T12:00", "also_taken": []} | ✅ xiaohongshu 2026-11-04T12:00 free | 审核可排期，查询目标时段 | get_material |
| 4 | 4 | `get_material` | {"material_id": "M07"} | ✅ 找到 M07《降噪耳机通勤一周体验》，license=有 | 先读取素材元数据 | check_rules |
| 5 | 5 | `check_rules` | {"material_id": "M07", "publish_at": "2026-11-04T19:00"} | ✅ M07 审核 pass | 读取成功，按发布时间做规则检查 | query_slots |
| 6 | 6 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-04T19:00", "also_taken": [{"channel": "xiaohongshu", "slot": "2026-11-04T12:00"}]} | ✅ douyin 2026-11-04T19:00 free | 审核可排期，查询目标时段 | save_schedule_draft |
| 7 | 7 | `save_schedule_draft` | {"items": [{"material_id": "M02", "channel": "xiaohongshu", "slot": "2026-11-04T12:00", "confirmation_status": "not_required", "note": ""}, {"material_id": "M07", "channel": "douyin", "slot": "2026-11-04T19:00", "confirmation_status": "not_required", "note": ""}]} | ✅ 草稿 D-6FDF3501 created（修订 1，2 条，未发布） | 所有素材处理完毕，保存可排期条目为草稿 | finish |
| 8 | 8 | `finish` | {"items": [{"material_id": "M02", "review_status": "pass", "risk_reasons": [], "suggested_channel": "xiaohongshu", "suggested_slot": "2026-11-04T12:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}, {"material_id": "M07", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-04T19:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}], "summary": "共 2 个素材，2 个已保存为草稿；未发布任何内容。"} | ✅ finish 通过工具记录核对 | 全部素材已处理 | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M02 | pass | — | — | xiaohongshu 2026-11-04T12:00 | xiaohongshu 2026-11-04T12:00 | not_required | — | saved |
| M07 | pass | — | — | douyin 2026-11-04T19:00 | douyin 2026-11-04T19:00 | not_required | — | saved |

**模型总结**：共 2 个素材，2 个已保存为草稿；未发布任何内容。
