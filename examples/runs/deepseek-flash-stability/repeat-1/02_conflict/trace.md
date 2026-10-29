# 02_conflict · 时段冲突（参考实例）

- 输入：`examples/inputs/02_conflict.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/02_conflict.json --provider deepseek --store .runtime/chainA.json`
- 模型：`deepseek-flash`；模型轮次 5/15；工具调用 6/40；finish 被退回 0 次
- 任务状态：**needs_confirmation**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-763DEB3C", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M01"} | ✅ 找到 M01《磁吸手机壳开箱》，license=有 | 请求中只有一个素材 M01，先读取其元数据以判断版权/授权信息是否完整。 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M01", "publish_at": "2026-11-03T18:00"} | ✅ M01 审核 pass | 元数据显示原创且音乐授权到 2027-12-31，需按请求时段跑规则确认有无其他风险。 | query_slots |
| 3 | 2 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-03T18:00"} | ✅ douyin 2026-11-03T18:00 occupied（已被排期 S-1001（M90 品牌直播预告）占用）；备选 19:00、16:00、21:00、15:00 | 确认抖音 2026-11-03 18:00 是否可用（本批次仅此一个时段）。 | check_rules |
| 4 | 3 | `check_rules` | {"material_id": "M01", "publish_at": "2026-11-03T19:00"} | ✅ M01 审核 pass | 原 18:00 已被占，拟改用同日 19:00 备选时段，按新时段复核规则与授权有效期。 | save_schedule_draft |
| 5 | 4 | `save_schedule_draft` | {"items": [{"material_id": "M01", "channel": "douyin", "slot": "2026-11-03T19:00", "confirmation_status": "pending", "note": "用户要求的抖音 2026-11-03 18:00 已被排期 S-1001（M90 品牌直播预告）占用，建议顺延至同日 19:00（最近的不早于原要求空闲整点），需用户确认是否接受该时段变更"}]} | ✅ 草稿 D-763DEB3C created（修订 1，1 条，未发布） | M01 规则检查通过，但原 18:00 已被占用，按最近可用备选 19:00 以 pending 状态写入草稿待确认。 | finish |
| 6 | 5 | `finish` | {"items": [{"material_id": "M01", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-03T19:00", "confirmation_status": "pending", "pending_items": ["用户指定的抖音 2026-11-03 18:00 已被排期 S-1001（M90 品牌直播预告）占用，建议改到同日 19:00，请确认是否接受该时段变更"], "in_draft": true}], "summary": "M01《磁吸手机壳开箱》审核通过（原创素材，音乐授权至 2027-12-31，无人物肖像与商业广告标识问题）。但用户要求的抖音 2026-11-03 18:00 已被排期 S-1001 占用，按“不早于原要求的最近空闲整点”建议顺延至 19:00，属对硬性要求的改动，故以 pending 状态写入排期草稿 D-763DEB3C（revision 1），等待用户确认。草稿仅为待发布安排，未发布、未上线。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M01 | pass | — | — | douyin 2026-11-03T18:00 | douyin 2026-11-03T19:00 | pending | ["用户指定的抖音 2026-11-03 18:00 已被排期 S-1001（M90 品牌直播预告）占用，建议改到同日 19:00，请确认是否接受该时段变更"] | saved |

**模型总结**：M01《磁吸手机壳开箱》审核通过（原创素材，音乐授权至 2027-12-31，无人物肖像与商业广告标识问题）。但用户要求的抖音 2026-11-03 18:00 已被排期 S-1001 占用，按“不早于原要求的最近空闲整点”建议顺延至 19:00，属对硬性要求的改动，故以 pending 状态写入排期草稿 D-763DEB3C（revision 1），等待用户确认。草稿仅为待发布安排，未发布、未上线。
