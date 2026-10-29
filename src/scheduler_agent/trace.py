"""把运行记录渲染为便于评审阅读的 Markdown。"""

from __future__ import annotations

import json
from typing import List, Optional


def _cell(value) -> str:
    if value is None or value == "" or value == [] or value == {}:
        return "—"
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False)
    return value.replace("|", "\\|").replace("\n", " ")


def _next_action(trace: List[dict], idx: int) -> str:
    for ev in trace[idx + 1:]:
        if ev["type"] == "tool":
            return ev["tool"]
        if ev["type"] == "stopped":
            return "停止"
    return "结束"


def render_markdown(report: dict, trace: List[dict], title: str, input_path: Optional[str] = None,
                    command: Optional[str] = None) -> str:
    st = report["stats"]
    lines = [f"# {title}", ""]
    if input_path:
        lines.append(f"- 输入：`{input_path}`")
    if command:
        lines.append(f"- 命令：`{command}`")
    lines += [
        f"- 模型：`{st['model']}`；模型轮次 {st['model_turns']}/{st['limits']['max_turns']}；"
        f"工具调用 {st['tool_calls']}/{st['limits']['max_tool_calls']}；finish 被退回 {st['finish_rejections']} 次",
        f"- 任务状态：**{report['task_status']}**；发布状态：{report['publish_status']}（{report['publish_note']}）",
        f"- 草稿：{_cell(report['draft'])}",
    ]
    if report.get("incomplete_reason"):
        lines.append(f"- 未完成原因：{report['incomplete_reason']}")
    lines += ["", "## 执行步骤", "",
              "| # | 轮次 | 动作 | 参数 | 返回摘要 | 决策依据（模型给出） | 下一步 |",
              "|---|---|---|---|---|---|---|"]
    for i, ev in enumerate(trace):
        if ev["type"] == "tool":
            lines.append(f"| {ev['step']} | {ev['turn']} | `{ev['tool']}` | {_cell(ev['args'])} | "
                         f"{'✅' if ev['ok'] else '❌'} {_cell(ev['observation'])} | {_cell(ev['reason'])} | "
                         f"{_next_action(trace, i)} |")
        elif ev["type"] == "text":
            lines.append(f"| — | {ev['turn']} | 文本回复（无工具调用） | — | {_cell(ev['content'])} | — | 提示继续 |")
        elif ev["type"] == "stopped":
            lines.append(f"| — | {ev['turn']} | **停止** | — | {_cell(ev['reason'])} | — | — |")
    lines += ["", "## 最终结果", "",
              "| 素材 | 审核 | 风险原因 | 规则命中 | 原要求 | 建议 | 确认状态 | 待确认项 | 草稿 |",
              "|---|---|---|---|---|---|---|---|---|"]
    for it in report["items"]:
        req = it["requested"]
        req_text = f"{req.get('channel', '?')} {req.get('publish_at', '未提供时间')}"
        if req.get("acceptable_window"):
            w = req["acceptable_window"]
            req_text += f"（可接受 {w['start'][-5:]}–{w['end'][-5:]}）"
        sug = f"{it.get('suggested_channel') or ''} {it.get('suggested_slot') or ''}".strip()
        draft = it["draft_status"]
        if it.get("existing_draft"):
            draft += f"（{it['existing_draft']['draft_id']}）"
        lines.append(f"| {it['material_id']} | {it['review_status']} | {_cell(it['risk_reasons'])} | "
                     f"{_cell(it['rule_findings'])} | {req_text} | {_cell(sug)} | {it['confirmation_status']} | "
                     f"{_cell(it['pending_items'])} | {draft} |")
    if report.get("summary"):
        lines += ["", f"**模型总结**：{report['summary']}"]
    return "\n".join(lines) + "\n"
