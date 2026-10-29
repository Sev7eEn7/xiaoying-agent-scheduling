# 01_normal · 正常排期

- 输入：`examples/inputs/01_normal.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/01_normal.json --provider deepseek --store .runtime/s01.json`
- 模型：`deepseek-chat`；模型轮次 5/15；工具调用 8/40；finish 被退回 0 次
- 任务状态：**completed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-6FDF3501", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M02"} | ✅ 找到 M02《秋季通勤三套穿搭》，license=有 | 请求要求为 M02 排期，先读取素材元数据以确认基本信息。 | get_material |
| 2 | 1 | `get_material` | {"material_id": "M07"} | ✅ 找到 M07《降噪耳机通勤一周体验》，license=有 | 请求要求为 M07 排期，先读取素材元数据以确认基本信息。 | check_rules |
| 3 | 2 | `check_rules` | {"material_id": "M02", "publish_at": "2026-11-04T12:00"} | ✅ M02 审核 pass | M02 元数据完整（原创、有肖像授权），按请求时段 2026-11-04T12:00 执行审核规则检查。 | check_rules |
| 4 | 2 | `check_rules` | {"material_id": "M07", "publish_at": "2026-11-04T19:00"} | ✅ M07 审核 pass | M07 元数据完整（原创、音乐授权至 2027-06-30），按请求时段 2026-11-04T19:00 执行审核规则检查。 | query_slots |
| 5 | 3 | `query_slots` | {"channel": "xiaohongshu", "publish_at": "2026-11-04T12:00"} | ✅ xiaohongshu 2026-11-04T12:00 free | M02 审核通过，检查小红书 2026-11-04T12:00 是否可用。 | query_slots |
| 6 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-04T19:00"} | ✅ douyin 2026-11-04T19:00 free | M07 审核通过，检查抖音 2026-11-04T19:00 是否可用。 | save_schedule_draft |
| 7 | 4 | `save_schedule_draft` | {"items": [{"material_id": "M02", "channel": "xiaohongshu", "slot": "2026-11-04T12:00", "confirmation_status": "not_required"}, {"material_id": "M07", "channel": "douyin", "slot": "2026-11-04T19:00", "confirmation_status": "not_required"}]} | ✅ 草稿 D-6FDF3501 created（修订 1，2 条，未发布） | M02、M07 审核均 pass，且各自请求时段查询为 free，按用户要求时段保存草稿。 | finish |
| 8 | 5 | `finish` | {"items": [{"material_id": "M02", "review_status": "pass", "risk_reasons": [], "suggested_channel": "xiaohongshu", "suggested_slot": "2026-11-04T12:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}, {"material_id": "M07", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-04T19:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}], "summary": "REQ-01 两个素材均审核通过：M02（秋季通勤三套穿搭，原创、肖像授权齐全）排小红书 2026-11-04T12:00；M07（降噪耳机通勤一周体验，原创、音乐授权至 2027-06-30）排抖音 2026-11-04T19:00。两个时段查询均为空闲且渠道不同无冲突，已按用户要求时段保存为排期草稿 D-6FDF3501（revision 1），未发布。无待确认项。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M02 | pass | — | — | xiaohongshu 2026-11-04T12:00 | xiaohongshu 2026-11-04T12:00 | not_required | — | saved |
| M07 | pass | — | — | douyin 2026-11-04T19:00 | douyin 2026-11-04T19:00 | not_required | — | saved |

**模型总结**：REQ-01 两个素材均审核通过：M02（秋季通勤三套穿搭，原创、肖像授权齐全）排小红书 2026-11-04T12:00；M07（降噪耳机通勤一周体验，原创、音乐授权至 2027-06-30）排抖音 2026-11-04T19:00。两个时段查询均为空闲且渠道不同无冲突，已按用户要求时段保存为排期草稿 D-6FDF3501（revision 1），未发布。无待确认项。
