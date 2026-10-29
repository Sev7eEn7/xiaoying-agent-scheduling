# 06_missing_info · 素材信息缺失

- 输入：`examples/inputs/06_missing_info.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/06_missing_info.json --provider deepseek --store .runtime/s06.json`
- 模型：`deepseek-flash`；模型轮次 8/15；工具调用 14/40；finish 被退回 0 次
- 任务状态：**needs_confirmation**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-E1DC4F7C", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M03"} | ✅ 找到 M03《社区咖啡馆探店》，license=缺失 | 需要读取 M03 的元数据以确定渠道、版权与授权信息 | get_material |
| 2 | 1 | `get_material` | {"material_id": "M05"} | ✅ 找到 M05《用户投稿：第一次带娃露营》，license=缺失 | 需要读取 M05 的元数据以确定渠道、版权与授权信息 | get_material |
| 3 | 1 | `get_material` | {"material_id": "M08"} | ✅ 找到 M08《五分钟快手早餐合集》，license=有 | 需要读取 M08 的元数据，且该请求缺少发布时间，需确认可用信息 | check_rules |
| 4 | 2 | `check_rules` | {"material_id": "M03", "publish_at": "2026-11-06T12:00"} | ✅ M03 审核 incomplete：R01[missing] 缺少必填字段 license；可查询版权登记库补查 | 按用户要求时段对 M03 做抖音 2026-11-06 12:00 的审核校验 | check_rules |
| 5 | 2 | `check_rules` | {"material_id": "M05", "publish_at": "2026-11-06T15:00"} | ✅ M05 审核 incomplete：R01[missing] 缺少必填字段 owner；R01[missing] 缺少必填字段 license；可查询版权登记库补查；R03[missing] 使用了背景音乐但缺少音乐授权编号；R07[review] 出镜人物肖像授权未提供 | 按用户要求时段对 M05 做抖音 2026-11-06 15:00 的审核校验 | lookup_license |
| 6 | 3 | `lookup_license` | {"material_id": "M03"} | ✅ 登记库命中 CR-5531（original，持有方 内容组C，到期 2027-06-30） | M03 审核结果为 incomplete 且提示可用于补查 license，先查版权登记库 | lookup_license |
| 7 | 3 | `lookup_license` | {"material_id": "M05"} | ✅ 登记库无 M05 的版权记录 | M05 审核结果为 incomplete 且提示可用于补查 license，先查版权登记库 | check_rules |
| 8 | 4 | `check_rules` | {"material_id": "M03", "publish_at": "2026-11-06T12:00"} | ✅ M03 审核 pass，版权信息来自登记库补查 | M03 已通过 lookup_license 查到 CR-5531 原件登记记录，重新检查以确认结论 | query_slots |
| 9 | 5 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-06T12:00"} | ✅ douyin 2026-11-06T12:00 free | M03 复核已经 pass，现在确认用户指定的抖音 2026-11-06 12:00 时段是否可用 | query_slots |
| 10 | 5 | `query_slots` | {"channel": "xiaohongshu", "publish_at": "2026-11-06T12:00", "also_taken": [{"channel": "douyin", "slot": "2026-11-06T12:00"}]} | ✅ xiaohongshu 2026-11-06T12:00 free | M08 未给发布时间，先在小红书 2026-11-06 12:00 试探可用性，以便给出建议时段 | check_rules |
| 11 | 5 | `check_rules` | {"material_id": "M08", "publish_at": "2026-11-06T12:00"} | ✅ M08 审核 pass | M08 元数据完整（原创授权、无出镜人物、无音乐），先按候选时段做规则检查 | query_slots |
| 12 | 6 | `query_slots` | {"also_taken": [{"channel": "douyin", "slot": "2026-11-06T12:00"}, {"channel": "xiaohongshu", "slot": "2026-11-06T12:00"}], "channel": "douyin", "publish_at": "2026-11-06T15:00"} | ✅ douyin 2026-11-06T15:00 free | 确认 M05 原要求的抖音 15:00 是否空闲，以便资料补齐后能按原时段排期 | save_schedule_draft |
| 13 | 7 | `save_schedule_draft` | {"items": [{"material_id": "M03", "channel": "douyin", "slot": "2026-11-06T12:00", "confirmation_status": "not_required"}, {"material_id": "M08", "channel": "xiaohongshu", "slot": "2026-11-06T12:00", "confirmation_status": "pending", "note": "请求未提供发布时间，草稿暂按建议时段 2026-11-06 12:00（该时段空闲）占位，待用户确认具体发布时间"}]} | ✅ 草稿 D-E1DC4F7C created（修订 1，2 条，未发布） | M03 复核 pass 且原时段空闲可保持；M08 检查 pass 但缺发布时间，按建议时段 pending 占位；M05 资料缺失不纳入草稿 | finish |
| 14 | 8 | `finish` | {"items": [{"material_id": "M03", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-06T12:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}, {"material_id": "M05", "review_status": "needs_info", "risk_reasons": ["缺少必填字段 owner（素材归属人）", "缺少必填字段 license，版权登记库中未查到登记记录", "使用了背景音乐但缺少音乐授权编号 music.license_id", "出镜人物肖像授权 portrait_release 未提供，需人工复核"], "suggested_channel": "douyin", "suggested_slot": "2026-11-06T15:00", "confirmation_status": "not_applicable", "pending_items": ["补充素材归属人 owner", "补充版权授权信息或登记编号（版权登记库查无记录）", "补充背景音乐授权编号 MUS-*", "补交出镜人物肖像授权（portrait_release）"], "in_draft": false}, {"material_id": "M08", "review_status": "pass", "risk_reasons": [], "suggested_channel": "xiaohongshu", "suggested_slot": "2026-11-06T12:00", "confirmation_status": "pending", "pending_items": ["请求未提供发布时间，需确认是否按建议时段 2026-11-06 12:00 在小红书发布"], "in_draft": true}], "summary": "已生成排期草稿 D-E1DC4F7C（rev 1，2 条，仅草稿未发布）。M03：首次检查缺 license 判 incomplete，查版权登记库得到 CR-5531（原创，持有人内容组C，有效期至 2027-06-30），重检 pass，按原要求抖音 2026-11-06 12:00 排入。M08：规则检查 pass，但请求未给发布时间，草稿暂按建议时段小红书 2026-11-06 12:00 占位（该时段空闲），状态 pending 待用户确认。M05：仍为资料缺失（缺 owner、缺版权授权且登记库无记录、背景音乐无授权编号、肖像授权未提供），补查无果，未纳入草稿；其原要求的抖音 2026-11-06 15:00 目前空闲，补齐资料后可沿用该时段。需注意：以上均为草稿，未发布上线。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M03 | pass | — | — | douyin 2026-11-06T12:00 | douyin 2026-11-06T12:00 | not_required | — | saved |
| M05 | needs_info | ["缺少必填字段 owner（素材归属人）", "缺少必填字段 license，版权登记库中未查到登记记录", "使用了背景音乐但缺少音乐授权编号 music.license_id", "出镜人物肖像授权 portrait_release 未提供，需人工复核"] | ["R01[missing] owner", "R01[missing] license", "R03[missing] music.license_id", "R07[review] portrait_release"] | douyin 2026-11-06T15:00 | douyin 2026-11-06T15:00 | not_applicable | ["补充素材归属人 owner", "补充版权授权信息或登记编号（版权登记库查无记录）", "补充背景音乐授权编号 MUS-*", "补交出镜人物肖像授权（portrait_release）"] | not_saved |
| M08 | pass | — | — | xiaohongshu 未提供时间 | xiaohongshu 2026-11-06T12:00 | pending | ["请求未提供发布时间，需确认是否按建议时段 2026-11-06 12:00 在小红书发布"] | saved |

**模型总结**：已生成排期草稿 D-E1DC4F7C（rev 1，2 条，仅草稿未发布）。M03：首次检查缺 license 判 incomplete，查版权登记库得到 CR-5531（原创，持有人内容组C，有效期至 2027-06-30），重检 pass，按原要求抖音 2026-11-06 12:00 排入。M08：规则检查 pass，但请求未给发布时间，草稿暂按建议时段小红书 2026-11-06 12:00 占位（该时段空闲），状态 pending 待用户确认。M05：仍为资料缺失（缺 owner、缺版权授权且登记库无记录、背景音乐无授权编号、肖像授权未提供），补查无果，未纳入草稿；其原要求的抖音 2026-11-06 15:00 目前空闲，补齐资料后可沿用该时段。需注意：以上均为草稿，未发布上线。
