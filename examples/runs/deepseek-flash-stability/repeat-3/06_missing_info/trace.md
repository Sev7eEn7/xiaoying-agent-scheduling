# 06_missing_info · 素材信息缺失

- 输入：`examples/inputs/06_missing_info.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/06_missing_info.json --provider deepseek --store .runtime/s06.json`
- 模型：`deepseek-flash`；模型轮次 7/15；工具调用 15/40；finish 被退回 1 次
- 任务状态：**needs_confirmation**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-E1DC4F7C", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M03"} | ✅ 找到 M03《社区咖啡馆探店》，license=缺失 | 请求要求为 M03 排期，先读取素材元数据 | get_material |
| 2 | 1 | `get_material` | {"material_id": "M05"} | ✅ 找到 M05《用户投稿：第一次带娃露营》，license=缺失 | 请求要求为 M05 排期，先读取素材元数据 | get_material |
| 3 | 1 | `get_material` | {"material_id": "M08"} | ✅ 找到 M08《五分钟快手早餐合集》，license=有 | 请求要求为 M08 排期，先读取素材元数据 | check_rules |
| 4 | 2 | `check_rules` | {"material_id": "M03", "publish_at": "2026-11-06T12:00"} | ✅ M03 审核 incomplete：R01[missing] 缺少必填字段 license；可查询版权登记库补查 | 按请求的抖音 11-06 12:00 时段审核 M03 的合规与授权有效期 | check_rules |
| 5 | 2 | `check_rules` | {"material_id": "M05", "publish_at": "2026-11-06T15:00"} | ✅ M05 审核 incomplete：R01[missing] 缺少必填字段 owner；R01[missing] 缺少必填字段 license；可查询版权登记库补查；R03[missing] 使用了背景音乐但缺少音乐授权编号；R07[review] 出镜人物肖像授权未提供 | 按请求的抖音 11-06 15:00 时段审核 M05，确认是否为资料缺失 | lookup_license |
| 6 | 2 | `lookup_license` | {"material_id": "M05"} | ✅ 登记库无 M05 的版权记录 | M05 元数据中版权与音乐授权信息为空，先查版权登记库补查 | check_rules |
| 7 | 2 | `check_rules` | {"material_id": "M08"} | ✅ M08 审核 pass | M08 未给出发布时间，先审核其内容合规性，再决定时段 | query_slots |
| 8 | 2 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-06T12:00"} | ✅ douyin 2026-11-06T12:00 free | M03 要求抖音 11-06 12:00，先确认该整点是否可用 | query_slots |
| 9 | 2 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-06T15:00"} | ✅ douyin 2026-11-06T15:00 free | M05 要求抖音 11-06 15:00，先确认该整点是否可用 | lookup_license |
| 10 | 3 | `lookup_license` | {"material_id": "M03"} | ✅ 登记库命中 CR-5531（original，持有方 内容组C，到期 2027-06-30） | M03 审核为 incomplete 且提示可查版权登记库，执行补查后需重新审核 | check_rules |
| 11 | 4 | `check_rules` | {"material_id": "M03", "publish_at": "2026-11-06T12:00"} | ✅ M03 审核 pass，版权信息来自登记库补查 | 已查到 M03 版权登记记录（CR-5531，有效期至 2027-06-30），重新审核该时段是否通过 | query_slots |
| 12 | 4 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-06T12:00", "also_taken": []} | ✅ douyin 2026-11-06T12:00 free | 再次确认 M03 的抖音 11-06 12:00 在本批次规划下仍可用 | save_schedule_draft |
| 13 | 5 | `save_schedule_draft` | {"items": [{"material_id": "M03", "channel": "douyin", "slot": "2026-11-06T12:00", "confirmation_status": "not_required"}]} | ✅ 草稿 D-E1DC4F7C created（修订 1，1 条，未发布） | M03 补查版权登记后审核通过，抖音 11-06 12:00 空闲且与用户要求一致；M05、M08 尚不具备排期条件，不纳入草稿 | finish |
| 14 | 6 | `finish` | {"items": [{"material_id": "M03", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-06T12:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}, {"material_id": "M05", "review_status": "needs_info", "risk_reasons": ["缺少必填字段 owner（素材归属方未知，用户投稿来源无法核实）", "缺少必填字段 license，且版权登记库补查无记录（lookup_license found=false）", "使用了背景音乐但缺少音乐授权编号 music.license_id 及到期时间", "出镜人物肖像授权 portrait_release 未提供，需人工复核"], "suggested_channel": "douyin", "suggested_slot": null, "confirmation_status": "pending", "pending_items": ["补充素材归属方 owner 与版权授权信息", "补充背景音乐授权编号及有效期", "补充出镜人物肖像授权（或删除出镜人物画面）", "资料补齐后需重新审核，才能确认 2026-11-06 15:00 抖音时段（该时段当前空闲）"], "in_draft": false}, {"material_id": "M08", "review_status": "pass", "risk_reasons": [], "suggested_channel": "xiaohongshu", "suggested_slot": null, "confirmation_status": "pending", "pending_items": ["请求未给出发布时间：请确认小红书的具体发布日期与整点时段，确认后再校验占用并排期"], "in_draft": false}], "summary": "本批次仅 M03 可排期：补查版权登记库得到记录 CR-5531（权利人内容组C，有效期至 2027-06-30）后审核通过，抖音 2026-11-06 12:00 空闲，已按用户要求并入草稿 D-E1DC4F7C（revision 1，仅草稿，未发布）。M05 审核为资料缺失：owner 与 license 为空且版权库无记录、背景音乐无授权编号、肖像授权缺失，补查无果，不进入草稿，需补齐信息后重新审核。M08 内容审核通过（原创、无人物），但请求未提供发布时间，无法排期，待确认具体时段后可补入同一草稿。请勿将本次操作理解为已发布。"} | ❌ 失败 REPORT_REJECTED：finish 与工具记录不一致，请修正后重新提交；输出中出现“已发布/上线/发布成功”等表述；本系统只保存草稿，不能声称发布 | — | finish |
| 15 | 7 | `finish` | {"items": [{"confirmation_status": "not_required", "in_draft": true, "material_id": "M03", "pending_items": [], "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-06T12:00"}, {"confirmation_status": "pending", "in_draft": false, "material_id": "M05", "pending_items": ["补充素材归属方 owner 与版权授权信息", "补充背景音乐授权编号及有效期", "补充出镜人物肖像授权（或删除出镜人物画面）", "资料补齐后需重新审核，才能确认 2026-11-06 15:00 抖音时段（该时段当前空闲）"], "review_status": "needs_info", "risk_reasons": ["缺少必填字段 owner（素材归属方未知，用户投稿来源无法核实）", "缺少必填字段 license，且版权登记库补查无记录（lookup_license found=false）", "使用了背景音乐但缺少音乐授权编号 music.license_id 及到期时间", "出镜人物肖像授权 portrait_release 未提供，需人工复核"], "suggested_channel": "douyin", "suggested_slot": null}, {"confirmation_status": "pending", "in_draft": false, "material_id": "M08", "pending_items": ["请求未给出发布时间：请确认小红书的具体发布日期与整点时段，确认后再校验占用并排期"], "review_status": "pass", "risk_reasons": [], "suggested_channel": "xiaohongshu", "suggested_slot": null}], "summary": "本批次仅 M03 可排期：补查版权登记库得到记录 CR-5531（权利人内容组C，有效期至 2027-06-30）后审核通过，抖音 2026-11-06 12:00 空闲，已按用户要求写入草稿 D-E1DC4F7C（revision 1，草稿状态，未对外推送）。M05 审核为资料缺失：owner 与 license 为空且版权库无记录、背景音乐无授权编号、肖像授权缺失，补查无果，不进入草稿，需补齐信息后重新审核。M08 内容审核通过（原创、无人物），但请求未提供时间，无法排期，待确认具体时段后可补入同一草稿。"} | ✅ finish 通过工具记录核对 | — | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M03 | pass | — | — | douyin 2026-11-06T12:00 | douyin 2026-11-06T12:00 | not_required | — | saved |
| M05 | needs_info | ["缺少必填字段 owner（素材归属方未知，用户投稿来源无法核实）", "缺少必填字段 license，且版权登记库补查无记录（lookup_license found=false）", "使用了背景音乐但缺少音乐授权编号 music.license_id 及到期时间", "出镜人物肖像授权 portrait_release 未提供，需人工复核"] | ["R01[missing] owner", "R01[missing] license", "R03[missing] music.license_id", "R07[review] portrait_release"] | douyin 2026-11-06T15:00 | douyin | pending | ["补充素材归属方 owner 与版权授权信息", "补充背景音乐授权编号及有效期", "补充出镜人物肖像授权（或删除出镜人物画面）", "资料补齐后需重新审核，才能确认 2026-11-06 15:00 抖音时段（该时段当前空闲）"] | not_saved |
| M08 | pass | — | — | xiaohongshu 未提供时间 | xiaohongshu | pending | ["请求未给出发布时间：请确认小红书的具体发布日期与整点时段，确认后再校验占用并排期"] | not_saved |

**模型总结**：本批次仅 M03 可排期：补查版权登记库得到记录 CR-5531（权利人内容组C，有效期至 2027-06-30）后审核通过，抖音 2026-11-06 12:00 空闲，已按用户要求写入草稿 D-E1DC4F7C（revision 1，草稿状态，未对外推送）。M05 审核为资料缺失：owner 与 license 为空且版权库无记录、背景音乐无授权编号、肖像授权缺失，补查无果，不进入草稿，需补齐信息后重新审核。M08 内容审核通过（原创、无人物），但请求未提供时间，无法排期，待确认具体时段后可补入同一草稿。
