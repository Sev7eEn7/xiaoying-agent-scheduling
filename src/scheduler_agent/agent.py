"""ReAct 循环：模型选择动作 → 执行工具 → 观察结果 → 模型决定下一步或 finish。

循环本身不含任何业务分支；业务判断全部由模型根据工具返回做出。
循环只负责：执行工具、记录 trace、限制步数、校验 finish。
"""

from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import asdict, dataclass
from typing import List

from .guard import build_report, validate_finish
from .llm import LLMError
from .prompts import SYSTEM_PROMPT, user_message
from .tools import TOOL_SCHEMAS, ToolContext, dispatch, summarize

TODAY = "2026-10-29"
NUDGE = "请继续通过工具完成任务；全部处理完毕后调用 finish 提交结果。"


@dataclass
class Limits:
    max_turns: int = 15          # 模型调用轮次上限
    max_tool_calls: int = 40     # 工具调用总次数上限（含 finish）
    max_finish_rejections: int = 2


@dataclass
class RunResult:
    report: dict
    trace: List[dict]
    messages: List[dict]


def run_agent(ctx: ToolContext, model, limits: Limits = Limits(), today: str = TODAY) -> RunResult:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message(ctx.request, today)},
    ]
    trace: List[dict] = []
    usage: Counter = Counter()
    started = time.time()
    tool_calls = 0
    rejections = 0
    turn = 0

    def stats() -> dict:
        return {
            "model": getattr(model, "label", type(model).__name__),
            "model_turns": turn,
            "tool_calls": tool_calls,
            "finish_rejections": rejections,
            "limits": asdict(limits),
            "elapsed_sec": round(time.time() - started, 2),
            "usage": dict(usage),
        }

    def stop(reason: str) -> RunResult:
        trace.append({"step": tool_calls, "turn": turn, "type": "stopped", "reason": reason})
        return RunResult(build_report(ctx, None, stats(), incomplete_reason=reason), trace, messages)

    while turn < limits.max_turns:
        turn += 1
        try:
            resp = model.complete(messages, TOOL_SCHEMAS)
        except LLMError as exc:
            return stop(f"MODEL_ERROR: {exc}")
        for k, v in (resp.usage or {}).items():
            if isinstance(v, int):
                usage[k] += v
        messages.append(resp.to_message())

        if not resp.tool_calls:
            trace.append({"step": tool_calls, "turn": turn, "type": "text", "content": resp.content})
            messages.append({"role": "user", "content": NUDGE})
            continue

        # finish 放在同一轮其他工具之后处理，确保它看到本轮工具的结果
        for call in sorted(resp.tool_calls, key=lambda c: c.name == "finish"):
            if tool_calls >= limits.max_tool_calls:
                return stop(f"TOOL_CALL_LIMIT_REACHED: 已达到工具调用上限 {limits.max_tool_calls}，任务未完成")
            tool_calls += 1
            try:
                args = json.loads(call.arguments or "{}")
                if not isinstance(args, dict):
                    raise ValueError("arguments 不是 JSON 对象")
            except ValueError as exc:
                args = {}
                result = {"ok": False, "error": {"code": "INVALID_JSON", "message": f"参数不是合法 JSON：{exc}",
                                                 "retryable": True}}
            else:
                result = None

            event = {"step": tool_calls, "turn": turn, "type": "tool", "tool": call.name,
                     "args": {k: v for k, v in args.items() if k != "reason"}, "reason": args.get("reason", "")}

            if result is None and call.name == "finish":
                issues = validate_finish(ctx, args)
                if not issues:
                    event.update(ok=True, observation="finish 通过工具记录核对")
                    trace.append(event)
                    return RunResult(build_report(ctx, args, stats()), trace, messages)
                rejections += 1
                result = {"ok": False, "error": {"code": "REPORT_REJECTED", "retryable": True,
                                                 "message": "finish 与工具记录不一致，请修正后重新提交",
                                                 "issues": issues}}
            elif result is None:
                result = dispatch(ctx, call.name, args)

            event.update(ok=bool(result.get("ok")), observation=summarize(call.name, args, result), result=result)
            trace.append(event)
            messages.append({"role": "tool", "tool_call_id": call.id,
                             "content": json.dumps(result, ensure_ascii=False)})
            if call.name == "finish" and rejections > limits.max_finish_rejections:
                return stop(f"REPORT_REJECTED: finish 连续 {rejections} 次与工具记录不一致")

    return stop(f"STEP_LIMIT_REACHED: 已达到模型轮次上限 {limits.max_turns}，任务未完成")
