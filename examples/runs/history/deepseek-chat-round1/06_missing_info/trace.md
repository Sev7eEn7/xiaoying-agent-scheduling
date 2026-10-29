# 06_missing_info · 素材信息缺失

- 输入：`examples/inputs/06_missing_info.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/06_missing_info.json --provider deepseek --store .runtime/s06.json`
- 模型：`deepseek-chat`；模型轮次 8/15；工具调用 14/40；finish 被退回 0 次
- 任务状态：**needs_confirmation**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-E1DC4F7C", "revision": 1, "attempts": 2, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M03"} | ✅ 找到 M03《社区咖啡馆探店》，license=缺失 | 请求要求为 M03 排期，先读取素材元数据以确认基本信息。 | get_material |
| 2 | 1 | `get_material` | {"material_id": "M05"} | ✅ 找到 M05《用户投稿：第一次带娃露营》，license=缺失 | 请求要求为 M05 排期，先读取素材元数据以确认基本信息。 | get_material |
| 3 | 1 | `get_material` | {"material_id": "M08"} | ✅ 找到 M08《五分钟快手早餐合集》，license=有 | 请求要求为 M08 排期（未给时间），先读取素材元数据。 | lookup_license |
| 4 | 2 | `lookup_license` | {"material_id": "M03"} | ✅ 登记库命中 CR-5531（original，持有方 内容组C，到期 2027-06-30） | M03 元数据 license 为 null，按规则先补查版权登记库。 | lookup_license |
| 5 | 2 | `lookup_license` | {"material_id": "M05"} | ✅ 登记库无 M05 的版权记录 | M05 元数据 license 为 null，按规则先补查版权登记库。 | check_rules |
| 6 | 2 | `check_rules` | {"material_id": "M08"} | ✅ M08 审核 pass | M08 版权信息完整（原创，内容组B），先按规则检查；其发布时间待定。 | check_rules |
| 7 | 3 | `check_rules` | {"material_id": "M03", "publish_at": "2026-11-06T12:00"} | ✅ M03 审核 pass，版权信息来自登记库补查 | M03 已通过 lookup_license 查到登记记录 CR-5531，按规则用该记录重新检查。 | check_rules |
| 8 | 3 | `check_rules` | {"material_id": "M05", "publish_at": "2026-11-06T15:00"} | ✅ M05 审核 incomplete：R01[missing] 缺少必填字段 owner；R01[missing] 缺少必填字段 license；可查询版权登记库补查；R03[missing] 使用了背景音乐但缺少音乐授权编号；R07[review] 出镜人物肖像授权未提供 | M05 版权补查无果，仍按规则检查以确认其余风险项。 | query_slots |
| 9 | 4 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-06T12:00"} | ✅ douyin 2026-11-06T12:00 free | M03 审核通过，按用户要求核查抖音 2026-11-06 12:00 是否可用。 | query_slots |
| 10 | 4 | `query_slots` | {"channel": "xiaohongshu", "publish_at": "2026-11-06T12:00"} | ✅ xiaohongshu 2026-11-06T12:00 free | M08 未给发布时间，先探测小红书 2026-11-06 12:00 作为候选时段。 | save_schedule_draft |
| 11 | 5 | `save_schedule_draft` | {"items": [{"material_id": "M03", "channel": "douyin", "slot": "2026-11-06T12:00", "confirmation_status": "not_required"}, {"material_id": "M08", "channel": "xiaohongshu", "slot": "2026-11-06T12:00", "confirmation_status": "pending", "note": "请求未指定发布时间，建议 2026-11-06 12:00 发布，待用户确认时段"}]} | ❌ 失败 VALIDATION_FAILED：草稿未保存：存在不合规条目，未写入任何数据；M08: 规则检查基于发布日 None，草稿时段为 2026-11-06T12:00，请用该时段重新 check_rules | M03 审核通过且抖音 12:00 空闲，按用户要求排期；M08 审核通过但请求缺发布时间，按建议时段排入并标记 pending 待确认；M05 资料缺失不放入草稿。 | check_rules |
| 12 | 6 | `check_rules` | {"material_id": "M08", "publish_at": "2026-11-06T12:00"} | ✅ M08 审核 pass | 保存校验要求 M08 按草稿时段 2026-11-06 12:00 重新检查规则。 | save_schedule_draft |
| 13 | 7 | `save_schedule_draft` | {"items": [{"channel": "douyin", "confirmation_status": "not_required", "material_id": "M03", "slot": "2026-11-06T12:00"}, {"channel": "xiaohongshu", "confirmation_status": "pending", "material_id": "M08", "note": "请求未指定发布时间，建议 2026-11-06 12:00 发布，待用户确认时段", "slot": "2026-11-06T12:00"}]} | ✅ 草稿 D-E1DC4F7C created（修订 1，2 条，未发布） | M08 已按 2026-11-06 12:00 重新检查通过，按校验要求重新保存草稿。 | finish |
| 14 | 8 | `finish` | {"items": [{"material_id": "M03", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-06T12:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}, {"material_id": "M05", "review_status": "needs_info", "risk_reasons": ["缺少必填字段 owner", "缺少必填字段 license，且版权登记库补查无记录", "使用了背景音乐但缺少音乐授权编号 music.license_id", "出镜人物肖像授权 portrait_release 未提供，需人工复核"], "suggested_channel": "douyin", "suggested_slot": null, "confirmation_status": "not_applicable", "pending_items": ["补充素材归属人 owner", "补充版权授权信息（版权登记库无记录，需提供授权文件）", "补充背景音乐授权编号", "补充出镜人物肖像授权"], "in_draft": false}, {"material_id": "M08", "review_status": "pass", "risk_reasons": [], "suggested_channel": "xiaohongshu", "suggested_slot": "2026-11-06T12:00", "confirmation_status": "pending", "pending_items": ["请求未指定发布时间，建议 2026-11-06 12:00 发布，待确认时段"], "in_draft": true}], "summary": "M03 审核通过，按用户要求排入抖音 2026-11-06 12:00；M08 审核通过，但请求未给发布时间，按建议时段小红书 2026-11-06 12:00 排入并标记待确认；M05 资料缺失（owner、版权、音乐授权、肖像授权），版权库补查无记录，列为 needs_info 未放入草稿。已保存排期草稿 D-E1DC4F7C（仅草稿，未发布）。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M03 | pass | — | — | douyin 2026-11-06T12:00 | douyin 2026-11-06T12:00 | not_required | — | saved |
| M05 | needs_info | ["缺少必填字段 owner", "缺少必填字段 license，且版权登记库补查无记录", "使用了背景音乐但缺少音乐授权编号 music.license_id", "出镜人物肖像授权 portrait_release 未提供，需人工复核"] | ["R01[missing] owner", "R01[missing] license", "R03[missing] music.license_id", "R07[review] portrait_release"] | douyin 2026-11-06T15:00 | douyin | not_applicable | ["补充素材归属人 owner", "补充版权授权信息（版权登记库无记录，需提供授权文件）", "补充背景音乐授权编号", "补充出镜人物肖像授权"] | not_saved |
| M08 | pass | — | — | xiaohongshu 未提供时间 | xiaohongshu 2026-11-06T12:00 | pending | ["请求未指定发布时间，建议 2026-11-06 12:00 发布，待确认时段"] | saved |

**模型总结**：M03 审核通过，按用户要求排入抖音 2026-11-06 12:00；M08 审核通过，但请求未给发布时间，按建议时段小红书 2026-11-06 12:00 排入并标记待确认；M05 资料缺失（owner、版权、音乐授权、肖像授权），版权库补查无记录，列为 needs_info 未放入草稿。已保存排期草稿 D-E1DC4F7C（仅草稿，未发布）。
