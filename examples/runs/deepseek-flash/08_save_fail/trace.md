# 08_save_fail · 保存失败

- 输入：`examples/inputs/08_save_fail.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/08_save_fail.json --provider deepseek --store .runtime/s08.json --inject save_fail`
- 模型：`deepseek-flash`；模型轮次 7/15；工具调用 7/40；finish 被退回 0 次
- 任务状态：**save_failed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "failed", "draft_id": null, "attempts": 3, "errors": ["STORAGE_UNAVAILABLE", "STORAGE_UNAVAILABLE", "STORAGE_UNAVAILABLE"]}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M02"} | ✅ 找到 M02《秋季通勤三套穿搭》，license=有 | 开始处理 REQ-08，先读取 M02 的元数据以确认审核所需信息。 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M02", "publish_at": "2026-11-08T12:00"} | ✅ M02 审核 pass | M02 元数据完整（原创、有肖像授权），按请求的 2026-11-08T12:00 检查规则与授权有效期。 | query_slots |
| 3 | 3 | `query_slots` | {"channel": "xiaohongshu", "publish_at": "2026-11-08T12:00"} | ✅ xiaohongshu 2026-11-08T12:00 free | M02 规则检查为 pass，进一步确认用户要求的小红书 2026-11-08T12:00 是否空闲。 | save_schedule_draft |
| 4 | 4 | `save_schedule_draft` | {"items": [{"material_id": "M02", "channel": "xiaohongshu", "slot": "2026-11-08T12:00", "confirmation_status": "not_required"}]} | ❌ 失败 STORAGE_UNAVAILABLE：草稿存储服务不可用，本次未写入任何数据 | M02 审核通过且小红书 2026-11-08T12:00 空闲，与用户要求完全一致，直接保存为草稿。 | save_schedule_draft |
| 5 | 5 | `save_schedule_draft` | {"items": [{"channel": "xiaohongshu", "confirmation_status": "not_required", "material_id": "M02", "slot": "2026-11-08T12:00"}]} | ❌ 失败 STORAGE_UNAVAILABLE：草稿存储服务不可用，本次未写入任何数据 | 上一次保存因 STORAGE_UNAVAILABLE 未写入且标记 retryable=true，按规则重试同一份草稿。 | save_schedule_draft |
| 6 | 6 | `save_schedule_draft` | {"items": [{"channel": "xiaohongshu", "confirmation_status": "not_required", "material_id": "M02", "slot": "2026-11-08T12:00"}]} | ❌ 失败 STORAGE_UNAVAILABLE：草稿存储服务不可用，本次未写入任何数据 | 第二次保存仍为 STORAGE_UNAVAILABLE（retryable），进行规则允许的最后一次重试。 | finish |
| 7 | 7 | `finish` | {"items": [{"material_id": "M02", "review_status": "pass", "risk_reasons": [], "suggested_channel": "xiaohongshu", "suggested_slot": "2026-11-08T12:00", "confirmation_status": "not_required", "pending_items": ["草稿存储服务不可用（STORAGE_UNAVAILABLE），已重试 2 次仍失败，草稿未写入，需稍后重新保存"], "in_draft": false}], "summary": "M02《秋季通勤三套穿搭》：元数据完整（原创，版权持有人内容组B，肖像授权已有，非商用无广告标注），按 2026-11-08T12:00 规则检查为 pass，无风险发现。小红书该整点时段查询为 free，与用户要求完全一致，无需改动、无需用户确认。排期草稿保存三次均因草稿存储服务不可用（STORAGE_UNAVAILABLE，retryable）而失败，未写入任何数据，因此该素材目前不在草稿中。建议存储服务恢复后按原时段（xiaohongshu / 2026-11-08T12:00）重新保存；本助手无发布能力，未做任何发布操作。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M02 | pass | — | — | xiaohongshu 2026-11-08T12:00 | xiaohongshu 2026-11-08T12:00 | not_required | ["草稿存储服务不可用（STORAGE_UNAVAILABLE），已重试 2 次仍失败，草稿未写入，需稍后重新保存"] | save_failed |

**模型总结**：M02《秋季通勤三套穿搭》：元数据完整（原创，版权持有人内容组B，肖像授权已有，非商用无广告标注），按 2026-11-08T12:00 规则检查为 pass，无风险发现。小红书该整点时段查询为 free，与用户要求完全一致，无需改动、无需用户确认。排期草稿保存三次均因草稿存储服务不可用（STORAGE_UNAVAILABLE，retryable）而失败，未写入任何数据，因此该素材目前不在草稿中。建议存储服务恢复后按原时段（xiaohongshu / 2026-11-08T12:00）重新保存；本助手无发布能力，未做任何发布操作。
