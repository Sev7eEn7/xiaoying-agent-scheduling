# 11_tool_retry · 工具首次失败后重试

- 输入：`examples/inputs/11_tool_retry.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/11_tool_retry.json --provider mock --store .runtime/s11.json --inject slots_fail_once`
- 模型：`mock-rule-policy`；模型轮次 6/15；工具调用 6/40；finish 被退回 0 次
- 任务状态：**completed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-C3257BC0", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M07"} | ✅ 找到 M07《降噪耳机通勤一周体验》，license=有 | 先读取素材元数据 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M07", "publish_at": "2026-11-08T19:00"} | ✅ M07 审核 pass | 读取成功，按发布时间做规则检查 | query_slots |
| 3 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-08T19:00", "also_taken": []} | ❌ 失败 TOOL_TIMEOUT：排期服务超时 | 审核可排期，查询目标时段 | query_slots |
| 4 | 4 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-08T19:00", "also_taken": []} | ✅ douyin 2026-11-08T19:00 free | query_slots 返回可重试错误，重试 | save_schedule_draft |
| 5 | 5 | `save_schedule_draft` | {"items": [{"material_id": "M07", "channel": "douyin", "slot": "2026-11-08T19:00", "confirmation_status": "not_required", "note": ""}]} | ✅ 草稿 D-C3257BC0 created（修订 1，1 条，未发布） | 所有素材处理完毕，保存可排期条目为草稿 | finish |
| 6 | 6 | `finish` | {"items": [{"material_id": "M07", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-08T19:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}], "summary": "共 1 个素材，1 个已保存为草稿；未发布任何内容。"} | ✅ finish 通过工具记录核对 | 全部素材已处理 | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M07 | pass | — | — | douyin 2026-11-08T19:00 | douyin 2026-11-08T19:00 | not_required | — | saved |

**模型总结**：共 1 个素材，1 个已保存为草稿；未发布任何内容。
