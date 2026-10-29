# 06_missing_info · 素材信息缺失

- 输入：`examples/inputs/06_missing_info.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/06_missing_info.json --provider mock --store .runtime/s06.json`
- 模型：`mock-rule-policy`；模型轮次 12/15；工具调用 12/40；finish 被退回 0 次
- 任务状态：**needs_confirmation**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "created", "draft_id": "D-E1DC4F7C", "revision": 1, "attempts": 1, "state": "draft"}

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M03"} | ✅ 找到 M03《社区咖啡馆探店》，license=缺失 | 先读取素材元数据 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M03", "publish_at": "2026-11-06T12:00"} | ✅ M03 审核 incomplete：R01[missing] 缺少必填字段 license；可查询版权登记库补查 | 读取成功，按发布时间做规则检查 | lookup_license |
| 3 | 3 | `lookup_license` | {"material_id": "M03"} | ✅ 登记库命中 CR-5531（original，持有方 内容组C，到期 2027-06-30） | 版权信息缺失，先查登记库补查 | check_rules |
| 4 | 4 | `check_rules` | {"material_id": "M03", "publish_at": "2026-11-06T12:00"} | ✅ M03 审核 pass，版权信息来自登记库补查 | 登记库有记录，重新检查 | query_slots |
| 5 | 5 | `query_slots` | {"channel": "douyin", "publish_at": "2026-11-06T12:00", "also_taken": []} | ✅ douyin 2026-11-06T12:00 free | 审核可排期，查询目标时段 | get_material |
| 6 | 6 | `get_material` | {"material_id": "M05"} | ✅ 找到 M05《用户投稿：第一次带娃露营》，license=缺失 | 先读取素材元数据 | check_rules |
| 7 | 7 | `check_rules` | {"material_id": "M05", "publish_at": "2026-11-06T15:00"} | ✅ M05 审核 incomplete：R01[missing] 缺少必填字段 owner；R01[missing] 缺少必填字段 license；可查询版权登记库补查；R03[missing] 使用了背景音乐但缺少音乐授权编号；R07[review] 出镜人物肖像授权未提供 | 读取成功，按发布时间做规则检查 | lookup_license |
| 8 | 8 | `lookup_license` | {"material_id": "M05"} | ✅ 登记库无 M05 的版权记录 | 版权信息缺失，先查登记库补查 | get_material |
| 9 | 9 | `get_material` | {"material_id": "M08"} | ✅ 找到 M08《五分钟快手早餐合集》，license=有 | 先读取素材元数据 | check_rules |
| 10 | 10 | `check_rules` | {"material_id": "M08", "publish_at": null} | ✅ M08 审核 pass | 读取成功，按发布时间做规则检查 | save_schedule_draft |
| 11 | 11 | `save_schedule_draft` | {"items": [{"material_id": "M03", "channel": "douyin", "slot": "2026-11-06T12:00", "confirmation_status": "not_required", "note": ""}]} | ✅ 草稿 D-E1DC4F7C created（修订 1，1 条，未发布） | 所有素材处理完毕，保存可排期条目为草稿 | finish |
| 12 | 12 | `finish` | {"items": [{"material_id": "M03", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin", "suggested_slot": "2026-11-06T12:00", "confirmation_status": "not_required", "pending_items": [], "in_draft": true}, {"material_id": "M05", "review_status": "needs_info", "risk_reasons": [], "suggested_channel": null, "suggested_slot": null, "confirmation_status": "not_applicable", "pending_items": ["请补充：缺少必填字段 owner", "请补充：缺少必填字段 license；可查询版权登记库补查", "请补充：使用了背景音乐但缺少音乐授权编号"], "in_draft": false}, {"material_id": "M08", "review_status": "needs_info", "risk_reasons": [], "suggested_channel": null, "suggested_slot": null, "confirmation_status": "not_applicable", "pending_items": ["请求缺少发布时间或渠道，请提供"], "in_draft": false}], "summary": "共 3 个素材，1 个已保存为草稿；未发布任何内容。"} | ✅ finish 通过工具记录核对 | 全部素材已处理 | 结束 |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M03 | pass | — | — | douyin 2026-11-06T12:00 | douyin 2026-11-06T12:00 | not_required | — | saved |
| M05 | needs_info | — | ["R01[missing] owner", "R01[missing] license", "R03[missing] music.license_id", "R07[review] portrait_release"] | douyin 2026-11-06T15:00 | — | not_applicable | ["请补充：缺少必填字段 owner", "请补充：缺少必填字段 license；可查询版权登记库补查", "请补充：使用了背景音乐但缺少音乐授权编号"] | not_saved |
| M08 | needs_info | — | — | xiaohongshu 未提供时间 | — | not_applicable | ["请求缺少发布时间或渠道，请提供"] | not_saved |

**模型总结**：共 3 个素材，1 个已保存为草稿；未发布任何内容。
