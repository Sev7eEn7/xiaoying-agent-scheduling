# 08_save_fail · 保存失败

- 输入：`examples/inputs/08_save_fail.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/08_save_fail.json --provider deepseek --store .runtime/s08.json --inject save_fail`
- 模型：`deepseek-chat`；模型轮次 6/15；工具调用 7/40；finish 被退回 0 次
- 任务状态：**save_failed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "failed", "draft_id": null, "attempts": 3, "errors": ["STORAGE_UNAVAILABLE", "STORAGE_UNAVAILABLE", "STORAGE_UNAVAILABLE"]}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M02"} | ✅ 找到 M02《秋季通勤三套穿搭》，license=有 | 请求要求为 M02 排期，先读取素材元数据以确认基本信息。 | check_rules |
| 2 | 1 | `check_rules` | {"material_id": "M02", "publish_at": "2026-11-08T12:00"} | ✅ M02 审核 pass | 按请求的渠道与时段对 M02 执行审核规则检查。 | query_slots |
| 3 | 2 | `query_slots` | {"channel": "xiaohongshu", "publish_at": "2026-11-08T12:00"} | ✅ xiaohongshu 2026-11-08T12:00 free | M02 审核结果为 pass，需确认请求的小红书 2026-11-08 12:00 时段是否可用。 | save_schedule_draft |
| 4 | 3 | `save_schedule_draft` | {"items": [{"material_id": "M02", "channel": "xiaohongshu", "slot": "2026-11-08T12:00", "confirmation_status": "not_required"}]} | ❌ 失败 STORAGE_UNAVAILABLE：草稿存储服务不可用，本次未写入任何数据 | M02 审核 pass 且小红书 2026-11-08 12:00 时段空闲，与用户要求一致，保存为草稿。 | save_schedule_draft |
| 5 | 4 | `save_schedule_draft` | {"items": [{"channel": "xiaohongshu", "confirmation_status": "not_required", "material_id": "M02", "slot": "2026-11-08T12:00"}]} | ❌ 失败 STORAGE_UNAVAILABLE：草稿存储服务不可用，本次未写入任何数据 | 上次保存返回 STORAGE_UNAVAILABLE 且 retryable=true，重试保存同一份草稿。 | save_schedule_draft |
| 6 | 5 | `save_schedule_draft` | {"items": [{"channel": "xiaohongshu", "confirmation_status": "not_required", "material_id": "M02", "slot": "2026-11-08T12:00"}]} | ❌ 失败 STORAGE_UNAVAILABLE：草稿存储服务不可用，本次未写入任何数据 | 第二次保存仍返回 STORAGE_UNAVAILABLE，按规则进行最后一次重试。 | finish |
| 7 | 6 | `finish` | {"items": [{"material_id": "M02", "review_status": "pass", "risk_reasons": [], "suggested_channel": "xiaohongshu", "suggested_slot": "2026-11-08T12:00", "confirmation_status": "not_required", "pending_items": ["草稿保存失败（STORAGE_UNAVAILABLE，已重试 2 次仍不可用），需存储服务恢复后重新保存排期草稿"], "in_draft": false}], "summary": "M02《秋季通勤三套穿搭》审核通过（原创、有肖像授权、非商业、无音乐），小红书 2026-11-08 12:00 时段空闲，与请求一致无需确认。但草稿存储服务连续三次返回 STORAGE_UNAVAILABLE，本次未写入任何草稿，需待服务恢复后重新保存；未做任何发布操作。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M02 | pass | — | — | xiaohongshu 2026-11-08T12:00 | xiaohongshu 2026-11-08T12:00 | not_required | ["草稿保存失败（STORAGE_UNAVAILABLE，已重试 2 次仍不可用），需存储服务恢复后重新保存排期草稿"] | save_failed |

**模型总结**：M02《秋季通勤三套穿搭》审核通过（原创、有肖像授权、非商业、无音乐），小红书 2026-11-08 12:00 时段空闲，与请求一致无需确认。但草稿存储服务连续三次返回 STORAGE_UNAVAILABLE，本次未写入任何草稿，需待服务恢复后重新保存；未做任何发布操作。
