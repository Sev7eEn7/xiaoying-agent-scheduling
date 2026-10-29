# 02_conflict · 时段冲突（参考实例）

- 输入：`examples/inputs/02_conflict.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/02_conflict.json --provider deepseek --store .runtime/chainA.json`
- 模型：`deepseek-flash`；模型轮次 6/15；工具调用 6/40；finish 被退回 0 次
- 任务状态：**needs_confirmation**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-763DEB3C", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M01"} | ✅ 找到 M01《磁吸手机壳开箱》，license=有 | 请求中唯一的素材，先读取元数据以了解版权与授权信息。 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M01", "publish_at": "2026-11-03T18:00"} | ✅ M01 审核 pass | 元数据齐全，按用户要求的 2026-11-03T18:00 校验授权有效期与内容规则。 | query_slots |
| 3 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-03T18:00"} | ✅ douyin 2026-11-03T18:00 occupied（已被排期 S-1001（M90 品牌直播预告）占用）；备选 19:00、16:00、21:00、15:00 | 审核通过，需确认用户要求的抖音 2026-11-03T18:00 是否空闲（本批次仅一个素材）。 | query_slots |
| 4 | 4 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-03T19:00"} | ✅ douyin 2026-11-03T19:00 free | 原时段被 S-1001 占用，按规则选择不早于原要求的最近空闲备选 19:00 并复核可用性。 | save_schedule_draft |
| 5 | 5 | `save_schedule_draft` | {"items": [{"material_id": "M01", "channel": "douyin", "slot": "2026-11-03T19:00", "confirmation_status": "pending", "note": "用户要求的 2026-11-03T18:00 已被既有排期 S-1001（M90 品牌直播预告）占用，建议顺延至同日 19:00，需用户确认"}]} | ✅ 草稿 D-763DEB3C created（修订 1，1 条，未发布） | M01 审核通过，18:00 被占用且无可用窗口，故以最近空闲时段 19:00 作为待确认建议保存草稿。 | finish |
| 6 | 6 | `finish` | {"items": [{"material_id": "M01", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-03T19:00", "confirmation_status": "pending", "pending_items": ["抖音 2026-11-03T18:00 已被排期 S-1001（M90 品牌直播预告）占用，需确认是否接受顺延至同日 19:00"], "in_draft": true}], "summary": "M01《磁吸手机壳开箱》规则检查通过（原创、音乐授权至 2027-12-31、无人物肖像、非商业推广），无内容合规风险。用户要求的抖音 2026-11-03T18:00 已被 S-1001 占用，已按“不早于原要求的最近空闲时段”建议改为同日 19:00，并以 pending 状态存入排期草稿 D-763DEB3C（仅草稿，未发布）。请用户确认时段顺延；若坚持 18:00 需先协调 S-1001。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M01 | pass | — | — | douyin 2026-11-03T18:00 | douyin 2026-11-03T19:00 | pending | ["抖音 2026-11-03T18:00 已被排期 S-1001（M90 品牌直播预告）占用，需确认是否接受顺延至同日 19:00"] | saved |

**模型总结**：M01《磁吸手机壳开箱》规则检查通过（原创、音乐授权至 2027-12-31、无人物肖像、非商业推广），无内容合规风险。用户要求的抖音 2026-11-03T18:00 已被 S-1001 占用，已按“不早于原要求的最近空闲时段”建议改为同日 19:00，并以 pending 状态存入排期草稿 D-763DEB3C（仅草稿，未发布）。请用户确认时段顺延；若坚持 18:00 需先协调 S-1001。
