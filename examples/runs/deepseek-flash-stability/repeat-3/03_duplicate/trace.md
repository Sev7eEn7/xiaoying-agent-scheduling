# 03_duplicate · 重复提交同一请求

- 输入：`examples/inputs/02_conflict.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/02_conflict.json --provider deepseek --store .runtime/chainA.json`
- 模型：`deepseek-flash`；模型轮次 7/15；工具调用 7/40；finish 被退回 0 次
- 任务状态：**needs_confirmation**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "duplicate", "draft_id": "D-763DEB3C", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M01"} | ✅ 找到 M01《磁吸手机壳开箱》，license=有 | 先读取请求中唯一素材 M01 的元数据，确认存在性与基础信息。 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M01", "publish_at": "2026-11-03T18:00"} | ✅ M01 审核 pass | M01 元数据齐全（原创、音乐授权至 2027-12-31），按用户要求的 2026-11-03T18:00 做规则校验。 | query_slots |
| 3 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-03T18:00"} | ✅ douyin 2026-11-03T18:00 occupied（已被排期 S-1001（M90 品牌直播预告）占用）；备选 19:00、16:00、21:00、15:00 | M01 审核通过，现查询抖音 2026-11-03T18:00 是否可用；本批次仅此一个素材，无 also_taken。 | query_slots |
| 4 | 4 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-03T19:00"} | ✅ douyin 2026-11-03T19:00 free | 18:00 已被 S-1001 占用，按“不早于原要求的最近空闲时段”规则验证 2026-11-03T19:00 是否可用。 | check_rules |
| 5 | 5 | `check_rules` | {"material_id": "M01", "publish_at": "2026-11-03T19:00"} | ✅ M01 审核 pass | 已确认 19:00 空闲，按拟用新时段复核 M01 的授权有效期与规则结果。 | save_schedule_draft |
| 6 | 6 | `save_schedule_draft` | {"items": [{"material_id": "M01", "channel": "douyin", "slot": "2026-11-03T19:00", "confirmation_status": "pending", "note": "用户原要求 2026-11-03T18:00 已被 S-1001（M90 品牌直播预告）占用，改用同日最近空闲时段 19:00，待用户确认"}]} | ✅ 草稿 D-763DEB3C duplicate（修订 1，1 条，未发布） | M01 规则校验通过且 19:00 空闲，原 18:00 被占用需用户确认改期，故以 pending 状态保存为草稿。 | finish |
| 7 | 7 | `finish` | {"items": [{"material_id": "M01", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-03T19:00", "confirmation_status": "pending", "pending_items": ["原定 2026-11-03T18:00 抖音时段已被排期 S-1001（M90 品牌直播预告）占用，草稿改为 2026-11-03T19:00，需用户确认改期（或另指定时段）"], "in_draft": true}], "summary": "M01《磁吸手机壳开箱》审核通过：原创版权自有、音乐授权至 2027-12-31、无真人出镜、非商业推广，18:00 与 19:00 两个时点 check_rules 均为 pass。抖音 2026-11-03T18:00 已被 S-1001（M90 品牌直播预告）占用，按“不早于原要求最近空闲时段”改为同日 19:00（已确认空闲），因此草稿中该条为 pending 待用户确认改期。已合并保存为排期草稿 D-763DEB3C（状态 duplicate，说明同内容草稿已存在，未重复创建），仅草稿，未发布。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M01 | pass | — | — | douyin 2026-11-03T18:00 | douyin 2026-11-03T19:00 | pending | ["原定 2026-11-03T18:00 抖音时段已被排期 S-1001（M90 品牌直播预告）占用，草稿改为 2026-11-03T19:00，需用户确认改期（或另指定时段）"] | saved |

**模型总结**：M01《磁吸手机壳开箱》审核通过：原创版权自有、音乐授权至 2027-12-31、无真人出镜、非商业推广，18:00 与 19:00 两个时点 check_rules 均为 pass。抖音 2026-11-03T18:00 已被 S-1001（M90 品牌直播预告）占用，按“不早于原要求最近空闲时段”改为同日 19:00（已确认空闲），因此草稿中该条为 pending 待用户确认改期。已合并保存为排期草稿 D-763DEB3C（状态 duplicate，说明同内容草稿已存在，未重复创建），仅草稿，未发布。
