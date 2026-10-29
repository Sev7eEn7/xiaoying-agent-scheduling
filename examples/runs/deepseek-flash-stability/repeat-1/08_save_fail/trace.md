# 08_save_fail · 保存失败

- 输入：`examples/inputs/08_save_fail.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/08_save_fail.json --provider deepseek --store .runtime/s08.json --inject save_fail`
- 模型：`deepseek-flash`；模型轮次 7/15；工具调用 7/40；finish 被退回 0 次
- 任务状态：**save_failed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "failed", "draft_id": null, "attempts": 3, "errors": ["STORAGE_UNAVAILABLE", "STORAGE_UNAVAILABLE", "STORAGE_UNAVAILABLE"]}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M02"} | ✅ 找到 M02《秋季通勤三套穿搭》，license=有 | 先读取素材 M02 的元数据以了解其基本信息与版权状态。 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M02", "publish_at": "2026-11-08T12:00"} | ✅ M02 审核 pass | M02 元数据完整（原创、有肖像授权），按用户要求的小红书时段 2026-11-08T12:00 进行审核检查。 | query_slots |
| 3 | 3 | `query_slots` | {"channel": "xiaohongshu", "publish_at": "2026-11-08T12:00"} | ✅ xiaohongshu 2026-11-08T12:00 free | M02 审核通过，需确认用户指定的小红书 2026-11-08T12:00 时段是否可用。 | save_schedule_draft |
| 4 | 4 | `save_schedule_draft` | {"items": [{"material_id": "M02", "channel": "xiaohongshu", "slot": "2026-11-08T12:00", "confirmation_status": "not_required", "note": ""}]} | ❌ 失败 STORAGE_UNAVAILABLE：草稿存储服务不可用，本次未写入任何数据 | M02 审核通过且用户指定时段为空闲，与用户要求完全一致，可保存为排期草稿。 | save_schedule_draft |
| 5 | 5 | `save_schedule_draft` | {"items": [{"channel": "xiaohongshu", "confirmation_status": "not_required", "material_id": "M02", "note": "", "slot": "2026-11-08T12:00"}]} | ❌ 失败 STORAGE_UNAVAILABLE：草稿存储服务不可用，本次未写入任何数据 | 上次保存因存储服务不可用失败且标记可重试，故按相同内容重试保存草稿。 | save_schedule_draft |
| 6 | 6 | `save_schedule_draft` | {"items": [{"channel": "xiaohongshu", "confirmation_status": "not_required", "material_id": "M02", "note": "", "slot": "2026-11-08T12:00"}]} | ❌ 失败 STORAGE_UNAVAILABLE：草稿存储服务不可用，本次未写入任何数据 | 第二次重试仍报存储不可用（可重试），按规则进行最后一次重试保存。 | finish |
| 7 | 7 | `finish` | {"items": [{"material_id": "M02", "review_status": "pass", "risk_reasons": [], "suggested_channel": "xiaohongshu", "suggested_slot": "2026-11-08T12:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": false}], "summary": "M02《秋季通勤三套穿搭》审核通过（原创、肖像授权齐全、无商用/广告标识、无音乐、无授权到期限制），用户指定的小红书 2026-11-08T12:00 时段查询为空闲，内容与时段均无需改动。但保存排期草稿连续 3 次返回 STORAGE_UNAVAILABLE（可重试错误，未写入任何数据），因此本条尚未进入草稿，需待存储服务恢复后重新保存；本流程未进行任何发布操作。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M02 | pass | — | — | xiaohongshu 2026-11-08T12:00 | xiaohongshu 2026-11-08T12:00 | not_required | — | save_failed |

**模型总结**：M02《秋季通勤三套穿搭》审核通过（原创、肖像授权齐全、无商用/广告标识、无音乐、无授权到期限制），用户指定的小红书 2026-11-08T12:00 时段查询为空闲，内容与时段均无需改动。但保存排期草稿连续 3 次返回 STORAGE_UNAVAILABLE（可重试错误，未写入任何数据），因此本条尚未进入草稿，需待存储服务恢复后重新保存；本流程未进行任何发布操作。
