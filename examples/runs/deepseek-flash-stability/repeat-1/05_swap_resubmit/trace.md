# 05_swap_resubmit · 更换占用时段后重复提交

- 输入：`examples/inputs/02_conflict.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/02_conflict.json --provider deepseek --store .runtime/chainA.json --schedule data/schedule_variant.json`
- 模型：`deepseek-flash`；模型轮次 5/15；工具调用 5/40；finish 被退回 0 次
- 任务状态：**completed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "updated", "draft_id": "D-763DEB3C", "revision": 3, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M01"} | ✅ 找到 M01《磁吸手机壳开箱》，license=有 | 请求中唯一的素材，先读取元数据以确定审核与排期依据。 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M01", "publish_at": "2026-11-03T18:00"} | ✅ M01 审核 pass | 素材为原创、有音乐授权，需按规则校验抖音 2026-11-03 18:00 发布的合规性。 | query_slots |
| 3 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-03T18:00"} | ✅ douyin 2026-11-03T18:00 free | 审核已通过，现需确认抖音 2026-11-03 18:00 是否可排期。 | save_schedule_draft |
| 4 | 4 | `save_schedule_draft` | {"items": [{"material_id": "M01", "channel": "douyin", "slot": "2026-11-03T18:00", "confirmation_status": "not_required"}]} | ✅ 草稿 D-763DEB3C updated（修订 3，1 条，未发布） | M01 规则检查 pass 且抖音该时段空闲，按用户硬性要求原时段保存为草稿。 | finish |
| 5 | 5 | `finish` | {"items": [{"material_id": "M01", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-03T18:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}], "summary": "M01《磁吸手机壳开箱》审核通过：原创素材、音乐授权有效期至 2027-12-31、无真人出镜、非商业推广也未需广告标识；抖音 2026-11-03 18:00 时段查询为空闲，已按请求的渠道与时段保存为排期草稿（D-763DEB3C，草稿状态，未发布）。无待确认项。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M01 | pass | — | — | douyin 2026-11-03T18:00 | douyin 2026-11-03T18:00 | not_required | — | saved |

**模型总结**：M01《磁吸手机壳开箱》审核通过：原创素材、音乐授权有效期至 2027-12-31、无真人出镜、非商业推广也未需广告标识；抖音 2026-11-03 18:00 时段查询为空闲，已按请求的渠道与时段保存为排期草稿（D-763DEB3C，草稿状态，未发布）。无待确认项。
