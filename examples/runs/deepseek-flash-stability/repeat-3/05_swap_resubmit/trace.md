# 05_swap_resubmit · 更换占用时段后重复提交

- 输入：`examples/inputs/02_conflict.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/02_conflict.json --provider deepseek --store .runtime/chainA.json --schedule data/schedule_variant.json`
- 模型：`deepseek-flash`；模型轮次 4/15；工具调用 5/40；finish 被退回 0 次
- 任务状态：**completed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "updated", "draft_id": "D-763DEB3C", "revision": 3, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M01"} | ✅ 找到 M01《磁吸手机壳开箱》，license=有 | 请求中列出了 M01，先读取其元数据确认渠道与审核所需信息。 | check_rules |
| 2 | 1 | `check_rules` | {"material_id": "M01", "publish_at": "2026-11-03T18:00"} | ✅ M01 审核 pass | 需要按规则校验 M01 在用户要求的 2026-11-03T18:00 是否可发。 | query_slots |
| 3 | 2 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-03T18:00"} | ✅ douyin 2026-11-03T18:00 free | M01 已通过规则检查，需确认抖音 2026-11-03T18:00 是否空闲以决定是否原时段排期。 | save_schedule_draft |
| 4 | 3 | `save_schedule_draft` | {"items": [{"material_id": "M01", "channel": "douyin", "slot": "2026-11-03T18:00", "confirmation_status": "not_required"}]} | ✅ 草稿 D-763DEB3C updated（修订 3，1 条，未发布） | M01 规则检查为 pass，且抖音 2026-11-03T18:00 空闲、与用户要求一致，故按原要求保存草稿。 | finish |
| 5 | 4 | `finish` | {"items": [{"material_id": "M01", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-03T18:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}], "summary": "REQ-02 处理完成：M01「磁吸手机壳开箱」审核通过（原创素材，音乐授权 MUS-1031 有效期至 2027-12-31，无人物肖像、非商业推广）。抖音 2026-11-03T18:00 时段空闲，按用户要求原时段排期，无需确认。已保存为排期草稿 D-763DEB3C（修订 3，state=draft），未发布上线。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M01 | pass | — | — | douyin 2026-11-03T18:00 | douyin 2026-11-03T18:00 | not_required | — | saved |

**模型总结**：REQ-02 处理完成：M01「磁吸手机壳开箱」审核通过（原创素材，音乐授权 MUS-1031 有效期至 2027-12-31，无人物肖像、非商业推广）。抖音 2026-11-03T18:00 时段空闲，按用户要求原时段排期，无需确认。已保存为排期草稿 D-763DEB3C（修订 3，state=draft），未发布上线。
