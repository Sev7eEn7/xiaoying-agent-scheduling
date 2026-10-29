# 11_tool_retry · 工具首次失败后重试

- 输入：`examples/inputs/11_tool_retry.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/11_tool_retry.json --provider deepseek --store .runtime/s11.json --inject slots_fail_once`
- 模型：`deepseek-flash`；模型轮次 5/15；工具调用 6/40；finish 被退回 0 次
- 任务状态：**completed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-C3257BC0", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M07"} | ✅ 找到 M07《降噪耳机通勤一周体验》，license=有 | 需要先读取 M07 的元数据以确认渠道、授权等信息，再进行审核。 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M07", "publish_at": "2026-11-08T19:00"} | ✅ M07 审核 pass | M07 元数据完整（原创、配乐授权至 2027-06-30），需按用户要求的 2026-11-08T19:00 校验审核规则与授权有效期。 | query_slots |
| 3 | 2 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-08T19:00"} | ❌ 失败 TOOL_TIMEOUT：排期服务超时 | 需确认用户要求的抖音 2026-11-08T19:00 是否可用，本批次仅 M07 一项。 | query_slots |
| 4 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-08T19:00"} | ✅ douyin 2026-11-08T19:00 free | 上次排期服务超时（retryable=true），按规则重试查询抖音 2026-11-08T19:00 的占用情况。 | save_schedule_draft |
| 5 | 4 | `save_schedule_draft` | {"items": [{"material_id": "M07", "channel": "douyin", "slot": "2026-11-08T19:00", "confirmation_status": "not_required"}]} | ✅ 草稿 D-C3257BC0 created（修订 1，1 条，未发布） | M07 审核结果为 pass，抖音 2026-11-08T19:00 查询为 free，且与用户硬性要求一致，故按原时段保存草稿。 | finish |
| 6 | 5 | `finish` | {"items": [{"material_id": "M07", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-08T19:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}], "summary": "M07（降噪耳机通勤一周体验）审核通过：原创素材，版权方为内容组A；配乐 MUS-1188 授权至 2027-06-30，覆盖 2026-11-08 发布日；无真人出镜、非商业推广、无需广告标识，check_rules 无 findings。抖音 2026-11-08T19:00 查询为 free，与用户要求完全一致，无需任何改动，confirmation_status=not_required。已将该素材保存为排期草稿 D-C3257BC0（revision 1，状态 draft，仅占位未发布）。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M07 | pass | — | — | douyin 2026-11-08T19:00 | douyin 2026-11-08T19:00 | not_required | — | saved |

**模型总结**：M07（降噪耳机通勤一周体验）审核通过：原创素材，版权方为内容组A；配乐 MUS-1188 授权至 2027-06-30，覆盖 2026-11-08 发布日；无真人出镜、非商业推广、无需广告标识，check_rules 无 findings。抖音 2026-11-08T19:00 查询为 free，与用户要求完全一致，无需任何改动，confirmation_status=not_required。已将该素材保存为排期草稿 D-C3257BC0（revision 1，状态 draft，仅占位未发布）。
