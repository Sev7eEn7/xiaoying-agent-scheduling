# 11_tool_retry · 工具首次失败后重试

- 输入：`examples/inputs/11_tool_retry.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/11_tool_retry.json --provider deepseek --store .runtime/s11.json --inject slots_fail_once`
- 模型：`deepseek-flash`；模型轮次 5/15；工具调用 6/40；finish 被退回 0 次
- 任务状态：**completed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-C3257BC0", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M07"} | ✅ 找到 M07《降噪耳机通勤一周体验》，license=有 | 请求要求为 M07 排期，先读取其元数据以确认渠道、版权与授权信息。 | check_rules |
| 2 | 1 | `check_rules` | {"material_id": "M07", "publish_at": "2026-11-08T19:00"} | ✅ M07 审核 pass | 按用户请求的 douyin 2026-11-08T19:00 直接做规则检查，确认审核结论。 | query_slots |
| 3 | 2 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-08T19:00"} | ❌ 失败 TOOL_TIMEOUT：排期服务超时 | M07 规则检查为 pass，需确认 douyin 原要求时段 2026-11-08T19:00 是否可用再决定是否保存草稿。 | query_slots |
| 4 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-08T19:00"} | ✅ douyin 2026-11-08T19:00 free | 上次 query_slots 返回 retryable 的 TOOL_TIMEOUT，按规则重试同一时段查询。 | save_schedule_draft |
| 5 | 4 | `save_schedule_draft` | {"items": [{"material_id": "M07", "channel": "douyin", "slot": "2026-11-08T19:00", "confirmation_status": "not_required"}]} | ✅ 草稿 D-C3257BC0 created（修订 1，1 条，未发布） | M07 审核为 pass 且 douyin 2026-11-08T19:00 查询为 free，符合用户硬性要求，保存为草稿。 | finish |
| 6 | 5 | `finish` | {"items": [{"material_id": "M07", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-08T19:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}], "summary": "M07《降噪耳机通勤一周体验》：原创素材（holder 内容组A，音乐授权 MUS-1188 至 2027-06-30），无人物出镜、非商业、无广告标识，check_rules 在 2026-11-08T19:00 结果为 pass，无风险项。douyin 2026-11-08T19:00 查询为空闲，与用户要求完全一致，无需确认，已保存为排期草稿 D-C3257BC0（revision 1，仅草稿、未发布）。本次无需人工复核或补充资料。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M07 | pass | — | — | douyin 2026-11-08T19:00 | douyin 2026-11-08T19:00 | not_required | — | saved |

**模型总结**：M07《降噪耳机通勤一周体验》：原创素材（holder 内容组A，音乐授权 MUS-1188 至 2027-06-30），无人物出镜、非商业、无广告标识，check_rules 在 2026-11-08T19:00 结果为 pass，无风险项。douyin 2026-11-08T19:00 查询为空闲，与用户要求完全一致，无需确认，已保存为排期草稿 D-C3257BC0（revision 1，仅草稿、未发布）。本次无需人工复核或补充资料。
