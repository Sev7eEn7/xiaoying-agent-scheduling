# 09_batch_window · 同批次冲突 + 用户允许窗口

- 输入：`examples/inputs/09_batch_window.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/09_batch_window.json --provider deepseek --store .runtime/s09.json`
- 模型：`deepseek-flash`；模型轮次 6/15；工具调用 9/40；finish 被退回 0 次
- 任务状态：**completed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-E0F7B21A", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M09"} | ✅ 找到 M09《桌面收纳改造》，license=有 | 请求处理 REQ-09，需先读取 M09 元数据以确认渠道与授权信息。 | get_material |
| 2 | 1 | `get_material` | {"material_id": "M10"} | ✅ 找到 M10《城市夜跑路线推荐》，license=有 | 请求处理 REQ-09，需先读取 M10 元数据以确认渠道与授权信息。 | check_rules |
| 3 | 2 | `check_rules` | {"material_id": "M09", "publish_at": "2026-11-05T20:00"} | ✅ M09 审核 pass | M09 元数据完整（原创、音乐授权至 2027-09-30），按请求时段 2026-11-05T20:00 检查审核规则。 | check_rules |
| 4 | 2 | `check_rules` | {"material_id": "M10", "publish_at": "2026-11-05T20:00"} | ✅ M10 审核 pass | M10 元数据完整（原创、音乐授权至 2027-09-30、有肖像授权），按请求时段 2026-11-05T20:00 检查审核规则。 | query_slots |
| 5 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-05T20:00"} | ✅ douyin 2026-11-05T20:00 free | 两个素材都通过审核但同为抖音 20:00，先确认该时段本身可用，以便保留无窗口的 M09 原时段。 | query_slots |
| 6 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-05T21:00", "also_taken": [{"channel": "douyin", "slot": "2026-11-05T20:00"}]} | ✅ douyin 2026-11-05T21:00 free | M10 需避开已规划给 M09 的 20:00，按默认规则查其窗口内不早于原要求的最近时段 21:00。 | check_rules |
| 7 | 4 | `check_rules` | {"material_id": "M10", "publish_at": "2026-11-05T21:00"} | ✅ M10 审核 pass | M10 时段调整为 21:00，虽同日期仍复核一次授权有效期与规则，确保草稿校验一致。 | save_schedule_draft |
| 8 | 5 | `save_schedule_draft` | {"items": [{"material_id": "M09", "channel": "douyin", "slot": "2026-11-05T20:00", "confirmation_status": "not_required"}, {"material_id": "M10", "channel": "douyin", "slot": "2026-11-05T21:00", "confirmation_status": "not_required"}]} | ✅ 草稿 D-E0F7B21A created（修订 1，2 条，未发布） | 两者均审核 pass，抖音 20:00 空闲且保留给 M09，M10 调整到其窗口内 21:00（空闲），故均可排期并保存草稿。 | finish |
| 9 | 6 | `finish` | {"items": [{"material_id": "M09", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-05T20:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}, {"material_id": "M10", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-05T21:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}], "summary": "REQ-09 两个素材均审核通过（原创素材，配乐授权至 2027-09-30，M10 另有肖像授权）。二者原本都要求抖音 2026-11-05 20:00，存在渠道同时段冲突：保留无窗口的 M09 原时段 20:00，将 M10 顺延至 21:00（落在其可接受窗口 18:00–22:00 内，无需人工确认）。已合并保存为一份排期草稿 D-E0F7B21A（revision 1，2 条），仅为草稿，未发布、未上线。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M09 | pass | — | — | douyin 2026-11-05T20:00 | douyin 2026-11-05T20:00 | not_required | — | saved |
| M10 | pass | — | — | douyin 2026-11-05T20:00（可接受 18:00–22:00） | douyin 2026-11-05T21:00 | not_required | — | saved |

**模型总结**：REQ-09 两个素材均审核通过（原创素材，配乐授权至 2027-09-30，M10 另有肖像授权）。二者原本都要求抖音 2026-11-05 20:00，存在渠道同时段冲突：保留无窗口的 M09 原时段 20:00，将 M10 顺延至 21:00（落在其可接受窗口 18:00–22:00 内，无需人工确认）。已合并保存为一份排期草稿 D-E0F7B21A（revision 1，2 条），仅为草稿，未发布、未上线。
