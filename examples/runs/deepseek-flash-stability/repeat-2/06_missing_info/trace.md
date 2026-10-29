# 06_missing_info · 素材信息缺失

- 输入：`examples/inputs/06_missing_info.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/06_missing_info.json --provider deepseek --store .runtime/s06.json`
- 模型：`deepseek-flash`；模型轮次 6/15；工具调用 13/40；finish 被退回 0 次
- 任务状态：**needs_confirmation**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-E1DC4F7C", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M03"} | ✅ 找到 M03《社区咖啡馆探店》，license=缺失 | 需要读取 M03 元数据以进行审核与排期。 | get_material |
| 2 | 1 | `get_material` | {"material_id": "M05"} | ✅ 找到 M05《用户投稿：第一次带娃露营》，license=缺失 | 需要读取 M05 元数据以进行审核与排期。 | get_material |
| 3 | 1 | `get_material` | {"material_id": "M08"} | ✅ 找到 M08《五分钟快手早餐合集》，license=有 | 需要读取 M08 元数据以进行审核与排期。 | check_rules |
| 4 | 2 | `check_rules` | {"material_id": "M03", "publish_at": "2026-11-06T12:00"} | ✅ M03 审核 incomplete：R01[missing] 缺少必填字段 license；可查询版权登记库补查 | M03 元数据 license 为空，先按请求时段跑一遍审核规则确认缺什么。 | check_rules |
| 5 | 2 | `check_rules` | {"material_id": "M05", "publish_at": "2026-11-06T15:00"} | ✅ M05 审核 incomplete：R01[missing] 缺少必填字段 owner；R01[missing] 缺少必填字段 license；可查询版权登记库补查；R03[missing] 使用了背景音乐但缺少音乐授权编号；R07[review] 出镜人物肖像授权未提供 | M05 为视频投稿，需按请求时段核对授权与肖像等规则。 | check_rules |
| 6 | 2 | `check_rules` | {"material_id": "M08"} | ✅ M08 审核 pass | M08 请求缺少发布时间，先不带时段做一次基础规则检查。 | lookup_license |
| 7 | 3 | `lookup_license` | {"material_id": "M03"} | ✅ 登记库命中 CR-5531（original，持有方 内容组C，到期 2027-06-30） | check_rules 提示 M03 缺少 license 且可查版权登记库补查。 | lookup_license |
| 8 | 3 | `lookup_license` | {"material_id": "M05"} | ✅ 登记库无 M05 的版权记录 | check_rules 提示 M05 缺少 license 可补查，同时确认能否补到音乐与投稿授权信息。 | query_slots |
| 9 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-06T12:00"} | ✅ douyin 2026-11-06T12:00 free | M03 需要按用户要求的 2026-11-06 12:00 抖音时段查可用性。 | query_slots |
| 10 | 3 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-06T15:00"} | ✅ douyin 2026-11-06T15:00 free | M05 需要按用户要求的 2026-11-06 15:00 抖音时段查可用性。 | check_rules |
| 11 | 4 | `check_rules` | {"material_id": "M03", "publish_at": "2026-11-06T12:00"} | ✅ M03 审核 pass，版权信息来自登记库补查 | 已通过 lookup_license 查到 M03 的版权登记记录（CR-5531，有效至 2027-06-30），按规则需重新检查。 | save_schedule_draft |
| 12 | 5 | `save_schedule_draft` | {"items": [{"material_id": "M03", "channel": "douyin", "slot": "2026-11-06T12:00", "confirmation_status": "not_required"}]} | ✅ 草稿 D-E1DC4F7C created（修订 1，1 条，未发布） | M03 补查版权登记后复核为 pass，且 2026-11-06 12:00 抖音时段空闲、与用户要求一致；M05 资料缺失、M08 缺发布时间，均不进草稿。 | finish |
| 13 | 6 | `finish` | {"items": [{"material_id": "M03", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-06T12:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}, {"material_id": "M05", "review_status": "needs_info", "risk_reasons": ["缺少必填字段 owner（素材归属人）", "缺少必填字段 license，且版权登记库未查到该素材登记记录，无法补查", "使用背景音乐但缺少音乐授权编号 music.license_id", "出镜人物肖像授权 portrait_release 未提供，需人工复核"], "suggested_channel": "douyin", "suggested_slot": null, "confirmation_status": "pending", "pending_items": ["补充素材归属人 owner", "补充版权授权信息（版权登记库无记录，需提供授权文件或原创声明）", "补充背景音乐授权编号 music.license_id", "补充出镜人物肖像授权 portrait_release，或改为修版移除可识别人物", "以上资料补齐后需重新审核，原定 2026-11-06 15:00 抖音时段将重新确认"], "in_draft": false}, {"material_id": "M08", "review_status": "pass", "risk_reasons": [], "suggested_channel": "xiaohongshu", "suggested_slot": null, "confirmation_status": "pending", "pending_items": ["请求未给出小红书发布时间，请指定具体整点时段（08:00–23:00），确认后再校验时段可用性并入草稿"], "in_draft": false}], "summary": "本批 3 个素材：M03 版权信息缺失，经版权登记库补查（CR-5531，有效至 2027-06-30）后复核通过，抖音 2026-11-06 12:00 时段空闲，已按用户要求写入排期草稿（草稿 D-E1DC4F7C，仅草稿未发布）。M05 为资料缺失：owner、license（登记库无记录）、音乐授权编号、肖像授权均缺，需补充后才能排期，暂不入草稿，原定 15:00 抖音时段待资料补齐后重新确认。M08 内容审核通过，但请求未给发布时间，需用户指定整点时段后再排入小红书；未自行编造时段。所有结果仅为草稿，未发布任何内容。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M03 | pass | — | — | douyin 2026-11-06T12:00 | douyin 2026-11-06T12:00 | not_required | — | saved |
| M05 | needs_info | ["缺少必填字段 owner（素材归属人）", "缺少必填字段 license，且版权登记库未查到该素材登记记录，无法补查", "使用背景音乐但缺少音乐授权编号 music.license_id", "出镜人物肖像授权 portrait_release 未提供，需人工复核"] | ["R01[missing] owner", "R01[missing] license", "R03[missing] music.license_id", "R07[review] portrait_release"] | douyin 2026-11-06T15:00 | douyin | pending | ["补充素材归属人 owner", "补充版权授权信息（版权登记库无记录，需提供授权文件或原创声明）", "补充背景音乐授权编号 music.license_id", "补充出镜人物肖像授权 portrait_release，或改为修版移除可识别人物", "以上资料补齐后需重新审核，原定 2026-11-06 15:00 抖音时段将重新确认"] | not_saved |
| M08 | pass | — | — | xiaohongshu 未提供时间 | xiaohongshu | pending | ["请求未给出小红书发布时间，请指定具体整点时段（08:00–23:00），确认后再校验时段可用性并入草稿"] | not_saved |

**模型总结**：本批 3 个素材：M03 版权信息缺失，经版权登记库补查（CR-5531，有效至 2027-06-30）后复核通过，抖音 2026-11-06 12:00 时段空闲，已按用户要求写入排期草稿（草稿 D-E1DC4F7C，仅草稿未发布）。M05 为资料缺失：owner、license（登记库无记录）、音乐授权编号、肖像授权均缺，需补充后才能排期，暂不入草稿，原定 15:00 抖音时段待资料补齐后重新确认。M08 内容审核通过，但请求未给发布时间，需用户指定整点时段后再排入小红书；未自行编造时段。所有结果仅为草稿，未发布任何内容。
