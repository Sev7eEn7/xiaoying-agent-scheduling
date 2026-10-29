# 06_missing_info · 素材信息缺失

- 输入：`examples/inputs/06_missing_info.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/06_missing_info.json --provider deepseek --store .runtime/s06.json`
- 模型：`deepseek-flash`；模型轮次 7/15；工具调用 13/40；finish 被退回 0 次
- 任务状态：**needs_confirmation**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-E1DC4F7C", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M03"} | ✅ 找到 M03《社区咖啡馆探店》，license=缺失 | 请求要求排期 M03，先读取素材元数据以确认渠道与授权信息。 | get_material |
| 2 | 1 | `get_material` | {"material_id": "M05"} | ✅ 找到 M05《用户投稿：第一次带娃露营》，license=缺失 | 请求要求排期 M05，先读取素材元数据以确认渠道与授权信息。 | get_material |
| 3 | 1 | `get_material` | {"material_id": "M08"} | ✅ 找到 M08《五分钟快手早餐合集》，license=有 | 请求要求排期 M08 但未给时间，读取元数据以了解素材情况。 | check_rules |
| 4 | 2 | `check_rules` | {"material_id": "M03", "publish_at": "2026-11-06T12:00"} | ✅ M03 审核 incomplete：R01[missing] 缺少必填字段 license；可查询版权登记库补查 | 按用户要求的 2026-11-06T12:00 抖音时段检查 M03 的审核规则。 | check_rules |
| 5 | 2 | `check_rules` | {"material_id": "M05", "publish_at": "2026-11-06T15:00"} | ✅ M05 审核 incomplete：R01[missing] 缺少必填字段 owner；R01[missing] 缺少必填字段 license；可查询版权登记库补查；R03[missing] 使用了背景音乐但缺少音乐授权编号；R07[review] 出镜人物肖像授权未提供 | 按用户要求的 2026-11-06T15:00 抖音时段检查 M05 的审核规则。 | check_rules |
| 6 | 2 | `check_rules` | {"material_id": "M08"} | ✅ M08 审核 pass | 请求未给 M08 时间，先不带时段检查素材本身是否有合规问题。 | lookup_license |
| 7 | 3 | `lookup_license` | {"material_id": "M03"} | ✅ 登记库命中 CR-5531（original，持有方 内容组C，到期 2027-06-30） | check_rules 显示 M03 缺少 license 字段，按规则先到版权登记库补查。 | lookup_license |
| 8 | 3 | `lookup_license` | {"material_id": "M05"} | ✅ 登记库无 M05 的版权记录 | check_rules 显示 M05 缺少 license 字段，按规则先到版权登记库补查。 | check_rules |
| 9 | 4 | `check_rules` | {"material_id": "M03", "publish_at": "2026-11-06T12:00"} | ✅ M03 审核 pass，版权信息来自登记库补查 | 已查到 M03 的版权登记记录 CR-5531，需带上该记录重新检查规则。 | check_rules |
| 10 | 4 | `check_rules` | {"material_id": "M05", "publish_at": "2026-11-06T15:00"} | ✅ M05 审核 incomplete：R01[missing] 缺少必填字段 owner；R01[missing] 缺少必填字段 license；可查询版权登记库补查；R03[missing] 使用了背景音乐但缺少音乐授权编号；R07[review] 出镜人物肖像授权未提供 | 版权登记库未查到 M05 记录，确认补查后规则检查结果是否仍为 incomplete。 | query_slots |
| 11 | 5 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-06T12:00"} | ✅ douyin 2026-11-06T12:00 free | M03 补查版权后已 pass，检查用户要求的抖音 11-06 12:00 时段是否可用。 | save_schedule_draft |
| 12 | 6 | `save_schedule_draft` | {"items": [{"material_id": "M03", "channel": "douyin", "slot": "2026-11-06T12:00", "confirmation_status": "not_required", "note": "与用户指定渠道和时段一致，抖音该时段空闲"}]} | ✅ 草稿 D-E1DC4F7C created（修订 1，1 条，未发布） | M03 补查版权登记 CR-5531 后 check_rules 为 pass 且抖音 11-06 12:00 空闲，M05 与 M08 分别因资料缺失和缺时间不入草稿。 | finish |
| 13 | 7 | `finish` | {"items": [{"material_id": "M03", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-06T12:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}, {"material_id": "M05", "review_status": "needs_info", "risk_reasons": ["缺少必填字段 owner（素材归属人）", "缺少必填字段 license，版权登记库补查无记录", "使用了背景音乐但缺少音乐授权编号 music.license_id", "出镜人物肖像授权 portrait_release 未提供，需人工复核"], "suggested_channel": "douyin", "suggested_slot": "2026-11-06T15:00", "confirmation_status": "pending", "pending_items": ["补充素材归属人 owner", "提供或确认版权授权信息（登记库未查到，需补充 license 记录）", "补充背景音乐授权编号 MUS 编号", "补交出镜人物肖像授权文件，并安排人工复核", "以上资料补齐前，抖音 2026-11-06T15:00 时段仅为暂留建议，需确认"], "in_draft": false}, {"material_id": "M08", "review_status": "pass", "risk_reasons": [], "suggested_channel": "xiaohongshu", "suggested_slot": null, "confirmation_status": "pending", "pending_items": ["请求未给出发布时间，请确认小红书的具体发布时段（08:00–23:00 整点）"], "in_draft": false}], "summary": "本批仅 M03 可排期：版权字段缺失已通过版权登记库补查（CR-5531，有效期至 2027-06-30），check_rules 转为 pass，抖音 2026-11-06T12:00 时段空闲，已按原要求写入排期草稿 D-E1DC4F7C（仅为草稿，未发布）。M05 补查版权登记库无记录，且缺 owner、音乐授权编号、肖像授权，判定 needs_info，未入草稿，需补齐资料后重新审核；其 11-06 15:00 时段仅为建议，待确认。M08 素材本身规则 pass，但请求未给发布时间，无法排期，请补充具体时段后再排。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M03 | pass | — | — | douyin 2026-11-06T12:00 | douyin 2026-11-06T12:00 | not_required | — | saved |
| M05 | needs_info | ["缺少必填字段 owner（素材归属人）", "缺少必填字段 license，版权登记库补查无记录", "使用了背景音乐但缺少音乐授权编号 music.license_id", "出镜人物肖像授权 portrait_release 未提供，需人工复核"] | ["R01[missing] owner", "R01[missing] license", "R03[missing] music.license_id", "R07[review] portrait_release"] | douyin 2026-11-06T15:00 | douyin 2026-11-06T15:00 | pending | ["补充素材归属人 owner", "提供或确认版权授权信息（登记库未查到，需补充 license 记录）", "补充背景音乐授权编号 MUS 编号", "补交出镜人物肖像授权文件，并安排人工复核", "以上资料补齐前，抖音 2026-11-06T15:00 时段仅为暂留建议，需确认"] | not_saved |
| M08 | pass | — | — | xiaohongshu 未提供时间 | xiaohongshu | pending | ["请求未给出发布时间，请确认小红书的具体发布时段（08:00–23:00 整点）"] | not_saved |

**模型总结**：本批仅 M03 可排期：版权字段缺失已通过版权登记库补查（CR-5531，有效期至 2027-06-30），check_rules 转为 pass，抖音 2026-11-06T12:00 时段空闲，已按原要求写入排期草稿 D-E1DC4F7C（仅为草稿，未发布）。M05 补查版权登记库无记录，且缺 owner、音乐授权编号、肖像授权，判定 needs_info，未入草稿，需补齐资料后重新审核；其 11-06 15:00 时段仅为建议，待确认。M08 素材本身规则 pass，但请求未给发布时间，无法排期，请补充具体时段后再排。
