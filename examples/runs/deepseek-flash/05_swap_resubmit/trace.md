# 05_swap_resubmit · 更换占用时段后重复提交

- 输入：`examples/inputs/02_conflict.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/02_conflict.json --provider deepseek --store .runtime/chainA.json --schedule data/schedule_variant.json`
- 模型：`deepseek-flash`；模型轮次 4/15；工具调用 5/40；finish 被退回 0 次
- 任务状态：**completed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "updated", "draft_id": "D-763DEB3C", "revision": 3, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M01"} | ✅ 找到 M01《磁吸手机壳开箱》，license=有 | 请求中要求为 M01 排期，先读取元数据确认审核所需信息。 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M01", "publish_at": "2026-11-03T18:00"} | ✅ M01 审核 pass | 元数据含原创版权与音乐授权（有效期至 2027-12-31），按请求时段 2026-11-03T18:00 执行审核规则检查。 | query_slots |
| 3 | 2 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-03T18:00"} | ✅ douyin 2026-11-03T18:00 free | 确认用户硬性要求的抖音 2026-11-03T18:00 时段是否可用。 | save_schedule_draft |
| 4 | 3 | `save_schedule_draft` | {"items": [{"material_id": "M01", "channel": "douyin", "slot": "2026-11-03T18:00", "confirmation_status": "not_required"}]} | ✅ 草稿 D-763DEB3C updated（修订 3，1 条，未发布） | M01 审核 pass 且抖音该时段空闲，与用户硬性要求一致，直接存入草稿。 | finish |
| 5 | 4 | `finish` | {"items": [{"material_id": "M01", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-03T18:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}], "summary": "M01（磁吸手机壳开箱）按规则检查通过：版权为原创、音乐授权有效期至 2027-12-31，无人物出镜无肖像授权问题，非商业推广无需广告标识。抖音 2026-11-03T18:00 时段空闲，与用户要求一致，无需确认。已保存为排期草稿（draft_id D-763DEB3C，第 3 次修订），仅为草稿，尚未发布。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M01 | pass | — | — | douyin 2026-11-03T18:00 | douyin 2026-11-03T18:00 | not_required | — | saved |

**模型总结**：M01（磁吸手机壳开箱）按规则检查通过：版权为原创、音乐授权有效期至 2027-12-31，无人物出镜无肖像授权问题，非商业推广无需广告标识。抖音 2026-11-03T18:00 时段空闲，与用户要求一致，无需确认。已保存为排期草稿（draft_id D-763DEB3C，第 3 次修订），仅为草稿，尚未发布。
