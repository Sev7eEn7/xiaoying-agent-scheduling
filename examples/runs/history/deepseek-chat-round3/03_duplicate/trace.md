# 03_duplicate · 重复提交同一请求

- 输入：`examples/inputs/02_conflict.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/02_conflict.json --provider deepseek --store .runtime/chainA.json`
- 模型：`deepseek-chat`；模型轮次 6/15；工具调用 6/40；finish 被退回 0 次
- 任务状态：**needs_confirmation**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "duplicate", "draft_id": "D-763DEB3C", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M01"} | ✅ 找到 M01《磁吸手机壳开箱》，license=有 | 请求要求为 M01 排期，先读取素材元数据以确认基本信息。 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M01", "publish_at": "2026-11-03T18:00"} | ✅ M01 审核 pass | 元数据完整（原创、音乐授权至 2027-12-31），按请求时段 2026-11-03T18:00 执行审核规则检查。 | query_slots |
| 3 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-03T18:00"} | ✅ douyin 2026-11-03T18:00 occupied（已被排期 S-1001（M90 品牌直播预告）占用）；备选 19:00、16:00、21:00、15:00 | M01 审核结果为 pass，需确认抖音 2026-11-03T18:00 是否空闲以决定能否按用户要求排期。 | check_rules |
| 4 | 4 | `check_rules` | {"material_id": "M01", "publish_at": "2026-11-03T19:00"} | ✅ M01 审核 pass | 原时段 18:00 已被 S-1001 占用，改用最近空闲时段 19:00，需按新时段重新校验授权有效期。 | save_schedule_draft |
| 5 | 5 | `save_schedule_draft` | {"items": [{"material_id": "M01", "channel": "douyin", "slot": "2026-11-03T19:00", "confirmation_status": "pending", "note": "用户要求 2026-11-03T18:00，该时段已被 S-1001（M90 品牌直播预告）占用，建议顺延至最近空闲时段 19:00，待用户确认"}]} | ✅ 草稿 D-763DEB3C duplicate（修订 1，1 条，未发布） | M01 审核 pass，原时段被占用，按最近空闲时段 19:00 保存为草稿并标记待确认。 | finish |
| 6 | 6 | `finish` | {"items": [{"material_id": "M01", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-03T19:00", "confirmation_status": "pending", "pending_items": ["原要求 2026-11-03T18:00 已被排期 S-1001（M90 品牌直播预告）占用，是否同意顺延至 2026-11-03T19:00"], "in_draft": true}], "summary": "M01（磁吸手机壳开箱）审核通过，无风险项。用户要求的抖音 2026-11-03T18:00 已被 S-1001 占用，已按最近空闲时段 19:00 保存为排期草稿（D-763DEB3C，仅草稿未发布），时段变更待用户确认。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M01 | pass | — | — | douyin 2026-11-03T18:00 | douyin 2026-11-03T19:00 | pending | ["原要求 2026-11-03T18:00 已被排期 S-1001（M90 品牌直播预告）占用，是否同意顺延至 2026-11-03T19:00"] | saved |

**模型总结**：M01（磁吸手机壳开箱）审核通过，无风险项。用户要求的抖音 2026-11-03T18:00 已被 S-1001 占用，已按最近空闲时段 19:00 保存为排期草稿（D-763DEB3C，仅草稿未发布），时段变更待用户确认。
