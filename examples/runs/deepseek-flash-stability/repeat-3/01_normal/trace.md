# 01_normal · 正常排期

- 输入：`examples/inputs/01_normal.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/01_normal.json --provider deepseek --store .runtime/s01.json`
- 模型：`deepseek-flash`；模型轮次 4/15；工具调用 8/40；finish 被退回 0 次
- 任务状态：**completed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-6FDF3501", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M02"} | ✅ 找到 M02《秋季通勤三套穿搭》，license=有 | 需要读取 M02 的元数据以进行审核 | get_material |
| 2 | 1 | `get_material` | {"material_id": "M07"} | ✅ 找到 M07《降噪耳机通勤一周体验》，license=有 | 需要读取 M07 的元数据以进行审核 | check_rules |
| 3 | 2 | `check_rules` | {"material_id": "M02", "publish_at": "2026-11-04T12:00"} | ✅ M02 审核 pass | 按请求的小红书时段校验 M02 的审核规则与授权有效期 | check_rules |
| 4 | 2 | `check_rules` | {"material_id": "M07", "publish_at": "2026-11-04T19:00"} | ✅ M07 审核 pass | 按请求的抖音时段校验 M07 的审核规则与授权有效期 | query_slots |
| 5 | 2 | `query_slots` | {"channel": "xiaohongshu", "publish_at": "2026-11-04T12:00"} | ✅ xiaohongshu 2026-11-04T12:00 free | 确认 M02 请求的小红书 11-04 12:00 是否可用 | query_slots |
| 6 | 2 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-04T19:00"} | ✅ douyin 2026-11-04T19:00 free | 确认 M07 请求的抖音 11-04 19:00 是否可用 | save_schedule_draft |
| 7 | 3 | `save_schedule_draft` | {"items": [{"material_id": "M02", "channel": "xiaohongshu", "slot": "2026-11-04T12:00", "confirmation_status": "not_required"}, {"material_id": "M07", "channel": "douyin", "slot": "2026-11-04T19:00", "confirmation_status": "not_required"}]} | ✅ 草稿 D-6FDF3501 created（修订 1，2 条，未发布） | M02 与 M07 均 check_rules=pass，且各自请求时段查询为 free，按用户硬性要求原样排入草稿 | finish |
| 8 | 4 | `finish` | {"items": [{"material_id": "M02", "review_status": "pass", "risk_reasons": [], "suggested_channel": "xiaohongshu", "suggested_slot": "2026-11-04T12:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}, {"material_id": "M07", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-04T19:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}], "summary": "REQ-01：M02（小红书 11-04 12:00）与 M07（抖音 11-04 19:00）审核均为 pass，无 findings；两个时段查询均为 free，且渠道不同无时段冲突，已按用户硬性要求原样保存为排期草稿 D-6FDF3501（修订 1，state=draft，仅草稿未发布）。无需人工复核或补充信息，无待确认项。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M02 | pass | — | — | xiaohongshu 2026-11-04T12:00 | xiaohongshu 2026-11-04T12:00 | not_required | — | saved |
| M07 | pass | — | — | douyin 2026-11-04T19:00 | douyin 2026-11-04T19:00 | not_required | — | saved |

**模型总结**：REQ-01：M02（小红书 11-04 12:00）与 M07（抖音 11-04 19:00）审核均为 pass，无 findings；两个时段查询均为 free，且渠道不同无时段冲突，已按用户硬性要求原样保存为排期草稿 D-6FDF3501（修订 1，state=draft，仅草稿未发布）。无需人工复核或补充信息，无待确认项。
