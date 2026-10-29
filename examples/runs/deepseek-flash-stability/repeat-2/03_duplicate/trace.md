# 03_duplicate · 重复提交同一请求

- 输入：`examples/inputs/02_conflict.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/02_conflict.json --provider deepseek --store .runtime/chainA.json`
- 模型：`deepseek-flash`；模型轮次 5/15；工具调用 7/40；finish 被退回 0 次
- 任务状态：**needs_confirmation**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "duplicate", "draft_id": "D-763DEB3C", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M01"} | ✅ 找到 M01《磁吸手机壳开箱》，license=有 | 请求中唯一的素材，先读取其元数据以确认类型与授权信息。 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M01", "publish_at": "2026-11-03T18:00"} | ✅ M01 审核 pass | 按用户要求的 2026-11-03T18:00 时段校验授权有效期与审核规则。 | query_slots |
| 3 | 2 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-03T18:00"} | ✅ douyin 2026-11-03T18:00 occupied（已被排期 S-1001（M90 品牌直播预告）占用）；备选 19:00、16:00、21:00、15:00 | 确认用户硬性要求的抖音 2026-11-03T18:00 时段是否可用。 | query_slots |
| 4 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-03T19:00"} | ✅ douyin 2026-11-03T19:00 free | 原时段被占，按规则6 选取不早于原要求的最近备选 19:00 并确认其确实空闲。 | check_rules |
| 5 | 3 | `check_rules` | {"material_id": "M01", "publish_at": "2026-11-03T19:00"} | ✅ M01 审核 pass | 时段调整到 19:00 后复查授权有效期与规则，确保结论对应最终建议时段。 | save_schedule_draft |
| 6 | 4 | `save_schedule_draft` | {"items": [{"material_id": "M01", "channel": "douyin", "slot": "2026-11-03T19:00", "confirmation_status": "pending", "note": "原要求 2026-11-03T18:00 已被排期 S-1001（M90 品牌直播预告）占用，建议顺延至最近空闲的 19:00；请求未提供 acceptable_window 或对该时段的确认，需用户确认是否接受 19:00"}]} | ✅ 草稿 D-763DEB3C duplicate（修订 1，1 条，未发布） | M01 审核 pass 且 19:00 空闲，因时段需改动用户硬性要求，以 pending 保存排期草稿（仅草稿，未发布）。 | finish |
| 7 | 5 | `finish` | {"items": [{"material_id": "M01", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-03T19:00", "confirmation_status": "pending", "pending_items": ["用户要求 2026-11-03T18:00 已被排期 S-1001（M90 品牌直播预告）占用，请确认是否接受改至 2026-11-03T19:00（最近空闲且不早于原要求）"], "in_draft": true}], "summary": "M01《磁吸手机壳开箱》审核通过（原创素材、音乐授权至 2027-12-31、无真人出镜、非商业投放，findings 为空）。唯一问题：用户指定的抖音 2026-11-03T18:00 已被 S-1001 占用，按“不早于原要求的最近空闲时段”建议 19:00，该时段空闲且复查仍为 pass。因请求未提供 acceptable_window 或确认，草稿中该条为 pending 待确认。已合并保存为排期草稿 D-763DEB3C（重复保存返回 duplicate，未产生第二份草稿），仅为草稿，未发布、未上线。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M01 | pass | — | — | douyin 2026-11-03T18:00 | douyin 2026-11-03T19:00 | pending | ["用户要求 2026-11-03T18:00 已被排期 S-1001（M90 品牌直播预告）占用，请确认是否接受改至 2026-11-03T19:00（最近空闲且不早于原要求）"] | saved |

**模型总结**：M01《磁吸手机壳开箱》审核通过（原创素材、音乐授权至 2027-12-31、无真人出镜、非商业投放，findings 为空）。唯一问题：用户指定的抖音 2026-11-03T18:00 已被 S-1001 占用，按“不早于原要求的最近空闲时段”建议 19:00，该时段空闲且复查仍为 pass。因请求未提供 acceptable_window 或确认，草稿中该条为 pending 待确认。已合并保存为排期草稿 D-763DEB3C（重复保存返回 duplicate，未产生第二份草稿），仅为草稿，未发布、未上线。
