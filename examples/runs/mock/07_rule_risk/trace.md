# 07_rule_risk · 规则风险：阻断与人工复核

- 输入：`examples/inputs/07_rule_risk.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/07_rule_risk.json --provider mock --store .runtime/s07.json`
- 模型：`mock-rule-policy`；模型轮次 7/15；工具调用 7/40；finish 被退回 0 次
- 任务状态：**needs_confirmation**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-DD1748B1", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M04"} | ✅ 找到 M04《祛痘精华推广》，license=有 | 先读取素材元数据 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M04", "publish_at": "2026-11-07T20:00"} | ✅ M04 审核 block：R04[block] 包含广告法禁用的极限用语（最有效、全网最、100%）；R05[review] 疑似功效/医疗宣称，需法务复核（祛痘、根治）；R06[review] 商业合作内容未标注“广告” | 读取成功，按发布时间做规则检查 | get_material |
| 3 | 3 | `get_material` | {"material_id": "M06"} | ✅ 找到 M06《双11预热海报》，license=有 | 先读取素材元数据 | check_rules |
| 4 | 4 | `check_rules` | {"material_id": "M06", "publish_at": "2026-11-07T12:00"} | ✅ M06 审核 review：R07[review] 出镜人物肖像授权未回传 | 读取成功，按发布时间做规则检查 | query_slots |
| 5 | 5 | `query_slots` | {"channel": "xiaohongshu", "publish_at": "2026-11-07T12:00", "also_taken": []} | ✅ xiaohongshu 2026-11-07T12:00 free | 审核可排期，查询目标时段 | save_schedule_draft |
| 6 | 6 | `save_schedule_draft` | {"items": [{"material_id": "M06", "channel": "xiaohongshu", "slot": "2026-11-07T12:00", "confirmation_status": "pending", "note": "需人工复核：出镜人物肖像授权未回传"}]} | ✅ 草稿 D-DD1748B1 created（修订 1，1 条，未发布） | 所有素材处理完毕，保存可排期条目为草稿 | finish |
| 7 | 7 | `finish` | {"items": [{"material_id": "M04", "review_status": "blocked", "risk_reasons": ["包含广告法禁用的极限用语", "疑似功效/医疗宣称，需法务复核", "商业合作内容未标注“广告”"], "suggested_channel": null, "suggested_slot": null, "confirmation_status": "not_applicable", "pending_items": [], "in_draft": false}, {"material_id": "M06", "review_status": "review", "risk_reasons": ["出镜人物肖像授权未回传"], "suggested_channel": "xiaohongshu", "suggested_slot": "2026-11-07T12:00", "confirmation_status": "pending", "pending_items": ["需人工复核：出镜人物肖像授权未回传"], "in_draft": true}], "summary": "共 2 个素材，1 个已保存为草稿；未发布任何内容。"} | ✅ finish 通过工具记录核对 | 全部素材已处理 | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M04 | blocked | ["包含广告法禁用的极限用语", "疑似功效/医疗宣称，需法务复核", "商业合作内容未标注“广告”"] | ["R04[block] caption", "R05[review] caption", "R06[review] ad_label"] | douyin 2026-11-07T20:00 | — | not_applicable | — | not_saved |
| M06 | review | ["出镜人物肖像授权未回传"] | ["R07[review] portrait_release"] | xiaohongshu 2026-11-07T12:00 | xiaohongshu 2026-11-07T12:00 | pending | ["需人工复核：出镜人物肖像授权未回传"] | saved |

**模型总结**：共 2 个素材，1 个已保存为草稿；未发布任何内容。
