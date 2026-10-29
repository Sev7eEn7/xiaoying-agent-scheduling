# 07_rule_risk · 规则风险：阻断与人工复核

- 输入：`examples/inputs/07_rule_risk.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/07_rule_risk.json --provider deepseek --store .runtime/s07.json`
- 模型：`deepseek-flash`；模型轮次 5/15；工具调用 7/40；finish 被退回 0 次
- 任务状态：**needs_confirmation**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-DD1748B1", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M04"} | ✅ 找到 M04《祛痘精华推广》，license=有 | 请求排期 M04 到抖音 2026-11-07 20:00，先读取素材元数据以了解其属性与授权信息。 | get_material |
| 2 | 1 | `get_material` | {"material_id": "M06"} | ✅ 找到 M06《双11预热海报》，license=有 | 请求排期 M06 到小红书 2026-11-07 12:00，先读取素材元数据以了解其属性与授权信息。 | check_rules |
| 3 | 2 | `check_rules` | {"material_id": "M04", "publish_at": "2026-11-07T20:00"} | ✅ M04 审核 block：R04[block] 包含广告法禁用的极限用语（最有效、全网最、100%）；R05[review] 疑似功效/医疗宣称，需法务复核（祛痘、根治）；R06[review] 商业合作内容未标注“广告” | M04 元数据已取得，按其请求时段 2026-11-07 20:00 执行审核规则检查（含授权有效期校验）。 | check_rules |
| 4 | 2 | `check_rules` | {"material_id": "M06", "publish_at": "2026-11-07T12:00"} | ✅ M06 审核 review：R07[review] 出镜人物肖像授权未回传 | M06 元数据已取得，按其请求时段 2026-11-07 12:00 执行审核规则检查（含授权有效期校验）。 | query_slots |
| 5 | 3 | `query_slots` | {"channel": "xiaohongshu", "publish_at": "2026-11-07T12:00"} | ✅ xiaohongshu 2026-11-07T12:00 free | M06 审核为 review 可进入草稿，需确认其请求的小红书 2026-11-07 12:00 时段是否可用；M04 已被阻断不占用任何时段。 | save_schedule_draft |
| 6 | 4 | `save_schedule_draft` | {"items": [{"material_id": "M06", "channel": "xiaohongshu", "slot": "2026-11-07T12:00", "confirmation_status": "pending", "note": "审核结论为 review（R07：出镜人物肖像授权未回传），需人工复核并补齐肖像授权；时段与用户要求一致，无需改期"}]} | ✅ 草稿 D-DD1748B1 created（修订 1，1 条，未发布） | M06 审核为 review 且其请求的小红书 2026-11-07 12:00 时段空闲，按原时段放入草稿并置为 pending；M04 被 block 不写入草稿。 | finish |
| 7 | 5 | `finish` | {"items": [{"material_id": "M04", "review_status": "blocked", "risk_reasons": ["R04 阻断：文案含广告法禁用极限用语（“最有效”“全网最”“100%”）", "R05 复核：疑似功效/医疗宣称（“祛痘”“根治”）需法务复核", "R06 复核：商业合作内容未标注“广告”"], "suggested_channel": "douyin", "suggested_slot": null, "confirmation_status": "not_applicable", "pending_items": ["需重写文案，删除“最有效”“全网最”“100%”“根治”等极限与功效宣称", "补充“广告”标识后重新提审", "重新审核通过前无法给出时段"], "in_draft": false}, {"material_id": "M06", "review_status": "review", "risk_reasons": ["R07 需复核：出镜人物肖像授权未回传（portrait_release=false 但含真人出镜）"], "suggested_channel": "xiaohongshu", "suggested_slot": "2026-11-07T12:00", "confirmation_status": "pending", "pending_items": ["等待人工（法务/合规）复核肖像授权风险", "补交出镜人物肖像授权书"], "in_draft": true}], "summary": "本批次 2 个素材：M04（祛痘精华，抖音）审核为 block（R04 极限用语阻断，另有功效宣称与未标“广告”两项复核项），不进入草稿，需重写文案并加广告标识后重新提审，故未给出时段。M06（双11预热海报，小红书）审核为 review，仅肖像授权未回传，请求的小红书 2026-11-07 12:00 时段查询为空闲，已按原时段写入排期草稿（draft_id D-DD1748B1，revision 1），确认状态 pending，等人工复核并补齐肖像授权。草稿仅为草稿状态，未发布、未上线。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M04 | blocked | ["R04 阻断：文案含广告法禁用极限用语（“最有效”“全网最”“100%”）", "R05 复核：疑似功效/医疗宣称（“祛痘”“根治”）需法务复核", "R06 复核：商业合作内容未标注“广告”"] | ["R04[block] caption", "R05[review] caption", "R06[review] ad_label"] | douyin 2026-11-07T20:00 | douyin | not_applicable | ["需重写文案，删除“最有效”“全网最”“100%”“根治”等极限与功效宣称", "补充“广告”标识后重新提审", "重新审核通过前无法给出时段"] | not_saved |
| M06 | review | ["R07 需复核：出镜人物肖像授权未回传（portrait_release=false 但含真人出镜）"] | ["R07[review] portrait_release"] | xiaohongshu 2026-11-07T12:00 | xiaohongshu 2026-11-07T12:00 | pending | ["等待人工（法务/合规）复核肖像授权风险", "补交出镜人物肖像授权书"] | saved |

**模型总结**：本批次 2 个素材：M04（祛痘精华，抖音）审核为 block（R04 极限用语阻断，另有功效宣称与未标“广告”两项复核项），不进入草稿，需重写文案并加广告标识后重新提审，故未给出时段。M06（双11预热海报，小红书）审核为 review，仅肖像授权未回传，请求的小红书 2026-11-07 12:00 时段查询为空闲，已按原时段写入排期草稿（draft_id D-DD1748B1，revision 1），确认状态 pending，等人工复核并补齐肖像授权。草稿仅为草稿状态，未发布、未上线。
