# 11_tool_retry · 工具首次失败后重试

- 输入：`examples/inputs/11_tool_retry.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/11_tool_retry.json --provider deepseek --store .runtime/s11.json --inject slots_fail_once`
- 模型：`deepseek-flash`；模型轮次 6/15；工具调用 6/40；finish 被退回 0 次
- 任务状态：**completed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-C3257BC0", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M07"} | ✅ 找到 M07《降噪耳机通勤一周体验》，license=有 | 处理排期请求 REQ-11，先读取 M07 的元数据以了解素材信息。 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M07", "publish_at": "2026-11-08T19:00"} | ✅ M07 审核 pass | M07 元数据齐全，按用户要求时段 2026-11-08T19:00 校验审核规则与授权有效期。 | query_slots |
| 3 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-08T19:00"} | ❌ 失败 TOOL_TIMEOUT：排期服务超时 | M07 审核结果为 pass，检查用户要求的抖音 2026-11-08T19:00 是否空闲。 | query_slots |
| 4 | 4 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-08T19:00"} | ✅ douyin 2026-11-08T19:00 free | 上一次 query_slots 返回可重试超时，重新查询抖音 2026-11-08T19:00 的占用情况。 | save_schedule_draft |
| 5 | 5 | `save_schedule_draft` | {"items": [{"material_id": "M07", "channel": "douyin", "slot": "2026-11-08T19:00", "confirmation_status": "not_required"}]} | ✅ 草稿 D-C3257BC0 created（修订 1，1 条，未发布） | M07 审核 pass 且抖音 2026-11-08T19:00 空闲，与用户要求完全一致，保存为草稿。 | finish |
| 6 | 6 | `finish` | {"items": [{"material_id": "M07", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-08T19:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}], "summary": "REQ-11 处理完成：M07《降噪耳机通勤一周体验》原创（版权持有方内容组A），配乐授权 MUS-1188 有效期至 2027-06-30，无人物出镜、非商业、无广告标识，按 2026-11-08T19:00 校验规则结果为 pass。抖音该时段查询为空闲，与用户要求一致，无需改动。已保存为排期草稿 D-C3257BC0（修订 1），仅草稿状态，尚未发布。无待确认事项。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M07 | pass | — | — | douyin 2026-11-08T19:00 | douyin 2026-11-08T19:00 | not_required | — | saved |

**模型总结**：REQ-11 处理完成：M07《降噪耳机通勤一周体验》原创（版权持有方内容组A），配乐授权 MUS-1188 有效期至 2027-06-30，无人物出镜、非商业、无广告标识，按 2026-11-08T19:00 校验规则结果为 pass。抖音该时段查询为空闲，与用户要求一致，无需改动。已保存为排期草稿 D-C3257BC0（修订 1），仅草稿状态，尚未发布。无待确认事项。
