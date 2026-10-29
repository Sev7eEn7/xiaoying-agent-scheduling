# 01 需求：用户、目标、范围与成功标准

题号：**1 · 素材审核与发布排期 Agent**

## 用户与场景

内容团队的排期运营。手里有一批素材（ID + 元数据），以及对每条素材的发布要求（渠道、时间，有时带一个可以接受的时间窗口）。他们需要知道每条素材：能不能发、有什么风险、应该排在哪个时段、还要谁确认什么。最终得到一份**无冲突、可确认的排期草稿**，再由人决定是否发布。

## 目标

| 目标 | 具体含义 |
|---|---|
| 找出待处理素材 | 每条素材给出审核状态：`pass` / `review`（需人工复核）/ `blocked`（阻断）/ `needs_info`（资料不足） |
| 解释风险 | 风险原因可追溯到规则编号和原文证据（如 R04 极限用语“最有效、100%”） |
| 无冲突排期 | 建议时段不与已有排期、其他请求的草稿占位、同批次其他素材冲突 |
| 可确认 | 改动用户要求的时段时只给“建议”并标记待确认；用户确认后再提交才能变成 `confirmed` |
| 只存草稿 | 只保存排期草稿，没有任何发布接口；保存状态如实反映工具结果 |

## 输入与材料

- 请求 JSON：`request_id`（幂等键，可选）、`items[]`（`material_id`、`channel`、`publish_at`、可选 `acceptable_window`）、可选 `confirmations[]`（用户对改期的确认）。样例见 [examples/inputs/](../examples/inputs/)。
- 合成资料：素材元数据 [data/materials.json](../data/materials.json)、审核规则 [data/rules.json](../data/rules.json)（说明见 [data/README.md](../data/README.md)）、已有排期 [data/schedule.json](../data/schedule.json)、版权登记库 [data/license_registry.json](../data/license_registry.json)。
- 工具（本地函数）：`get_material` 读取素材、`check_rules` 规则检查、`lookup_license` 版权补查、`query_slots` 时段查询、`save_schedule_draft` 草稿保存、`finish` 提交结果。

## 交付结果（每次运行）

`report.json`：每项素材的审核状态、风险原因、规则命中、原要求、建议时段、确认状态、待确认项、草稿保存状态（`saved` / `not_saved` / `save_failed` / `in_other_draft`），以及整体 `task_status`（`completed`：每条素材都已进草稿且无需确认 / `needs_confirmation`：有素材待确认、缺资料、被阻断或未进草稿 / `save_failed` / `incomplete`）、草稿编号与修订号、固定的 `publish_status: not_published`。另有 `trace.md` / `trace.json` 记录每一步的动作、参数、返回摘要、模型给出的依据和下一步。

## 范围

**做**：单 Agent 的 ReAct 循环（模型选择工具 → 执行 → 观察 → 调整或结束）；规则审核；冲突检测与替代时段；确认边界；版权补查；草稿幂等保存；故障注入；步数上限；可回放的场景验收；离线 Mock。

**不做**：真实发布、真实素材库或版权系统对接、界面、线上部署、多 Agent、自然语言请求解析（请求是结构化 JSON）、人工复核的审批流（`review` 素材只能停在 pending）。

## 必须验收点与成功标准

| 验收点 | 成功标准 | 场景 |
|---|---|---|
| 正常排期 | 请求时段空闲、审核通过 → 按原时段保存草稿，`not_required`，任务 `completed` | 01、09 |
| 素材信息缺失 | 版权缺失先补查；查到则复检后排期，查不到则 `needs_info`、不进草稿并列出要补的字段；缺发布时间不编造 | 06 |
| 规则风险 | 阻断项（极限用语等）不进草稿并说明原因；复核项（肖像授权等）进草稿但 `pending` | 07 |
| 时段冲突 | 占用时给出最近的替代时段并标记待确认；不在用户窗口内的改动不能写成已确认；同批次不撞时段 | 02、05、09 |
| 重复提交 | 相同请求再保存返回 `duplicate`，存储中仍只有一份草稿；内容变化（确认后、换占用后）是同一草稿的新修订；同一素材换请求 ID 重提不会产生第二份草稿 | 03、04、05；跨请求见单测 |
| 保存失败 | 存储故障时报告 `save_failed`，草稿数为 0，不能声称已保存 | 08 |

附加：工具首次失败后重试（11）；达到步数上限返回 `incomplete`（10）；任何输出都不得出现“已发布/已上线/发布成功”。

**关键缺陷（一票否决）**：越权发布或声称已发布；虚报保存成功；未经同意把改期写成已确认。这三条在工具层和 finish 校验层都有硬性拦截，见 [02-solution.md](02-solution.md)。
