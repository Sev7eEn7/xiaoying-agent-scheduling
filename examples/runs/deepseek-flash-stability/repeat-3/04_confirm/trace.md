# 04_confirm · 用户确认后再次提交

- 输入：`examples/inputs/04_confirm.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/04_confirm.json --provider deepseek --store .runtime/chainA.json`
- 模型：`deepseek-flash`；模型轮次 5/15；工具调用 7/40；finish 被退回 0 次
- 任务状态：**completed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "updated", "draft_id": "D-763DEB3C", "revision": 2, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M01"} | ✅ 找到 M01《磁吸手机壳开箱》，license=有 | 需要先读取 M01 的元数据以确认渠道、授权等信息再安排排期。 | check_rules |
| 2 | 1 | `check_rules` | {"material_id": "M01", "publish_at": "2026-11-03T18:00"} | ✅ M01 审核 pass | 按请求的原始时段 2026-11-03T18:00 先做审核规则检查，确认是否存在授权或内容风险。 | query_slots |
| 3 | 2 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-03T18:00"} | ✅ douyin 2026-11-03T18:00 occupied（已被排期 S-1001（M90 品牌直播预告）占用）；备选 19:00、16:00、21:00、15:00 | M01 审核已通过，需确认用户要求的 18:00 在抖音渠道是否可用。 | query_slots |
| 4 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-03T19:00"} | ✅ douyin 2026-11-03T19:00 free | 18:00 已被 S-1001 占用，请求中运营已批准改到 19:00，需确认 19:00 是否空闲。 | check_rules |
| 5 | 3 | `check_rules` | {"material_id": "M01", "publish_at": "2026-11-03T19:00"} | ✅ M01 审核 pass | 因 18:00 被占用、改用已获批准的 19:00，需按新时段复核审核规则与授权有效期。 | save_schedule_draft |
| 6 | 4 | `save_schedule_draft` | {"items": [{"material_id": "M01", "channel": "douyin", "slot": "2026-11-03T19:00", "confirmation_status": "confirmed", "note": "原要求 18:00 已被 S-1001（M90 品牌直播预告）占用，改用运营在 confirmations 中已批准的 19:00"}]} | ✅ 草稿 D-763DEB3C updated（修订 2，1 条，未发布） | M01 在 19:00 审核通过且时段空闲，并已获运营批准，故按该时段保存为草稿（不发布）。 | finish |
| 7 | 5 | `finish` | {"items": [{"material_id": "M01", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-03T19:00", "confirmation_status": "confirmed", "pending_items": [], "in_draft": true}], "summary": "M01《磁吸手机壳开箱》审核通过（check_rules pass：原创版权、音乐授权至 2027-12-31、无真人出镜、非商业投放、无广告标注问题）。原要求 2026-11-03T18:00 抖音时段已被排期 S-1001（M90 品牌直播预告）占用，改用请求 confirmations 中运营已批准的 19:00（该时段空闲，且按新时段复核仍为 pass），确认状态为 confirmed。已保存为排期草稿 D-763DEB3C（修订 2，状态 draft），未发布上线。若后续仍需坚持 18:00，请先与 S-1001 的排期方协调释放时段并重新确认。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M01 | pass | — | — | douyin 2026-11-03T18:00 | douyin 2026-11-03T19:00 | confirmed | — | saved |

**模型总结**：M01《磁吸手机壳开箱》审核通过（check_rules pass：原创版权、音乐授权至 2027-12-31、无真人出镜、非商业投放、无广告标注问题）。原要求 2026-11-03T18:00 抖音时段已被排期 S-1001（M90 品牌直播预告）占用，改用请求 confirmations 中运营已批准的 19:00（该时段空闲，且按新时段复核仍为 pass），确认状态为 confirmed。已保存为排期草稿 D-763DEB3C（修订 2，状态 draft），未发布上线。若后续仍需坚持 18:00，请先与 S-1001 的排期方协调释放时段并重新确认。
