# 07_rule_risk · 规则风险：阻断与人工复核

- 输入：`examples/inputs/07_rule_risk.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/07_rule_risk.json --provider deepseek --store .runtime/s07.json`
- 模型：`deepseek-flash`；模型轮次 5/15；工具调用 7/40；finish 被退回 0 次
- 任务状态：**needs_confirmation**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-DD1748B1", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M04"} | ✅ 找到 M04《祛痘精华推广》，license=有 | 需要先读取 M04 元数据以判断审核与排期条件 | get_material |
| 2 | 1 | `get_material` | {"material_id": "M06"} | ✅ 找到 M06《双11预热海报》，license=有 | 需要先读取 M06 元数据以判断审核与排期条件 | check_rules |
| 3 | 2 | `check_rules` | {"material_id": "M04", "publish_at": "2026-11-07T20:00"} | ✅ M04 审核 block：R04[block] 包含广告法禁用的极限用语（最有效、全网最、100%）；R05[review] 疑似功效/医疗宣称，需法务复核（祛痘、根治）；R06[review] 商业合作内容未标注“广告” | 基于 M04 元数据（功效类文案+商业推广未标广告）按其请求时段校验审核结果 | check_rules |
| 4 | 2 | `check_rules` | {"material_id": "M06", "publish_at": "2026-11-07T12:00"} | ✅ M06 审核 review：R07[review] 出镜人物肖像授权未回传 | 基于 M06 元数据（含人物但无肖像授权）按其请求时段校验审核结果 | query_slots |
| 5 | 3 | `query_slots` | {"channel": "xiaohongshu", "publish_at": "2026-11-07T12:00"} | ✅ xiaohongshu 2026-11-07T12:00 free | M06 审核为 review 可排期，按用户指定的 11-07 12:00 查小红书时段是否可用 | save_schedule_draft |
| 6 | 4 | `save_schedule_draft` | {"items": [{"material_id": "M06", "channel": "xiaohongshu", "slot": "2026-11-07T12:00", "confirmation_status": "pending", "note": "审核结果为 review：R07 出镜人物肖像授权未回传，需人工复核并补齐肖像授权；时段与用户要求一致，未改动"}]} | ✅ 草稿 D-DD1748B1 created（修订 1，1 条，未发布） | M06 审核为 review 且指定时段空闲，按要求时段放入草稿并标记待确认；M04 因 block 不纳入 | finish |
| 7 | 5 | `finish` | {"items": [{"material_id": "M04", "review_status": "blocked", "risk_reasons": ["R04(block)：文案含广告法禁用极限用语“最有效/全网最/100%”", "R05(review)：文案“祛痘、根治”疑似功效/医疗宣称，需法务复核", "R06(review)：商业合作内容未标注“广告”"], "suggested_channel": "douyin", "suggested_slot": null, "confirmation_status": "not_applicable", "pending_items": ["需重写文案，删除“最有效/全网最/100%/根治”等极限与医疗宣称用语", "修改后需重新提交审核（含法务复核功效宣称）", "商业合作需补标“广告”标识", "审核通过前无可用建议时段，暂不可排期"], "in_draft": false}, {"material_id": "M06", "review_status": "review", "risk_reasons": ["R07(review)：出镜人物肖像授权未回传"], "suggested_channel": "xiaohongshu", "suggested_slot": "2026-11-07T12:00", "confirmation_status": "pending", "pending_items": ["补齐出镜人物肖像授权回传并完成人工复核（R07）", "草稿已按用户要求时段 2026-11-07T12:00 占位，复核通过后方可推进"], "in_draft": true}], "summary": "本批 2 个素材：M04（抖音 11-07 20:00）审核结论为 block——文案含广告法禁用极限用语（最有效/全网最/100%），另有功效医疗宣称与未标“广告”两项需复核问题，已阻断、未纳入草稿，需改写文案并重新送审后再排期。M06（小红书 11-07 12:00）结论为 review，仅肖像授权未回传一项问题，指定时段空闲且与用户要求一致，已连同待确认说明保存为排期草稿 D-DD1748B1（修订 1，仅草稿，未发布），需补齐肖像授权并完成人工复核。M06 时段未做任何改动，无争用冲突。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M04 | blocked | ["R04(block)：文案含广告法禁用极限用语“最有效/全网最/100%”", "R05(review)：文案“祛痘、根治”疑似功效/医疗宣称，需法务复核", "R06(review)：商业合作内容未标注“广告”"] | ["R04[block] caption", "R05[review] caption", "R06[review] ad_label"] | douyin 2026-11-07T20:00 | douyin | not_applicable | ["需重写文案，删除“最有效/全网最/100%/根治”等极限与医疗宣称用语", "修改后需重新提交审核（含法务复核功效宣称）", "商业合作需补标“广告”标识", "审核通过前无可用建议时段，暂不可排期"] | not_saved |
| M06 | review | ["R07(review)：出镜人物肖像授权未回传"] | ["R07[review] portrait_release"] | xiaohongshu 2026-11-07T12:00 | xiaohongshu 2026-11-07T12:00 | pending | ["补齐出镜人物肖像授权回传并完成人工复核（R07）", "草稿已按用户要求时段 2026-11-07T12:00 占位，复核通过后方可推进"] | saved |

**模型总结**：本批 2 个素材：M04（抖音 11-07 20:00）审核结论为 block——文案含广告法禁用极限用语（最有效/全网最/100%），另有功效医疗宣称与未标“广告”两项需复核问题，已阻断、未纳入草稿，需改写文案并重新送审后再排期。M06（小红书 11-07 12:00）结论为 review，仅肖像授权未回传一项问题，指定时段空闲且与用户要求一致，已连同待确认说明保存为排期草稿 D-DD1748B1（修订 1，仅草稿，未发布），需补齐肖像授权并完成人工复核。M06 时段未做任何改动，无争用冲突。
