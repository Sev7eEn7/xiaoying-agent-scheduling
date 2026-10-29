# 11_tool_retry · 工具首次失败后重试

- 输入：`examples/inputs/11_tool_retry.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/11_tool_retry.json --provider deepseek --store .runtime/s11.json --inject slots_fail_once`
- 模型：`deepseek-chat`；模型轮次 6/15；工具调用 6/40；finish 被退回 0 次
- 任务状态：**completed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-C3257BC0", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M07"} | ✅ 找到 M07《降噪耳机通勤一周体验》，license=有 | 请求要求为 M07 排期到抖音 2026-11-08T19:00，先读取素材元数据以确认基本信息。 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M07", "publish_at": "2026-11-08T19:00"} | ✅ M07 审核 pass | 素材为原创、音乐授权到 2027-06-30、无人物出镜，按请求时段 2026-11-08T19:00 检查审核规则。 | query_slots |
| 3 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-08T19:00"} | ❌ 失败 TOOL_TIMEOUT：排期服务超时 | 审核通过，检查抖音 2026-11-08T19:00 是否可用。 | query_slots |
| 4 | 4 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-08T19:00"} | ✅ douyin 2026-11-08T19:00 free | 上次查询超时且可重试，重试查询抖音 2026-11-08T19:00 的占用情况。 | save_schedule_draft |
| 5 | 5 | `save_schedule_draft` | {"items": [{"material_id": "M07", "channel": "douyin", "slot": "2026-11-08T19:00", "confirmation_status": "not_required"}]} | ✅ 草稿 D-C3257BC0 created（修订 1，1 条，未发布） | M07 审核通过且抖音 2026-11-08T19:00 空闲，与用户要求一致，保存为排期草稿。 | finish |
| 6 | 6 | `finish` | {"items": [{"material_id": "M07", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-08T19:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}], "summary": "M07《降噪耳机通勤一周体验》审核通过（原创、音乐授权至 2027-06-30、无人物出镜、非商业推广），抖音 2026-11-08T19:00 空闲，已按用户要求保存为排期草稿 D-C3257BC0（revision 1），未发布。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M07 | pass | — | — | douyin 2026-11-08T19:00 | douyin 2026-11-08T19:00 | not_required | — | saved |

**模型总结**：M07《降噪耳机通勤一周体验》审核通过（原创、音乐授权至 2027-06-30、无人物出镜、非商业推广），抖音 2026-11-08T19:00 空闲，已按用户要求保存为排期草稿 D-C3257BC0（revision 1），未发布。
