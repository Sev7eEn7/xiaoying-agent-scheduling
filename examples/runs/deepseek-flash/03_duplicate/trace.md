# 03_duplicate · 重复提交同一请求

- 输入：`examples/inputs/02_conflict.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/02_conflict.json --provider deepseek --store .runtime/chainA.json`
- 模型：`deepseek-flash`；模型轮次 5/15；工具调用 6/40；finish 被退回 0 次
- 任务状态：**needs_confirmation**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "duplicate", "draft_id": "D-763DEB3C", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M01"} | ✅ 找到 M01《磁吸手机壳开箱》，license=有 | 请求要求为 M01 排期到抖音 2026-11-03T18:00，先读取素材元数据以确认是否存在及审核所需字段。 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M01", "publish_at": "2026-11-03T18:00"} | ✅ M01 审核 pass | 元数据显示为原创素材、音乐授权有效，按其要求的发布时间做正式审核校验。 | query_slots |
| 3 | 2 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-03T18:00"} | ✅ douyin 2026-11-03T18:00 occupied（已被排期 S-1001（M90 品牌直播预告）占用）；备选 19:00、16:00、21:00、15:00 | 审核同时确认用户要求的抖音 2026-11-03T18:00 时段是否可用。 | check_rules |
| 4 | 3 | `check_rules` | {"material_id": "M01", "publish_at": "2026-11-03T19:00"} | ✅ M01 审核 pass | 原 18:00 已被 S-1001 占用，改用最近的 19:00，需按新时段重新校验审核结论。 | save_schedule_draft |
| 5 | 4 | `save_schedule_draft` | {"items": [{"material_id": "M01", "channel": "douyin", "slot": "2026-11-03T19:00", "confirmation_status": "pending", "note": "原要求 2026-11-03T18:00 已被 S-1001（M90 品牌直播预告）占用，建议顺延至 19:00，待用户确认"}]} | ✅ 草稿 D-763DEB3C duplicate（修订 1，1 条，未发布） | M01 审核 pass，原 18:00 被占用且 19:00 已复核 pass，故按待确认的替代时段保存草稿。 | finish |
| 6 | 5 | `finish` | {"items": [{"material_id": "M01", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-03T19:00", "confirmation_status": "pending", "pending_items": ["原要求时段 2026-11-03T18:00 已被 S-1001（M90 品牌直播预告）占用，是否接受顺延至 2026-11-03T19:00（已复核审核通过、时段空闲）"], "in_draft": true}], "summary": "REQ-02 共 1 个素材：M01（磁吸手机壳开箱）规则审核 pass，无风险发现，音乐授权有效至 2027-12-31。用户要求的抖音 2026-11-03T18:00 已被 S-1001（M90 品牌直播预告）占用，按「不早于原要求的最近空闲时段」选了 19:00，并已在该时段重新审核通过。因时段与硬性要求不一致，草稿中以 pending 记录，等待用户确认。已保存为排期草稿 D-763DEB3C（工具返回 duplicate，表示同一请求已有相同草稿，未重复创建）；仅为草稿，未发布、未上线。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M01 | pass | — | — | douyin 2026-11-03T18:00 | douyin 2026-11-03T19:00 | pending | ["原要求时段 2026-11-03T18:00 已被 S-1001（M90 品牌直播预告）占用，是否接受顺延至 2026-11-03T19:00（已复核审核通过、时段空闲）"] | saved |

**模型总结**：REQ-02 共 1 个素材：M01（磁吸手机壳开箱）规则审核 pass，无风险发现，音乐授权有效至 2027-12-31。用户要求的抖音 2026-11-03T18:00 已被 S-1001（M90 品牌直播预告）占用，按「不早于原要求的最近空闲时段」选了 19:00，并已在该时段重新审核通过。因时段与硬性要求不一致，草稿中以 pending 记录，等待用户确认。已保存为排期草稿 D-763DEB3C（工具返回 duplicate，表示同一请求已有相同草稿，未重复创建）；仅为草稿，未发布、未上线。
