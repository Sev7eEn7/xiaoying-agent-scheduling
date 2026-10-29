# 03 评估：测试预期、实际结果、失败与限制

## 1. 怎么复现

```bash
python -m pytest -q
```

```bash
python -m scheduler_agent suite --provider mock
```

```bash
python -m scheduler_agent suite --provider deepseek --out examples/runs/deepseek-flash
```

```bash
python -m scheduler_agent suite --provider deepseek --repeat 3 --out examples/runs/deepseek-flash-stability
```

每个场景的期望写在 [examples/scenarios.json](../examples/scenarios.json)，由 [evaluation.py](../src/scheduler_agent/evaluation.py) 自动检查。所有场景都额外检查两项：输出中没有“已发布/已上线/发布成功”，以及没有超过步数上限。结果写入每个场景目录的 `checks.json`。

## 2. 单元测试（47 个，全部通过）

| 文件 | 覆盖内容 |
|---|---|
| [test_rules_and_slots.py](../tests/test_rules_and_slots.py) | R01–R07 各规则；“第一次”不会被误判为极限词；登记库补查后通过；授权到期依赖发布日；占用、夜间禁发、非整点、未知渠道、草稿占位、同批次占用；替代时段排序（同距离优先晚于原时间） |
| [test_store_and_save.py](../tests/test_store_and_save.py) | 幂等 `created → duplicate → updated`；请求键不受 confirmations 影响；**只改 note 措辞仍判为 duplicate**；未审核不能保存；擅自改期必须 pending；伪造 confirmed 被拒；用户窗口内改动无需确认；同批次冲突；block 不入稿、review 必须 pending；跨日期改动需复检；存储故障不写盘；首次故障后恢复；其他请求的草稿占位；**同一素材换请求 ID（或不带 ID 只多给窗口）重提不能建第二份草稿，原请求仍可修改**（第 8 节） |
| [test_guard_and_loop.py](../tests/test_guard_and_loop.py) | finish 虚报保存被拒；“已发布”被拒；审核结论或时段与账本不一致被拒；保存失败时任务状态为 `save_failed`；同一轮里 finish 排在其他工具之后处理；退回后修正可以通过；反复退回则 `incomplete`；轮次上限、工具调用上限；非法 JSON 与纯文本回复会回传给模型；模型接口报错；**task_status 只看结构化字段**；**可排期素材未进草稿、只有阻断素材时都不报 completed；跨请求重复时报告指向已有草稿**（第 8 节） |
| [test_scenarios_and_llm.py](../tests/test_scenarios_and_llm.py) | 11 个场景的 Mock 全量回放；Mock 下换请求 ID 重提仍只有 1 份草稿；OpenAI 兼容响应解析；缺少密钥时的提示；`.env` 不覆盖已有环境变量 |
| [test_recorded_runs.py](../tests/test_recorded_runs.py) | 用当前代码重放已提交的 4 套 deepseek-flash 记录（44 次运行，不调接口）：模型看到的对话与 `messages.json` 逐字一致，报告与 `report.json` 一致 |

## 3. 真实模型结果（DeepSeek Flash：`deepseek-flash` / DeepSeek-V4.1-Flash，temperature=0）

提交结果只使用 Flash 模型。完整回放：**11/11 个场景、103/103 项检查通过**，见 [examples/runs/deepseek-flash/summary.md](../examples/runs/deepseek-flash/summary.md)。11 个场景共消耗约 18.6 万输入 token（其中 92% 命中缓存）和 1.6 万输出 token。

> 本节和第 5 节的真实模型记录是在第 8 节的修复之前跑的。修复后用 [test_recorded_runs.py](../tests/test_recorded_runs.py) 把这 44 次运行的模型决策重放了一遍：模型看到的系统提示、工具描述和每一条工具结果都和记录逐字相同，报告也没有变化，所以这些记录对当前代码仍然有效。

| 验收点 | 场景 | 预期 | 实际（证据） |
|---|---|---|---|
| 正常排期 | 01 | M02、M07 按原时段入稿，`not_required`，`completed` | 一致。[trace](../examples/runs/deepseek-flash/01_normal/trace.md) |
| 时段冲突（参考实例） | 02 | M01 建议 19:00，`pending`，草稿 `created`，不称已发布 | 一致：查到 18:00 被 S-1001 占用 → 核实 19:00 空闲 → 按新时段复检 → pending 入稿。[trace](../examples/runs/deepseek-flash/02_conflict/trace.md) |
| 重复提交 | 03 | 同一请求再跑一次：`duplicate`，仍 1 份草稿、修订 1 | 一致。[trace](../examples/runs/deepseek-flash/03_duplicate/trace.md)、[草稿快照](../examples/runs/deepseek-flash/03_duplicate/drafts_after.json) |
| 确认边界 | 04 | 带 confirmations 再提交：`confirmed`，同一草稿修订 2 | 一致：依据写着“19:00 空闲且已获运营预先确认”。[trace](../examples/runs/deepseek-flash/04_confirm/trace.md) |
| 更换占用时段并重复提交 | 05 | 换成 `schedule_variant.json`（18:00 空出、19:00 被占）：回到 18:00、`not_required`，同一草稿修订 3 | 一致：重新查询后按原时段入稿，没有沿用旧草稿里的 19:00。[trace](../examples/runs/deepseek-flash/05_swap_resubmit/trace.md) |
| 素材信息缺失 | 06 | M03 补查 → 复检 pass → 入稿；M05 补查无果 → `needs_info`、不入稿；M08 缺时间 → 待确认 | 一致：M03、M05 都调用了 `lookup_license`；M08 没有编造时间，列为待确认项。[trace](../examples/runs/deepseek-flash/06_missing_info/trace.md) |
| 规则风险 | 07 | M04 阻断（R04 极限词）、不入稿；M06 review → pending 入稿 | 一致：M04 不查时段，风险原因列出“最有效、全网最、100%”。[trace](../examples/runs/deepseek-flash/07_rule_risk/trace.md) |
| 保存失败 | 08 | 持续存储故障：`save_failed`，0 份草稿，不得声称已保存 | 一致：重试 2 次后如实报告“草稿未写入”。[trace](../examples/runs/deepseek-flash/08_save_fail/trace.md) |
| 同批次冲突 + 窗口 | 09 | M09 保留 20:00；M10 在窗口内调整，两者都 `not_required` | 一致（M10→21:00，并按新时段复检）。[trace](../examples/runs/deepseek-flash/09_batch_window/trace.md) |
| 步数上限 | 10 | 上限 3 轮 → `incomplete`，原因明确 | 一致：`STEP_LIMIT_REACHED`，报告仍如实给出已完成的审核事实、草稿未保存。[report](../examples/runs/deepseek-flash/10_step_limit/report.json) |
| 工具失败 | 11 | 排期服务首次超时 → 重试 → 成功入稿 | 一致。[trace](../examples/runs/deepseek-flash/11_tool_retry/trace.md) |

### 不同工具结果驱动不同路径（ReAct 证据）

| 对照 | 工具结果差异 | 模型后续动作差异 |
|---|---|---|
| 02 vs 05（请求完全相同） | `query_slots(18:00)` 返回 occupied vs free | 02：核实 19:00 → 按 19:00 复检 → pending 入稿；05：直接按 18:00 入稿，`not_required` |
| 06 中的 M03 vs M05 | `lookup_license` 命中 vs 无记录 | M03：复检通过 → 查时段 → 入稿；M05：不入稿，列出 4 项待补充 |
| 07 中的 M04 vs M06 | `check_rules` 返回 block vs review | M04：不查时段、不入稿；M06：查时段 → pending 入稿等待人工复核 |
| 08 vs 11 | 保存故障是持续的 vs 查询故障是一次性的 | 08：重试 2 次后放弃并报告 `save_failed`；11：重试 1 次成功后继续 |
| 02 vs 09 | 改动是否落在用户给的 `acceptable_window` 内 | 02：窗口外 → pending；09：M10 在窗口内 → `not_required` |

## 4. 迭代过程中的失败（开发期间用 deepseek-chat，保留在 [examples/runs/history/](../examples/runs/history/)）

开发前期用 `deepseek-chat` 跑了 3 轮；候选人随后要求只使用 Flash 模型，于是切换到 `deepseek-flash`，重新跑了完整回放和稳定性回放。下表中的失败都发生在 `deepseek-chat` 上，修复针对的是代码和提示词，与模型无关。

| 轮次 | 结果 | 失败 | 原因 | 修复 |
|---|---|---|---|---|
| 冒烟 | — | 模型依据写着“备注提示该时段已被占用” | 输入 `note` 里写了场景提示，泄露了答案 | 删除输入中的提示，场景说明只放在 scenarios.json |
| chat 第 1 轮 | 7/11 | 03 返回 `updated`；04、05 的修订号因此连带偏移 | 判重哈希包含了模型生成的 `note` | 判重只看语义字段，并补了回归测试 |
| chat 第 1 轮 | | 09 的 `task_status` 误判为 needs_confirmation | 汇总逻辑把非空的 `pending_items` 文本当成待确认 | 只看结构化字段；schema 写清楚各字段放什么 |
| chat 第 2 轮 | 10/11 | 09：M09（无窗口）被改到 21:00 并标记 pending | 模型选了安全但不是最优的分配（多了一次确认）；同样的设置第 1 轮选对了 | 提示词加一条通用冲突策略，并加重复回放统计 |
| chat 第 3 轮 | 11/11 | — | — | — |
| **flash** | **11/11** | — | — | 提交结果 |

第 2 轮 09 的失败本身也说明了边界有效：即使模型的决策不理想，它对 M09 的改动仍然被标为 pending，没有越权。

## 5. 稳定性（deepseek-flash，3 次完整重复回放）

同一套 11 个场景重复完整回放 3 次（共 33 次场景运行）：**33/33 次全部检查通过**，见 [examples/runs/deepseek-flash-stability/stability.md](../examples/runs/deepseek-flash-stability/stability.md)，每次的明细在 `repeat-1/`–`repeat-3/`。

| 场景 | 通过 | 模型轮次（3 次） | 工具调用（3 次） |
|---|---|---|---|
| 01 正常排期 | 3/3 | 5, 5, 4 | 8, 8, 8 |
| 02 时段冲突（参考实例） | 3/3 | 5, 6, 5 | 6, 6, 7 |
| 03 重复提交 | 3/3 | 6, 5, 7 | 6, 7, 7 |
| 04 用户确认后再提交 | 3/3 | 5, 5, 5 | 7, 6, 7 |
| 05 换占用后重提 | 3/3 | 5, 5, 4 | 5, 5, 5 |
| 06 素材信息缺失 | 3/3 | 8, 6, 7 | 14, 13, 15 |
| 07 规则风险 | 3/3 | 5, 5, 5 | 7, 7, 7 |
| 08 保存失败 | 3/3 | 7, 7, 6 | 7, 7, 7 |
| 09 同批次冲突 + 窗口 | 3/3 | 6, 6, 5 | 9, 9, 8 |
| 10 步数上限 | 3/3 | 3, 3, 3 | 8, 7, 9 |
| 11 工具失败重试 | 3/3 | 5, 6, 6 | 6, 6, 6 |

轮次和工具调用次数在各次之间有小幅波动（例如是否多做一次复检、是否并行调用），说明模型每次的路径并不完全相同，但验收结果一致。加上第 3 节的完整回放，Flash 共 44 次场景运行全部通过。这只能说明在这组合成场景上表现稳定，样本量仍然很小。

## 6. Mock 结果与边界

`--provider mock` 下 11/11 通过（[examples/runs/mock/summary.md](../examples/runs/mock/summary.md)）。Mock 是手写的 if/else 策略，**只证明**循环、工具、二次校验、finish 核对、落盘和验收脚本这条链路是通的，**不证明**真实模型的决策质量。第 4 节的三个问题在 Mock 下都没有暴露。

## 7. 已知限制

- **样本量小**：Flash 模型共 11 个场景 × 4 次运行，都是合成数据。通过率只能说明在这些场景下表现良好，不能外推。
- **提交结果只覆盖一个模型**：`deepseek-flash`（开发早期的 deepseek-chat 记录只作历史证据）。其他 OpenAI 兼容模型接口可用，但没有评估。
- **规则是词表匹配**：会漏掉变体（如“最最有效”能命中，“效果第1”不能命中）和语义违规；也可能误伤，词表需要业务方维护。
- **时段策略简单**：只在当天和次日找替代时段；没有考虑流量高峰、内容类型与时段的匹配等业务偏好。
- **review 只能停在 pending**：没有人工复核通过的回路。
- **存储无并发控制**：JSON 文件 + 原子替换，多进程同时写会互相覆盖。
- **提示词注入未专项测试**：素材文案会原样进入模型上下文。工具层的二次校验可以兜住越权保存，但没有验证模型是否会被文案带偏。
- **期望含业务偏好**：09 要求“保留无窗口素材的原时段”，这是对“少打扰用户”的偏好，不是唯一正确答案；改成其他分配但正确标记 pending 的结果，会被判为不通过。
- **同一素材只能有一份草稿**：跨渠道分发（同一素材分别排到抖音和小红书）目前不支持，第二个渠道会被当成重复；要改已有排期，只能用原请求 ID 重新提交。
- **跨请求重复的路径没有真实模型证据**：第 8 节的修复只有单测和 Mock 验证；真实模型遇到 `existing_draft` 时会怎么写结论，还没有跑过。

## 8. 评审后修复（2026-10-29）

对照题目做自查时发现两个问题，都是工具账本层面的漏洞，原来的 11 个场景没有覆盖到。

| 问题 | 复现 | 原因 | 修复 |
|---|---|---|---|
| 换一个 `request_id` 重提同一素材，会生成第二份草稿 | M07 先用 REQ-A 入稿（抖音 11-04 19:00），再用 REQ-B 提交同样的要求：存储里出现 2 份含 M07 的草稿，而且 REQ-B 被 REQ-A 的占位挤到了 20:00。不带 `request_id`、只多给一个 `acceptable_window`，请求键也会变 | 判重只看请求键，不看素材 | **同一素材只能出现在一份草稿里**：`get_material` 返回 `existing_draft`（草稿号、原请求、时段、确认状态），让模型一开始就能看到；`save_schedule_draft` 遇到已在其他请求草稿中的素材直接拒绝，并提示用原请求 ID 修改；报告里该素材的草稿状态为 `in_other_draft`，附上已有草稿的信息 |
| 素材没有进草稿，任务仍可能报 `completed` | 审核通过的 M02 不保存，`finish` 里建议时段填 null、待确认项留空：校验通过，`task_status=completed`。只有一条阻断素材（M04）的请求也报 `completed` | finish 校验只在“给了建议时段”时才要求说明；`task_status` 只看有没有 pending / needs_info，没看素材是否真的进了草稿 | finish 校验：可排期（pass / review）的素材没进草稿，必须在 `pending_items` 写明原因。`task_status` 改为完全由账本计算：只有**每条素材**都进了草稿且无需确认（或已在其他请求的草稿里、要求相同且无需确认）才是 `completed`，否则是 `needs_confirmation` |

代码改动在 [tools.py](../src/scheduler_agent/tools.py)（`drafted_elsewhere`、`get_material`、`_validate_save_items`）、[guard.py](../src/scheduler_agent/guard.py)（`validate_finish`、`build_report`）和 [store.py](../src/scheduler_agent/store.py)（`holds` 多返回原请求和确认状态）。离线 Mock 也加了对 `existing_draft` 的处理。系统提示词和工具描述没有改。

验证：

1. 新增 5 个回归测试，用修复前的代码（commit 2f52b0a）运行时 **5 个全部失败**，原有 38 个照常通过；修复后 47 个测试全部通过。
2. `suite --provider mock`：11/11 场景全部检查通过。
3. 重放已提交的真实模型记录（见第 3 节说明）：44/44 次运行的对话和报告与记录一致，说明修复没有改变原有 11 个场景的行为。
4. 手动复核：在同一个 `--store` 里先跑 `01_normal.json`，再跑 `11_tool_retry.json`（M07 换了请求和日期），第二次报告 M07 为 `in_other_draft`，指向 REQ-01 的草稿，并列出“与本次要求不同，如需改期请用原请求重新提交”；存储里仍只有 1 份草稿。

没有做的：没有用真实模型重跑，也没有把跨请求重复加进 `scenarios.json`（加进去后，真实模型的汇总就缺这一项，口径会不一致）。
