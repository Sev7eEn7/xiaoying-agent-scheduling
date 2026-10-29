import json
from typing import List, Tuple

import pytest

from scheduler_agent.domain import load_materials, load_registry, load_rules, load_schedule
from scheduler_agent.llm import ModelTurn, ToolCall
from scheduler_agent.store import DraftStore
from scheduler_agent.tools import FaultInjector, ToolContext


@pytest.fixture
def make_ctx(tmp_path):
    def _make(request: dict, inject=(), store_name: str = "drafts.json", schedule=None) -> ToolContext:
        return ToolContext(
            request=request,
            materials=load_materials(),
            rules=load_rules(),
            registry=load_registry(),
            schedule=schedule if schedule is not None else load_schedule(),
            store=DraftStore(tmp_path / store_name),
            faults=FaultInjector(inject),
        )
    return _make


class ScriptedModel:
    """测试用：按预设轮次返回工具调用，用来驱动循环的边界行为（不是 Mock 决策）。"""

    label = "scripted"

    def __init__(self, turns: List[List[Tuple[str, object]]], repeat_last: bool = False):
        self.turns = turns
        self.repeat_last = repeat_last
        self.calls = 0
        self.seen = []

    def complete(self, messages, tools):
        self.seen.append(messages[-1])
        idx = self.calls if not self.repeat_last else min(self.calls, len(self.turns) - 1)
        self.calls += 1
        if idx >= len(self.turns):
            return ModelTurn(content="(no more script)")
        turn = self.turns[idx]
        if isinstance(turn, str):
            return ModelTurn(content=turn)
        calls = []
        for i, (name, args) in enumerate(turn):
            raw = args if isinstance(args, str) else json.dumps(args, ensure_ascii=False)
            calls.append(ToolCall(f"c{self.calls}-{i}", name, raw))
        return ModelTurn(content=None, tool_calls=calls)


REQ_CONFLICT = {"request_id": "REQ-T", "items": [
    {"material_id": "M01", "channel": "douyin", "publish_at": "2026-11-03T18:00"}]}
