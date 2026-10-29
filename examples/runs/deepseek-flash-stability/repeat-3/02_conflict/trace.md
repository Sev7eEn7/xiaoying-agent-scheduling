# 02_conflict · 时段冲突（参考实例）

- 输入：`examples/inputs/02_conflict.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/02_conflict.json --provider deepseek --store .runtime/chainA.json`
- 模型：`deepseek-flash`；模型轮次 5/15；工具调用 7/40；finish 被退回 0 次
- 任务状态：**needs_confirmation**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-763DEB3C", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M01"} | ✅ 找到 M01《磁吸手机壳开箱》，license=有 | 请求中唯一素材，需先读取元数据以确定审核与排期所需信息。 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M01", "publish_at": "2026-11-03T18:00"} | ✅ M01 审核 pass | 按用户要求的抖音 2026-11-03T18:00 校验授权有效期与内容合规。 | query_slots |
| 3 | 2 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-03T18:00"} | ✅ douyin 2026-11-03T18:00 occupied（已被排期 S-1001（M90 品牌直播预告）占用）；备选 19:00、16:00、21:00、15:00 | 确认用户指定时段在抖音渠道是否可用（本批次仅一个素材，无 also_taken）。 | query_slots |
| 4 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-03T19:00"} | ✅ douyin 2026-11-03T19:00 free | 原 18:00 已被 S-1001 占用，按不早于原要求选最近备选 19:00，确认其确实空闲。 | check_rules |
| 5 | 3 | `check_rules` | {"material_id": "M01", "publish_at": "2026-11-03T19:00"} | ✅ M01 审核 pass | 时段从 18:00 调整到同日 19:00，复核该时段下授权有效期与合规结论仍成立。 | save_schedule_draft |
| 6 | 4 | `save_schedule_draft` | {"items": [{"material_id": "M01", "channel": "douyin", "slot": "2026-11-03T19:00", "confirmation_status": "pending", "note": "用户原要求 2026-11-03T18:00 已被排期 S-1001（M90 品牌直播预告）占用；建议顺延至同日 19:00（抖音渠道此刻空闲），需用户确认是否接受该时段调整。"}]} | ✅ 草稿 D-763DEB3C created（修订 1，1 条，未发布） | M01 审核 pass、抖音 19:00 空闲，原 18:00 冲突故以 pending 形式保存草稿待确认。 | finish |
| 7 | 5 | `finish` | {"items": [{"material_id": "M01", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-03T19:00", "confirmation_status": "pending", "pending_items": ["确认抖音发布时段由原要求的 2026-11-03T18:00 顺延至同日 19:00（18:00 已被 S-1001 M90 品牌直播预告占用；19:00 为不早于原要求的最近空闲时段）"], "in_draft": true}], "summary": "M01（磁吸手机壳开箱）按规则检查通过（pass，无 findings），已保存为排期草稿 D-763DEB3C（仅草稿，未发布）。唯一问题是原定时段抖音 2026-11-03T18:00 已被 S-1001（M90 品牌直播预告）占用，故建议顺延至同日 19:00，因超出用户硬性要求且素材无可用窗口、请求中也无确认，该时段标记为 pending，需用户确认后再定稿。若用户坚持 18:00，需另行协调 S-1001。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M01 | pass | — | — | douyin 2026-11-03T18:00 | douyin 2026-11-03T19:00 | pending | ["确认抖音发布时段由原要求的 2026-11-03T18:00 顺延至同日 19:00（18:00 已被 S-1001 M90 品牌直播预告占用；19:00 为不早于原要求的最近空闲时段）"] | saved |

**模型总结**：M01（磁吸手机壳开箱）按规则检查通过（pass，无 findings），已保存为排期草稿 D-763DEB3C（仅草稿，未发布）。唯一问题是原定时段抖音 2026-11-03T18:00 已被 S-1001（M90 品牌直播预告）占用，故建议顺延至同日 19:00，因超出用户硬性要求且素材无可用窗口、请求中也无确认，该时段标记为 pending，需用户确认后再定稿。若用户坚持 18:00，需另行协调 S-1001。
