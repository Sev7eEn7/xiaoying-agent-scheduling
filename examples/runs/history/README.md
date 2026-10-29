# 开发历史记录（非提交结果）

这里保留的是开发早期用 **`deepseek-chat`** 跑出的记录，用来佐证 [docs/05-retrospective.md](../../../docs/05-retrospective.md) 中“真实模型暴露的问题与修复”。候选人随后要求只使用 Flash 模型，因此**提交结果以 [../deepseek-flash/](../deepseek-flash/) 为准**。

| 目录 | 内容 |
|---|---|
| `deepseek-chat-round1/` | 第 1 轮完整回放，7/11：暴露了判重受 note 影响（03→04、05 连带失败）和 task_status 依赖自由文本（09） |
| `deepseek-chat-round2-09_batch_window/`、`deepseek-chat-round2-summary.md` | 第 2 轮，10/11：09 中模型改动了没有窗口的 M09（已正确标记 pending，但不是最优） |
| `deepseek-chat-round3/` | 第 3 轮，11/11（加入通用冲突策略之后） |

这些记录生成之后，代码有过修改（判重字段、task_status 计算、schema 描述、提示词中的冲突策略），所以它们不能代表当前代码的行为。
