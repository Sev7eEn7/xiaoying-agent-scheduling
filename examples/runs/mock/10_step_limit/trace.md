# 10_step_limit · 达到步数上限

- 输入：`examples/inputs/06_missing_info.json`
- 命令：`python3 -m scheduler_agent run examples/inputs/06_missing_info.json --provider mock --store .runtime/s10.json --max-turns 3`
- 模型：`mock-rule-policy`；模型轮次 3/3；工具调用 3/40；finish 被退回 0 次
- 任务状态：**incomplete**；发布状态：not_published（本 Agent 只保存排期草稿，不调用任何发布接口）
- 草稿：{"status": "not_attempted", "draft_id": null, "attempts": 0}
- 未完成原因：STEP_LIMIT_REACHED: 已达到模型轮次上限 3，任务未完成

## 执行步骤

| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |
|---|---|---|---|---|---|---|
| 1 | 1 | `get_material` | {"material_id": "M03"} | ✅ 找到 M03《社区咖啡馆探店》，license=缺失 | 先读取素材元数据 | check_rules |
| 2 | 2 | `check_rules` | {"material_id": "M03", "publish_at": "2026-11-06T12:00"} | ✅ M03 审核 incomplete：R01[missing] 缺少必填字段 license；可查询版权登记库补查 | 读取成功，按发布时间做规则检查 | lookup_license |
| 3 | 3 | `lookup_license` | {"material_id": "M03"} | ✅ 登记库命中 CR-5531（original，持有方 内容组C，到期 2027-06-30） | 版权信息缺失，先查登记库补查 | 停止 |
| — | 3 | **停止** | — | STEP_LIMIT_REACHED: 已达到模型轮次上限 3，任务未完成 | — | — |

## 最终结果

| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |
|---|---|---|---|---|---|---|---|---|
| M03 | needs_info | ["缺少必填字段 license；可查询版权登记库补查"] | ["R01[missing] license"] | douyin 2026-11-06T12:00 | — | unknown | — | not_saved |
| M05 | unknown | — | — | douyin 2026-11-06T15:00 | — | unknown | — | not_saved |
| M08 | unknown | — | — | xiaohongshu 未提供时间 | — | unknown | — | not_saved |
