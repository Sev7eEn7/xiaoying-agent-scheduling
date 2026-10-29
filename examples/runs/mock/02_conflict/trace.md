# 02_conflict · 时段冲突（参考实例）

- 输入：`examples/inputs/02_conflict.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/02_conflict.json --provider mock --store .runtime/chainA.json`
- 模型：`mock-rule-policy`；模型轮次 5/15；工具调用 5/40；finish 被退回 0 次
- 任务状态：**needs_confirmation**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-763DEB3C", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M01"} | ✅ 找到 M01《磁吸手机壳开箱》，license=有 | 先读取素材元数据 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M01", "publish_at": "2026-11-03T18:00"} | ✅ M01 审核 pass | 读取成功，按发布时间做规则检查 | query_slots |
| 3 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-03T18:00", "also_taken": []} | ✅ douyin 2026-11-03T18:00 occupied（已被排期 S-1001（M90 品牌直播预告）占用）；备选 19:00、16:00、21:00、15:00 | 审核可排期，查询目标时段 | save_schedule_draft |
| 4 | 4 | `save_schedule_draft` | {"items": [{"material_id": "M01", "channel": "douyin", "slot": "2026-11-03T19:00", "confirmation_status": "pending", "note": "2026-11-03T18:00 不可用（已被排期 S-1001（M90 品牌直播预告）占用），建议改为 2026-11-03T19:00，需用户确认"}]} | ✅ 草稿 D-763DEB3C created（修订 1，1 条，未发布） | 所有素材处理完毕，保存可排期条目为草稿 | finish |
| 5 | 5 | `finish` | {"items": [{"material_id": "M01", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-03T19:00", "confirmation_status": "pending", "pending_items": ["2026-11-03T18:00 不可用（已被排期 S-1001（M90 品牌直播预告）占用），建议改为 2026-11-03T19:00，需用户确认"], "in_draft": true}], "summary": "共 1 个素材，1 个已保存为草稿；未发布任何内容。"} | ✅ finish 通过工具记录核对 | 全部素材已处理 | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M01 | pass | — | — | douyin 2026-11-03T18:00 | douyin 2026-11-03T19:00 | pending | ["2026-11-03T18:00 不可用（已被排期 S-1001（M90 品牌直播预告）占用），建议改为 2026-11-03T19:00，需用户确认"] | saved |

**模型总结**：共 1 个素材，1 个已保存为草稿；未发布任何内容。
