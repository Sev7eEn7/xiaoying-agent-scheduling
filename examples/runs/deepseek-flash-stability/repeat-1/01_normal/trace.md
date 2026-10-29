# 01_normal · 正常排期

- 输入：`examples/inputs/01_normal.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/01_normal.json --provider deepseek --store .runtime/s01.json`
- 模型：`deepseek-flash`；模型轮次 5/15；工具调用 8/40；finish 被退回 0 次
- 任务状态：**completed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-6FDF3501", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M02"} | ✅ 找到 M02《秋季通勤三套穿搭》，license=有 | 先读取 M02 元数据，用于确认版权信息、授权窗口等审核前置条件 | get_material |
| 2 | 1 | `get_material` | {"material_id": "M07"} | ✅ 找到 M07《降噪耳机通勤一周体验》，license=有 | 同时读取 M07 元数据，用于确认版权信息、授权窗口等审核前置条件 | check_rules |
| 3 | 2 | `check_rules` | {"material_id": "M02", "publish_at": "2026-11-04T12:00"} | ✅ M02 审核 pass | M02 元数据完整（原创、有肖像授权），按请求时段检查规则是否通过 | check_rules |
| 4 | 2 | `check_rules` | {"material_id": "M07", "publish_at": "2026-11-04T19:00"} | ✅ M07 审核 pass | M07 元数据完整（原创、音乐授权至2027-06-30），按请求时段检查规则是否通过 | query_slots |
| 5 | 3 | `query_slots` | {"channel": "xiaohongshu", "publish_at": "2026-11-04T12:00"} | ✅ xiaohongshu 2026-11-04T12:00 free | M02 规则通过，检查小红书 11-04 12:00 是否可用 | query_slots |
| 6 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-04T19:00"} | ✅ douyin 2026-11-04T19:00 free | M07 规则通过，检查抖音 11-04 19:00 是否可用 | save_schedule_draft |
| 7 | 4 | `save_schedule_draft` | {"items": [{"material_id": "M02", "channel": "xiaohongshu", "slot": "2026-11-04T12:00", "confirmation_status": "not_required"}, {"material_id": "M07", "channel": "douyin", "slot": "2026-11-04T19:00", "confirmation_status": "not_required"}]} | ✅ 草稿 D-6FDF3501 created（修订 1，2 条，未发布） | 两个素材规则均 pass，且各自渠道请求时段均 free，按用户原始要求保存草稿 | finish |
| 8 | 5 | `finish` | {"items": [{"material_id": "M02", "review_status": "pass", "risk_reasons": [], "suggested_channel": "xiaohongshu", "suggested_slot": "2026-11-04T12:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}, {"material_id": "M07", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-04T19:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}], "summary": "两个素材均审核通过（规则 pass，版权/音乐授权齐全），所请求时段在小红书与抖音各自渠道均为空闲，且不冲突，已按原始要求保存为排期草稿 D-6FDF3501（revision 1，仅草稿未发布）。无需用户确认或补充事项。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M02 | pass | — | — | xiaohongshu 2026-11-04T12:00 | xiaohongshu 2026-11-04T12:00 | not_required | — | saved |
| M07 | pass | — | — | douyin 2026-11-04T19:00 | douyin 2026-11-04T19:00 | not_required | — | saved |

**模型总结**：两个素材均审核通过（规则 pass，版权/音乐授权齐全），所请求时段在小红书与抖音各自渠道均为空闲，且不冲突，已按原始要求保存为排期草稿 D-6FDF3501（revision 1，仅草稿未发布）。无需用户确认或补充事项。
