# 10_step_limit · 达到步数上限

- 输入：`examples/inputs/06_missing_info.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/06_missing_info.json --provider deepseek --store .runtime/s10.json --max-turns 3`
- 模型：`deepseek-flash`；模型轮次 3/3；工具调用 8/40；finish 被退回 0 次
- 任务状态：**incomplete**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "not_attempted", "draft_id": null, "attempts": 0}
- 未完成原因：STEP_LIMIT_REACHED: 已达到模型轮次上限 3，任务未完成

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M03"} | ✅ 找到 M03《社区咖啡馆探店》，license=缺失 | 需要读取 M03 元数据以进行审核与排期 | get_material |
| 2 | 1 | `get_material` | {"material_id": "M05"} | ✅ 找到 M05《用户投稿：第一次带娃露营》，license=缺失 | 需要读取 M05 元数据以进行审核与排期 | get_material |
| 3 | 1 | `get_material` | {"material_id": "M08"} | ✅ 找到 M08《五分钟快手早餐合集》，license=有 | 需要读取 M08 元数据以确认渠道与时间要求 | check_rules |
| 4 | 2 | `check_rules` | {"material_id": "M03", "publish_at": "2026-11-06T12:00"} | ✅ M03 审核 incomplete：R01[missing] 缺少必填字段 license；可查询版权登记库补查 | M03 元数据缺失 license，需按 12:00 排期校验授权有效期与审核规则 | check_rules |
| 5 | 2 | `check_rules` | {"material_id": "M05", "publish_at": "2026-11-06T15:00"} | ✅ M05 审核 incomplete：R01[missing] 缺少必填字段 owner；R01[missing] 缺少必填字段 license；可查询版权登记库补查；R03[missing] 使用了背景音乐但缺少音乐授权编号；R07[review] 出镜人物肖像授权未提供 | M05 元数据缺失 license 与肖像授权，需按 15:00 排期校验审核规则 | check_rules |
| 6 | 2 | `check_rules` | {"material_id": "M08", "publish_at": "2026-10-31T10:00"} | ✅ M08 审核 pass | M08 请求未给发布时间，先用一个占位整点做规则校验，仅用于审核判定 | lookup_license |
| 7 | 3 | `lookup_license` | {"material_id": "M03"} | ✅ 登记库命中 CR-5531（original，持有方 内容组C，到期 2027-06-30） | M03 审核结果为 incomplete（缺少 license），按规则先补查版权登记库 | lookup_license |
| 8 | 3 | `lookup_license` | {"material_id": "M05"} | ✅ 登记库无 M05 的版权记录 | M05 审核结果为 incomplete（缺少 license），按规则先补查版权登记库 | 停止 |
| — | 3 | **停止** | — | STEP_LIMIT_REACHED: 已达到模型轮次上限 3，任务未完成 | — | — |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M03 | needs_info | ["缺少必填字段 license；可查询版权登记库补查"] | ["R01[missing] license"] | douyin 2026-11-06T12:00 | — | unknown | — | not_saved |
| M05 | needs_info | ["缺少必填字段 owner", "缺少必填字段 license；可查询版权登记库补查", "使用了背景音乐但缺少音乐授权编号", "出镜人物肖像授权未提供"] | ["R01[missing] owner", "R01[missing] license", "R03[missing] music.license_id", "R07[review] portrait_release"] | douyin 2026-11-06T15:00 | — | unknown | — | not_saved |
| M08 | pass | — | — | xiaohongshu 未提供时间 | — | unknown | — | not_saved |
