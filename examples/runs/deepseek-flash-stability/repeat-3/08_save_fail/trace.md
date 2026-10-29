# 08_save_fail · 保存失败

- 输入：`examples/inputs/08_save_fail.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/08_save_fail.json --provider deepseek --store .runtime/s08.json --inject save_fail`
- 模型：`deepseek-flash`；模型轮次 6/15；工具调用 7/40；finish 被退回 0 次
- 任务状态：**save_failed**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "failed", "draft_id": null, "attempts": 3, "errors": ["STORAGE_UNAVAILABLE", "STORAGE_UNAVAILABLE", "STORAGE_UNAVAILABLE"]}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M02"} | ✅ 找到 M02《秋季通勤三套穿搭》，license=有 | 先读取 M02 元数据，确认素材基本信息与内容要素，再决定后续审核步骤 | check_rules |
| 2 | 1 | `check_rules` | {"material_id": "M02", "publish_at": "2026-11-08T12:00"} | ✅ M02 审核 pass | 按请求的小红书 2026-11-08 12:00 时段校验 M02 的审核规则与授权有效期 | query_slots |
| 3 | 2 | `query_slots` | {"channel": "xiaohongshu", "publish_at": "2026-11-08T12:00"} | ✅ xiaohongshu 2026-11-08T12:00 free | M02 审核结果为 pass，现在确认请求的小红书 2026-11-08 12:00 时段是否可排期 | save_schedule_draft |
| 4 | 3 | `save_schedule_draft` | {"items": [{"material_id": "M02", "channel": "xiaohongshu", "slot": "2026-11-08T12:00", "confirmation_status": "not_required", "note": ""}]} | ❌ 失败 STORAGE_UNAVAILABLE：草稿存储服务不可用，本次未写入任何数据 | M02 审核 pass 且请求的小红书 2026-11-08 12:00 时段空闲，按用户硬性要求原样保存草稿 | save_schedule_draft |
| 5 | 4 | `save_schedule_draft` | {"items": [{"channel": "xiaohongshu", "confirmation_status": "not_required", "material_id": "M02", "note": "", "slot": "2026-11-08T12:00"}]} | ❌ 失败 STORAGE_UNAVAILABLE：草稿存储服务不可用，本次未写入任何数据 | 上一次保存返回 STORAGE_UNAVAILABLE（retryable=true），按规则重试同一次草稿保存 | save_schedule_draft |
| 6 | 5 | `save_schedule_draft` | {"items": [{"channel": "xiaohongshu", "confirmation_status": "not_required", "material_id": "M02", "note": "", "slot": "2026-11-08T12:00"}]} | ❌ 失败 STORAGE_UNAVAILABLE：草稿存储服务不可用，本次未写入任何数据 | 第二次重试保存仍返回 STORAGE_UNAVAILABLE，这是同一次草稿的最后一次重试尝试 | finish |
| 7 | 6 | `finish` | {"items": [{"material_id": "M02", "review_status": "pass", "risk_reasons": [], "suggested_channel": "xiaohongshu", "suggested_slot": "2026-11-08T12:00", "confirmation_status": "not_required", "pending_items": ["草稿保存失败：草稿存储服务不可用（STORAGE_UNAVAILABLE），已重试 2 次仍失败，需存储恢复后重新保存该条排期"], "in_draft": false}], "summary": "M02「秋季通勤三套穿搭」按 2026-11-08 12:00 审核结果为 pass（无 findings，原创版权、无音乐、有肖像授权、非商业、无广告标），小红书该时段查询为 free，时段与用户要求一致，无需任何改动，审核与排期规划均无待确认项。但【排期草稿未能保存】：save_schedule_draft 连续三次返回 STORAGE_UNAVAILABLE（可重试类错误，已用满 2 次重试），存储服务不可用、未写入任何数据，因此本素材当前不在草稿中。请在存储服务恢复后重新提交同一排期保存（内容相同则幂等返回 duplicate）。本环节无发布能力，未做任何发布操作。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M02 | pass | — | — | xiaohongshu 2026-11-08T12:00 | xiaohongshu 2026-11-08T12:00 | not_required | ["草稿保存失败：草稿存储服务不可用（STORAGE_UNAVAILABLE），已重试 2 次仍失败，需存储恢复后重新保存该条排期"] | save_failed |

**模型总结**：M02「秋季通勤三套穿搭」按 2026-11-08 12:00 审核结果为 pass（无 findings，原创版权、无音乐、有肖像授权、非商业、无广告标），小红书该时段查询为 free，时段与用户要求一致，无需任何改动，审核与排期规划均无待确认项。但【排期草稿未能保存】：save_schedule_draft 连续三次返回 STORAGE_UNAVAILABLE（可重试类错误，已用满 2 次重试），存储服务不可用、未写入任何数据，因此本素材当前不在草稿中。请在存储服务恢复后重新提交同一排期保存（内容相同则幂等返回 duplicate）。本环节无发布能力，未做任何发布操作。
