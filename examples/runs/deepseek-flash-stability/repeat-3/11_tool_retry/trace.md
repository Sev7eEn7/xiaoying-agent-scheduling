# 11_tool_retry · 工具首次失败后重试

- 输入：`examples/inputs/11_tool_retry.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/11_tool_retry.json --provider deepseek --store .runtime/s11.json --inject slots_fail_once`
- 模型：`deepseek-flash`；模型轮次 6/15；工具调用 6/40；finish 被退回 0 次
- 任务状态：**completed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-C3257BC0", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M07"} | ✅ 找到 M07《降噪耳机通勤一周体验》，license=有 | 请求 REQ-11 需要先读取素材 M07 的元数据以判断审核前提。 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M07", "publish_at": "2026-11-08T19:00"} | ✅ M07 审核 pass | 元数据显示 M07 为原创、音乐授权到 2027-06-30、无人物出镜，现按请求时段校验审核规则。 | query_slots |
| 3 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-08T19:00"} | ❌ 失败 TOOL_TIMEOUT：排期服务超时 | M07 审核结果为 pass，需确认抖音 2026-11-08 19:00 这一用户指定时段是否可用。 | query_slots |
| 4 | 4 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-08T19:00"} | ✅ douyin 2026-11-08T19:00 free | 上次查询排期服务超时且标记可重试，现重试同一时段查询（第 1 次重试）。 | save_schedule_draft |
| 5 | 5 | `save_schedule_draft` | {"items": [{"material_id": "M07", "channel": "douyin", "slot": "2026-11-08T19:00", "confirmation_status": "not_required"}]} | ✅ 草稿 D-C3257BC0 created（修订 1，1 条，未发布） | M07 审核 pass 且抖音 2026-11-08 19:00 为空闲，与用户要求一致，保存为草稿（不发布）。 | finish |
| 6 | 6 | `finish` | {"items": [{"material_id": "M07", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-08T19:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}], "summary": "REQ-11 共 1 条素材：M07（降噪耳机通勤一周体验）按 2026-10-28 规则版本检查结果为 pass，无风险发现；音乐授权有效期至 2027-06-30，覆盖发布日。抖音 2026-11-08 19:00 时段空闲，与用户要求一致，无需改动。已保存为排期草稿 D-C3257BC0（revision 1，仅草稿，未发布）。无待确认事项。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M07 | pass | — | — | douyin 2026-11-08T19:00 | douyin 2026-11-08T19:00 | not_required | — | saved |

**模型总结**：REQ-11 共 1 条素材：M07（降噪耳机通勤一周体验）按 2026-10-28 规则版本检查结果为 pass，无风险发现；音乐授权有效期至 2027-06-30，覆盖发布日。抖音 2026-11-08 19:00 时段空闲，与用户要求一致，无需改动。已保存为排期草稿 D-C3257BC0（revision 1，仅草稿，未发布）。无待确认事项。
