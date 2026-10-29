# 07_rule_risk · 规则风险：阻断与人工复核

- 输入：`examples/inputs/07_rule_risk.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/07_rule_risk.json --provider deepseek --store .runtime/s07.json`
- 模型：`deepseek-chat`；模型轮次 5/15；工具调用 7/40；finish 被退回 0 次
- 任务状态：**needs_confirmation**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-DD1748B1", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M04"} | ✅ 找到 M04《祛痘精华推广》，license=有 | 需要读取 M04 元数据以进行审核与排期 | get_material |
| 2 | 1 | `get_material` | {"material_id": "M06"} | ✅ 找到 M06《双11预热海报》，license=有 | 需要读取 M06 元数据以进行审核与排期 | check_rules |
| 3 | 2 | `check_rules` | {"material_id": "M04", "publish_at": "2026-11-07T20:00"} | ✅ M04 审核 block：R04[block] 包含广告法禁用的极限用语（最有效、全网最、100%）；R05[review] 疑似功效/医疗宣称，需法务复核（祛痘、根治）；R06[review] 商业合作内容未标注“广告” | 按请求时段 2026-11-07T20:00 校验 M04 的审核规则与授权有效期 | check_rules |
| 4 | 2 | `check_rules` | {"material_id": "M06", "publish_at": "2026-11-07T12:00"} | ✅ M06 审核 review：R07[review] 出镜人物肖像授权未回传 | 按请求时段 2026-11-07T12:00 校验 M06 的审核规则与授权有效期 | query_slots |
| 5 | 3 | `query_slots` | {"channel": "xiaohongshu", "publish_at": "2026-11-07T12:00"} | ✅ xiaohongshu 2026-11-07T12:00 free | M06 审核为 review 可排期，需确认小红书 2026-11-07T12:00 是否可用 | save_schedule_draft |
| 6 | 4 | `save_schedule_draft` | {"items": [{"material_id": "M06", "channel": "xiaohongshu", "slot": "2026-11-07T12:00", "confirmation_status": "pending", "note": "审核为 review：出镜人物肖像授权未回传，需人工复核通过后方可发布；时段与用户要求一致"}]} | ✅ 草稿 D-DD1748B1 created（修订 1，1 条，未发布） | M06 审核为 review 且小红书 12:00 时段空闲，按用户要求时段保存为待复核草稿；M04 被阻断不纳入 | finish |
| 7 | 5 | `finish` | {"items": [{"material_id": "M04", "review_status": "blocked", "risk_reasons": ["R04 阻断：文案含广告法禁用极限用语（最有效、全网最、100%）", "R05 需复核：疑似功效/医疗宣称（祛痘、根治）", "R06 需复核：商业合作内容未标注“广告”"], "suggested_channel": null, "suggested_slot": null, "confirmation_status": "not_applicable", "pending_items": ["需修改文案去除极限用语与功效/医疗宣称，并补充广告标识后重新送审"], "in_draft": false}, {"material_id": "M06", "review_status": "review", "risk_reasons": ["R07 需复核：出镜人物肖像授权未回传"], "suggested_channel": "xiaohongshu", "suggested_slot": "2026-11-07T12:00", "confirmation_status": "pending", "pending_items": ["补交出镜人物肖像授权并完成人工复核", "复核通过前不得发布"], "in_draft": true}], "summary": "M04 因广告法极限用语被阻断，未纳入草稿，需修改文案并补广告标识后重审；M06 为 review（肖像授权未回传），已按用户要求的小红书 2026-11-07 12:00 保存为排期草稿（D-DD1748B1，仅草稿未发布），待人工复核确认。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M04 | blocked | ["R04 阻断：文案含广告法禁用极限用语（最有效、全网最、100%）", "R05 需复核：疑似功效/医疗宣称（祛痘、根治）", "R06 需复核：商业合作内容未标注“广告”"] | ["R04[block] caption", "R05[review] caption", "R06[review] ad_label"] | douyin 2026-11-07T20:00 | — | not_applicable | ["需修改文案去除极限用语与功效/医疗宣称，并补充广告标识后重新送审"] | not_saved |
| M06 | review | ["R07 需复核：出镜人物肖像授权未回传"] | ["R07[review] portrait_release"] | xiaohongshu 2026-11-07T12:00 | xiaohongshu 2026-11-07T12:00 | pending | ["补交出镜人物肖像授权并完成人工复核", "复核通过前不得发布"] | saved |

**模型总结**：M04 因广告法极限用语被阻断，未纳入草稿，需修改文案并补广告标识后重审；M06 为 review（肖像授权未回传），已按用户要求的小红书 2026-11-07 12:00 保存为排期草稿（D-DD1748B1，仅草稿未发布），待人工复核确认。
