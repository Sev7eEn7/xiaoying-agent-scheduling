# 场景验收汇总（provider=mock，模型 mock-rule-policy）

共 11 个场景，检查项通过 103/103。每个场景目录下有 report.json、trace.md、trace.json、messages.json（原始模型输入输出）、drafts_after.json、checks.json。

| 场景 | 覆盖验收点 | task_status | 模型轮次 | 工具调用 | finish 退回 | 检查 | 未通过 |
|---|---|---|---|---|---|---|---|
| [01_normal](01_normal/trace.md) 正常排期 | 正常排期 | completed | 8 | 8 | 0 | 13/13 | — |
| [02_conflict](02_conflict/trace.md) 时段冲突（参考实例） | 时段冲突、确认边界 | needs_confirmation | 5 | 5 | 0 | 11/11 | — |
| [03_duplicate](03_duplicate/trace.md) 重复提交同一请求 | 重复提交 | needs_confirmation | 5 | 5 | 0 | 9/9 | — |
| [04_confirm](04_confirm/trace.md) 用户确认后再次提交 | 确认边界、重复提交 | completed | 5 | 5 | 0 | 9/9 | — |
| [05_swap_resubmit](05_swap_resubmit/trace.md) 更换占用时段后重复提交 | 时段冲突、重复提交 | completed | 5 | 5 | 0 | 9/9 | — |
| [06_missing_info](06_missing_info/trace.md) 素材信息缺失 | 素材信息缺失、补查 | needs_confirmation | 12 | 12 | 0 | 15/15 | — |
| [07_rule_risk](07_rule_risk/trace.md) 规则风险：阻断与人工复核 | 规则风险 | needs_confirmation | 7 | 7 | 0 | 10/10 | — |
| [08_save_fail](08_save_fail/trace.md) 保存失败 | 保存失败、工具失败 | save_failed | 7 | 7 | 0 | 7/7 | — |
| [09_batch_window](09_batch_window/trace.md) 同批次冲突 + 用户允许窗口 | 时段冲突、确认边界、正常排期 | completed | 8 | 8 | 0 | 10/10 | — |
| [10_step_limit](10_step_limit/trace.md) 达到步数上限 | 步数上限 | incomplete | 3 | 3 | 0 | 3/3 | — |
| [11_tool_retry](11_tool_retry/trace.md) 工具首次失败后重试 | 工具失败 | completed | 6 | 6 | 0 | 7/7 | — |
