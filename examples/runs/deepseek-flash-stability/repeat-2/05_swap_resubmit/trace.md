# 05_swap_resubmit · 更换占用时段后重复提交

- 输入：`examples/inputs/02_conflict.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/02_conflict.json --provider deepseek --store .runtime/chainA.json --schedule data/schedule_variant.json`
- 模型：`deepseek-flash`；模型轮次 5/15；工具调用 5/40；finish 被退回 0 次
- 任务状态：**completed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "updated", "draft_id": "D-763DEB3C", "revision": 3, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M01"} | ✅ 找到 M01《磁吸手机壳开箱》，license=有 | 请求中只有 M01 一个素材，先读取其元数据以判断审核所需信息是否齐全。 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M01", "publish_at": "2026-11-03T18:00"} | ✅ M01 审核 pass | 元数据完整（原创、配乐授权到 2027-12-31），按用户要求的时段做审核检查。 | query_slots |
| 3 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-03T18:00"} | ✅ douyin 2026-11-03T18:00 free | 审核结论为 pass，现查询抖音 2026-11-03 18:00 是否可用，以确认能否按用户硬性要求排期。 | save_schedule_draft |
| 4 | 4 | `save_schedule_draft` | {"items": [{"material_id": "M01", "channel": "douyin", "slot": "2026-11-03T18:00", "confirmation_status": "not_required"}]} | ✅ 草稿 D-763DEB3C updated（修订 3，1 条，未发布） | M01 审核通过且抖音 18:00 空闲，与用户要求完全一致，故按原时段保存草稿。 | finish |
| 5 | 5 | `finish` | {"items": [{"material_id": "M01", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-03T18:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}], "summary": "M01（磁吸手机壳开箱）审核通过：原创素材、配乐授权有效期至 2027-12-31、无人物出镜与商业推广要素，findings 为空。抖音 2026-11-03 18:00 查询为空闲，与用户硬性要求一致，无需调整。已按原时段保存排期草稿 D-763DEB3C（revision 3，状态 draft，未发布，上线需另行发布流程）。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M01 | pass | — | — | douyin 2026-11-03T18:00 | douyin 2026-11-03T18:00 | not_required | — | saved |

**模型总结**：M01（磁吸手机壳开箱）审核通过：原创素材、配乐授权有效期至 2027-12-31、无人物出镜与商业推广要素，findings 为空。抖音 2026-11-03 18:00 查询为空闲，与用户硬性要求一致，无需调整。已按原时段保存排期草稿 D-763DEB3C（revision 3，状态 draft，未发布，上线需另行发布流程）。
