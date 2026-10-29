"""用当前代码重放已提交的真实模型（deepseek-flash）运行记录，不调用模型接口。

把记录里模型每一轮的工具调用按原顺序喂给循环，要求：
1. 生成的完整对话（系统提示、请求、工具结果）与 messages.json 逐字一致——模型看到的输入没有变；
2. 报告（除耗时等统计）与 report.json 一致。
代码改动只要改变了模型能看到的工具结果或最终结论，这里就会失败，提示需要重跑真实模型。
"""

import pytest

from scheduler_agent.agent import Limits, run_agent
from scheduler_agent.domain import PROJECT_ROOT, load_json
from scheduler_agent.evaluation import build_context
from scheduler_agent.llm import ModelTurn, ToolCall

EXAMPLES = PROJECT_ROOT / "examples"
RUN_ROOTS = ["deepseek-flash"] + [f"deepseek-flash-stability/repeat-{k}" for k in (1, 2, 3)]


class ReplayModel:
    def __init__(self, recorded: list, label: str):
        self.turns = [m for m in recorded if m["role"] == "assistant"]
        self.label = label
        self.calls = 0

    def complete(self, messages, tools):
        m = self.turns[self.calls]
        self.calls += 1
        calls = [ToolCall(c["id"], c["function"]["name"], c["function"]["arguments"]) for c in m.get("tool_calls") or []]
        return ModelTurn(content=m["content"] or None, tool_calls=calls)


def _without_stats(report: dict) -> dict:
    return {k: v for k, v in report.items() if k != "stats"}


@pytest.mark.parametrize("root", RUN_ROOTS)
def test_recorded_real_model_runs_replay_unchanged(root, tmp_path):
    run_root = EXAMPLES / "runs" / root
    for sc in load_json(EXAMPLES / "scenarios.json")["scenarios"]:  # 按顺序执行，共享 store 的场景依次落在同一存储
        recorded_msgs = load_json(run_root / sc["id"] / "messages.json")
        recorded_report = load_json(run_root / sc["id"] / "report.json")
        schedule = PROJECT_ROOT / sc["schedule"] if sc.get("schedule") else None
        ctx = build_context(load_json(EXAMPLES / sc["input"]), tmp_path / f"{sc['store']}.json", schedule,
                            tuple(sc.get("inject", [])))
        result = run_agent(ctx, ReplayModel(recorded_msgs, recorded_report["stats"]["model"]),
                           Limits(**sc.get("limits", {})))
        assert result.messages == recorded_msgs, f"{root}/{sc['id']}: 模型看到的输入已变化"
        assert _without_stats(result.report) == _without_stats(recorded_report), f"{root}/{sc['id']}: 报告结论已变化"
