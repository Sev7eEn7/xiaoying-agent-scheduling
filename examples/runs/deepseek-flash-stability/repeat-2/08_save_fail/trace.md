# 08_save_fail · 保存失败

- 输入：`examples/inputs/08_save_fail.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/08_save_fail.json --provider deepseek --store .runtime/s08.json --inject save_fail`
- 模型：`deepseek-flash`；模型轮次 7/15；工具调用 7/40；finish 被退回 0 次
- 任务状态：**save_failed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "failed", "draft_id": null, "attempts": 3, "errors": ["STORAGE_UNAVAILABLE", "STORAGE_UNAVAILABLE", "STORAGE_UNAVAILABLE"]}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M02"} | ✅ 找到 M02《秋季通勤三套穿搭》，license=有 | 请求排期的素材 M02，先读取其元数据以了解审核所需信息。 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M02", "publish_at": "2026-11-08T12:00"} | ✅ M02 审核 pass | 元数据完整（原创、有肖像授权、非商业），按用户要求的 2026-11-08 12:00 做审核规则检查。 | query_slots |
| 3 | 3 | `query_slots` | {"channel": "xiaohongshu", "publish_at": "2026-11-08T12:00"} | ✅ xiaohongshu 2026-11-08T12:00 free | 审核结果为 pass，需确认用户指定的小红书 2026-11-08 12:00 时段是否可用。 | save_schedule_draft |
| 4 | 4 | `save_schedule_draft` | {"items": [{"material_id": "M02", "channel": "xiaohongshu", "slot": "2026-11-08T12:00", "confirmation_status": "not_required", "note": "与用户要求的渠道和时段完全一致，审核通过且时段空闲"}]} | ❌ 失败 STORAGE_UNAVAILABLE：草稿存储服务不可用，本次未写入任何数据 | M02 审核 pass 且小红书 2026-11-08 12:00 时段空闲，按用户原始要求保存排期草稿。 | save_schedule_draft |
| 5 | 5 | `save_schedule_draft` | {"items": [{"channel": "xiaohongshu", "confirmation_status": "not_required", "material_id": "M02", "note": "与用户要求的渠道和时段完全一致，审核通过且时段空闲", "slot": "2026-11-08T12:00"}]} | ❌ 失败 STORAGE_UNAVAILABLE：草稿存储服务不可用，本次未写入任何数据 | 上次保存因存储服务不可用失败（retryable=true），按规则重试同一份草稿。 | save_schedule_draft |
| 6 | 6 | `save_schedule_draft` | {"items": [{"channel": "xiaohongshu", "confirmation_status": "not_required", "material_id": "M02", "note": "与用户要求的渠道和时段完全一致，审核通过且时段空闲", "slot": "2026-11-08T12:00"}]} | ❌ 失败 STORAGE_UNAVAILABLE：草稿存储服务不可用，本次未写入任何数据 | 第二次重试（重试上限内最后一次）保存同一份草稿。 | finish |
| 7 | 7 | `finish` | {"items": [{"material_id": "M02", "review_status": "pass", "risk_reasons": [], "suggested_channel": "xiaohongshu", "suggested_slot": "2026-11-08T12:00", "confirmation_status": "not_required", "pending_items": ["草稿保存失败：草稿存储服务不可用（STORAGE_UNAVAILABLE），已按规则重试 2 次仍未写入，需稍后重新保存排期草稿"], "in_draft": false}], "summary": "M02（秋季通勤三套穿搭，小红书 2026-11-08 12:00）审核通过：原创授权、肖像授权齐全、非商业内容，check_rules 结果 pass；该时段查询为空闲，与用户要求完全一致，无需调整或确认。但保存排期草稿时草稿存储服务不可用（STORAGE_UNAVAILABLE），按规则重试 2 次后仍失败，本次未写入任何数据，因此 M02 目前不在草稿中，需待存储恢复后重新保存。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M02 | pass | — | — | xiaohongshu 2026-11-08T12:00 | xiaohongshu 2026-11-08T12:00 | not_required | ["草稿保存失败：草稿存储服务不可用（STORAGE_UNAVAILABLE），已按规则重试 2 次仍未写入，需稍后重新保存排期草稿"] | save_failed |

**模型总结**：M02（秋季通勤三套穿搭，小红书 2026-11-08 12:00）审核通过：原创授权、肖像授权齐全、非商业内容，check_rules 结果 pass；该时段查询为空闲，与用户要求完全一致，无需调整或确认。但保存排期草稿时草稿存储服务不可用（STORAGE_UNAVAILABLE），按规则重试 2 次后仍失败，本次未写入任何数据，因此 M02 目前不在草稿中，需待存储恢复后重新保存。
