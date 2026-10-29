# 03_duplicate · 重复提交同一请求

- 输入：`examples/inputs/02_conflict.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/02_conflict.json --provider deepseek --store .runtime/chainA.json`
- 模型：`deepseek-flash`；模型轮次 6/15；工具调用 6/40；finish 被退回 0 次
- 任务状态：**needs_confirmation**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "duplicate", "draft_id": "D-763DEB3C", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M01"} | ✅ 找到 M01《磁吸手机壳开箱》，license=有 | 请求只包含 M01，先读取其元数据以便后续按规则审核。 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M01", "publish_at": "2026-11-03T18:00"} | ✅ M01 审核 pass | 元数据显示为原创且音乐授权有效期覆盖 2026-11-03，需按规则确认该时段是否可发。 | query_slots |
| 3 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-03T18:00"} | ✅ douyin 2026-11-03T18:00 occupied（已被排期 S-1001（M90 品牌直播预告）占用）；备选 19:00、16:00、21:00、15:00 | 审核已 pass，需确认抖音 2026-11-03T18:00 是否空闲才能排入草稿。 | query_slots |
| 4 | 4 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-03T19:00"} | ✅ douyin 2026-11-03T19:00 free | 18:00 已被 S-1001 占用，备选中最接近且不早于原要求的是 19:00，需确认其确实空闲。 | save_schedule_draft |
| 5 | 5 | `save_schedule_draft` | {"items": [{"material_id": "M01", "channel": "douyin", "slot": "2026-11-03T19:00", "confirmation_status": "pending", "note": "原要求 2026-11-03T18:00 抖音时段已被排期 S-1001（M90 品牌直播预告）占用，建议顺延至同日 19:00，需用户确认是否接受该时段改动"}]} | ✅ 草稿 D-763DEB3C duplicate（修订 1，1 条，未发布） | M01 审核 pass，原要求的抖音 18:00 已被 S-1001 占用，改用同日最近的空闲整点 19:00，因改动用户硬性要求故置为 pending。 | finish |
| 6 | 6 | `finish` | {"items": [{"material_id": "M01", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-03T19:00", "confirmation_status": "pending", "pending_items": ["原要求抖音 2026-11-03T18:00 已被排期 S-1001（M90 品牌直播预告）占用，草稿改为同日 19:00，请确认是否接受该时段改动（或指定其他时段）"], "in_draft": true}], "summary": "REQ-02 仅含 1 个素材 M01（磁吸手机壳开箱）。get_material 显示为原创、音乐 MUS-1031 授权至 2027-12-31、无真人出镜，元数据完整无需补查版权。check_rules 在 2026-11-03 返回 pass、无 findings。用户要求的抖音 2026-11-03T18:00 已被排期 S-1001（M90 品牌直播预告）占用，按“不早于原要求的最近空闲时段”改议 19:00（已查为空闲），素材无 acceptable_window 且请求未批准该时段，故确认状态为 pending。已保存为排期草稿 D-763DEB3C（返回 duplicate，即同一份草稿已存在，未重复创建），仅草稿、未发布。待用户确认时段改动后即可推进。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M01 | pass | — | — | douyin 2026-11-03T18:00 | douyin 2026-11-03T19:00 | pending | ["原要求抖音 2026-11-03T18:00 已被排期 S-1001（M90 品牌直播预告）占用，草稿改为同日 19:00，请确认是否接受该时段改动（或指定其他时段）"] | saved |

**模型总结**：REQ-02 仅含 1 个素材 M01（磁吸手机壳开箱）。get_material 显示为原创、音乐 MUS-1031 授权至 2027-12-31、无真人出镜，元数据完整无需补查版权。check_rules 在 2026-11-03 返回 pass、无 findings。用户要求的抖音 2026-11-03T18:00 已被排期 S-1001（M90 品牌直播预告）占用，按“不早于原要求的最近空闲时段”改议 19:00（已查为空闲），素材无 acceptable_window 且请求未批准该时段，故确认状态为 pending。已保存为排期草稿 D-763DEB3C（返回 duplicate，即同一份草稿已存在，未重复创建），仅草稿、未发布。待用户确认时段改动后即可推进。
