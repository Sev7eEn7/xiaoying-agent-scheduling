# 素材审核与发布排期 Agent（题号 1）

帮内容团队审核一批待发布素材，给出风险原因、无冲突的建议时段和待确认项，并把可排期的素材保存为**排期草稿**。项目没有任何发布能力：只保存草稿，不调用发布接口。

- 决策：模型通过函数调用自主选择 `get_material → check_rules → (lookup_license 补查) → query_slots → save_schedule_draft → finish`，根据工具结果决定补查、替代时段、请求确认或阻断。
- 约束：越权改期、阻断素材入稿、虚报保存成功、声称已发布，这几类问题在**工具层**和 **finish 校验层**都有代码拦截，不依赖提示词。
- 幂等：同一请求重复提交只会有一份草稿（内容相同返回 `duplicate`，内容变化记为同一草稿的新修订）；同一素材也只能出现在一份草稿里，换一个请求 ID 重提会被识别为已在草稿中（`in_other_draft`）。
- 上限：默认 15 轮模型调用、40 次工具调用。触达上限时返回 `task_status=incomplete` 和原因。

## 环境

- Python ≥ 3.9（在 macOS 自带的 3.9.6 上开发和测试）。运行时只用标准库，测试需要 `pytest`。
- 真实模型：任意 OpenAI 兼容、支持函数调用的接口。提交的运行记录**只使用 DeepSeek Flash 模型 `deepseek-flash`（DeepSeek-V4.1-Flash）**，这也是 `--provider deepseek` 的默认模型。
- 无模型时可以用 `--provider mock` 离线运行（边界见下文）。

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
```

真实模型需要配置密钥（离线 Mock 不需要）：

```bash
cp .env.example .env
# 编辑 .env，填写 LLM_API_KEY（DeepSeek 默认 base_url / model 已在 .env.example 中给出）
```

## 运行

单个请求（参考实例：M01 要求抖音 18:00，但该时段已被占用）：

```bash
python -m scheduler_agent run examples/inputs/02_conflict.json --provider deepseek --out .runtime/demo
```

回放全部 11 个验收场景，并自动检查结果（每个场景单独输出 report / trace / 检查结果）：

```bash
python -m scheduler_agent suite --provider deepseek --out examples/runs/deepseek-flash
```

```bash
python -m scheduler_agent suite --provider mock
```

运行测试：

```bash
python -m pytest -q
```

常用参数：`--schedule` 指定已有排期文件；`--store` 指定草稿存储（默认 `.runtime/drafts.json`）；`--inject` 注入故障（`save_fail`、`save_fail_once`、`slots_fail_once`、`material_fail`……）；`--max-turns` / `--max-tool-calls` 设置上限；`--json` 以 JSON 输出报告。查看草稿：`python -m scheduler_agent drafts --store <文件>`。

## 评审入口

| 想看什么 | 去哪里 |
|---|---|
| 真实模型的全部场景结果 | [examples/runs/deepseek-flash/summary.md](examples/runs/deepseek-flash/summary.md) |
| 参考实例的完整 trace | [examples/runs/deepseek-flash/02_conflict/trace.md](examples/runs/deepseek-flash/02_conflict/trace.md) |
| 同一请求在不同工具结果下走不同路径 | `02_conflict`（18:00 被占）对比 `05_swap_resubmit`（18:00 空出） |
| 重复 3 次的稳定性 | [examples/runs/deepseek-flash-stability/stability.md](examples/runs/deepseek-flash-stability/stability.md) |
| 测试预期、实际结果、失败与限制 | [docs/03-evaluation.md](docs/03-evaluation.md) |
| 防越权 / 防虚报 / 防重复的代码 | [tools.py `_validate_save_items`](src/scheduler_agent/tools.py)、[guard.py `validate_finish`](src/scheduler_agent/guard.py)、[store.py `upsert`](src/scheduler_agent/store.py) |
| 循环本体（不含业务分支） | [agent.py](src/scheduler_agent/agent.py) |

### 按审核要点手动复核：更换占用时段并重复提交

```bash
python -m scheduler_agent run examples/inputs/02_conflict.json --provider deepseek --store .runtime/review.json
```

```bash
python -m scheduler_agent run examples/inputs/02_conflict.json --provider deepseek --store .runtime/review.json
```

```bash
python -m scheduler_agent run examples/inputs/02_conflict.json --provider deepseek --store .runtime/review.json --schedule data/schedule_variant.json
```

```bash
python -m scheduler_agent drafts --store .runtime/review.json
```

预期结果：第 1 次建议 19:00、待确认，草稿 `created`；第 2 次草稿 `duplicate`；第 3 次（18:00 空出、19:00 被占）回到 18:00、`not_required`，草稿 `updated`（修订 2）；`drafts` 始终只有 1 份。也可以直接编辑 `data/schedule.json` 换掉占用时段，或在命令中加 `--inject save_fail`，检查是否如实报告保存失败。

## 目录

```
README.md
src/scheduler_agent/   循环、工具、校验、规则、时段、存储、模型接入、Mock、评估
tests/                 47 个 pytest 用例（规则、时段、存储、保存校验、finish 校验、循环上限、全场景 Mock 回放、真实模型记录重放）
examples/inputs/       请求输入
examples/scenarios.json  场景定义与期望
examples/runs/deepseek-flash/            真实模型（deepseek-flash）运行：report.json / trace.md / trace.json / messages.json / drafts_after.json / checks.json
examples/runs/deepseek-flash-stability/  同一套场景重复 3 次的稳定性回放
examples/runs/history/                   开发迭代早期用 deepseek-chat 跑出的失败记录（仅作历史证据）
examples/runs/mock/                      离线 Mock 运行（同样结构）
data/                  合成素材、规则、排期、版权登记库（说明见 data/README.md）
docs/01-05             需求 / 方案 / 评估 / AI 使用 / 复盘
requirements.txt       测试依赖（运行时无第三方依赖）
.env.example           模型配置；离线 Mock 无需配置
```

## 离线 Mock 的边界

`--provider mock` 是一个手写的规则策略（[mock_model.py](src/scheduler_agent/mock_model.py)），它与真实模型使用同一套工具协议。它只证明循环、工具、校验、落盘和验收脚本能跑通，**不能证明真实模型的决策效果**。决策效果以 `examples/runs/deepseek-flash/` 为准。

## 实际投入与取舍

见 [docs/05-retrospective.md](docs/05-retrospective.md)（用时、未完成部分）和 [docs/02-solution.md §8](docs/02-solution.md)（技术取舍）。AI 辅助的范围见 [docs/04-ai-usage.md](docs/04-ai-usage.md)。
