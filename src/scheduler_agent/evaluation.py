"""场景回放与验收检查：同一套期望既用于离线 Mock，也用于真实模型运行。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from .agent import Limits, RunResult, run_agent
from .domain import PROJECT_ROOT, load_json, load_materials, load_registry, load_rules, load_schedule
from .guard import FORBIDDEN_CLAIMS
from .llm import make_model
from .store import DraftStore
from .tools import FaultInjector, ToolContext
from .trace import render_markdown

EXAMPLES = PROJECT_ROOT / "examples"


def build_context(request: dict, store_path: Path, schedule_path: Optional[Path] = None,
                  inject: tuple = ()) -> ToolContext:
    return ToolContext(
        request=request,
        materials=load_materials(),
        rules=load_rules(),
        registry=load_registry(),
        schedule=load_schedule(schedule_path),
        store=DraftStore(store_path),
        faults=FaultInjector(inject),
    )


def _matches(actual, allowed) -> bool:
    return actual in allowed if isinstance(allowed, list) else actual == allowed


def check_expectations(expect: dict, result: RunResult, ctx: ToolContext) -> List[dict]:
    report, trace = result.report, result.trace
    checks = []

    def add(name, expected, actual, ok=None):
        checks.append({"check": name, "expected": expected, "actual": actual,
                       "pass": _matches(actual, expected) if ok is None else ok})

    if "task_status" in expect:
        add("task_status", expect["task_status"], report["task_status"])
    items = {i["material_id"]: i for i in report["items"]}
    for mid, fields in expect.get("items", {}).items():
        for field, allowed in fields.items():
            if field == "pending_items_nonempty":
                add(f"{mid}.pending_items 非空", True, bool(items.get(mid, {}).get("pending_items")))
            else:
                add(f"{mid}.{field}", allowed, items.get(mid, {}).get(field))
    if "draft_status" in expect:
        add("draft.status", expect["draft_status"], report["draft"]["status"])
    drafts = ctx.store.list_drafts()
    if "store_drafts" in expect:
        add("存储中的草稿数", expect["store_drafts"], len(drafts))
    if "store_revision" in expect:
        draft = ctx.store.get(ctx.key)
        add("该请求草稿的修订号", expect["store_revision"], draft["revision"] if draft else None)
    for mid in expect.get("store_excludes", []):
        stored = [i["material_id"] for d in drafts for i in d["items"]]
        add(f"{mid} 不在任何草稿中", True, mid not in stored)
    for need in expect.get("trace_includes", []):
        hit = any(ev["type"] == "tool" and ev["tool"] == need["tool"]
                  and all(ev["args"].get(k) == v for k, v in need.items() if k != "tool") for ev in trace)
        add(f"trace 包含 {need}", True, hit)
    text = json.dumps(report, ensure_ascii=False)
    add("未声称已发布", True, not FORBIDDEN_CLAIMS.search(text))
    st = report["stats"]
    add("未超过步数上限", True,
        st["model_turns"] <= st["limits"]["max_turns"] and st["tool_calls"] <= st["limits"]["max_tool_calls"])
    return checks


def _write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        path.write_text(data, encoding="utf-8")
    else:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_run(out_dir: Path, result: RunResult, ctx: ToolContext, title: str, input_rel: str,
              command: str) -> None:
    _write(out_dir / "report.json", result.report)
    _write(out_dir / "trace.json", result.trace)
    _write(out_dir / "messages.json", result.messages)
    _write(out_dir / "drafts_after.json", ctx.store.list_drafts())
    _write(out_dir / "trace.md", render_markdown(result.report, result.trace, title, input_rel, command))


def run_suite(provider: str, out_dir: Path, only: Optional[List[str]] = None,
              scenarios_path: Path = EXAMPLES / "scenarios.json") -> List[dict]:
    scenarios = [sc for sc in load_json(scenarios_path)["scenarios"] if not only or sc["id"] in only]
    stores_dir = out_dir / "_stores"
    for name in {sc["store"] for sc in scenarios}:  # 每次回放从空存储开始；共享 store 的场景须一起运行
        (stores_dir / f"{name}.json").unlink(missing_ok=True)
    summary = []
    for sc in scenarios:
        request = load_json(EXAMPLES / sc["input"])
        schedule = PROJECT_ROOT / sc["schedule"] if sc.get("schedule") else None
        ctx = build_context(request, stores_dir / f"{sc['store']}.json", schedule, tuple(sc.get("inject", [])))
        limits = Limits(**sc.get("limits", {}))
        print(f"[{sc['id']}] {sc['title']} …", flush=True)
        result = run_agent(ctx, make_model(provider), limits)
        checks = check_expectations(sc.get("expect", {}), result, ctx)
        flags = " ".join(filter(None, [
            f"--schedule {sc['schedule']}" if sc.get("schedule") else "",
            " ".join(f"--inject {m}" for m in sc.get("inject", [])),
            " ".join(f"--{k.replace('_', '-')} {v}" for k, v in sc.get("limits", {}).items()),
        ]))
        command = (f"python3 -m scheduler_agent run examples/{sc['input']} --provider {provider} "
                   f"--store .runtime/{sc['store']}.json {flags}").strip()
        run_dir = out_dir / sc["id"]
        write_run(run_dir, result, ctx, f"{sc['id']} · {sc['title']}", f"examples/{sc['input']}", command)
        _write(run_dir / "checks.json", checks)
        passed = sum(c["pass"] for c in checks)
        failed = [c["check"] for c in checks if not c["pass"]]
        print(f"    task_status={result.report['task_status']} turns={result.report['stats']['model_turns']} "
              f"tools={result.report['stats']['tool_calls']} checks={passed}/{len(checks)}"
              + (f" FAILED: {failed}" if failed else ""), flush=True)
        summary.append({"id": sc["id"], "title": sc["title"], "covers": sc.get("covers", []),
                        "model": result.report["stats"]["model"],
                        "task_status": result.report["task_status"],
                        "model_turns": result.report["stats"]["model_turns"],
                        "tool_calls": result.report["stats"]["tool_calls"],
                        "finish_rejections": result.report["stats"]["finish_rejections"],
                        "checks_passed": passed, "checks_total": len(checks), "failed_checks": failed})
    if not only:
        _write(out_dir / "summary.json", summary)
        _write(out_dir / "summary.md", _summary_md(provider, summary))
    return summary


def _summary_md(provider: str, summary: List[dict]) -> str:
    total = sum(s["checks_total"] for s in summary)
    passed = sum(s["checks_passed"] for s in summary)
    models = "、".join(sorted({s["model"] for s in summary}))
    lines = [f"# 场景验收汇总（provider={provider}，模型 {models}）", "",
             f"共 {len(summary)} 个场景，检查项通过 {passed}/{total}。每个场景目录下有 report.json、trace.md、"
             "trace.json、messages.json（原始模型输入输出）、drafts_after.json、checks.json。", "",
             "| 场景 | 覆盖验收点 | task_status | 模型轮次 | 工具调用 | finish 退回 | 检查 | 未通过 |",
             "|---|---|---|---|---|---|---|---|"]
    for s in summary:
        lines.append(f"| [{s['id']}]({s['id']}/trace.md) {s['title']} | {'、'.join(s['covers'])} | {s['task_status']} | "
                     f"{s['model_turns']} | {s['tool_calls']} | {s['finish_rejections']} | "
                     f"{s['checks_passed']}/{s['checks_total']} | {'；'.join(s['failed_checks']) or '—'} |")
    return "\n".join(lines) + "\n"


def run_repeats(provider: str, out_dir: Path, repeat: int, only: Optional[List[str]] = None) -> List[dict]:
    """同一组场景重复回放，统计每个场景“全部检查通过”的次数与失败的检查项。"""
    rows: dict = {}
    for k in range(1, repeat + 1):
        print(f"=== repeat {k}/{repeat}", flush=True)
        for s in run_suite(provider, out_dir / f"repeat-{k}", only):
            row = rows.setdefault(s["id"], {"id": s["id"], "title": s["title"], "model": s["model"], "runs": 0, "passed": 0,
                                            "turns": [], "tools": [], "failed_checks": []})
            row["runs"] += 1
            row["passed"] += not s["failed_checks"]
            row["turns"].append(s["model_turns"])
            row["tools"].append(s["tool_calls"])
            row["failed_checks"] += [f"#{k}: {c}" for c in s["failed_checks"]]
    result = list(rows.values())
    models = "、".join(sorted({r["model"] for r in result}))
    lines = [f"# 稳定性回放（provider={provider}，模型 {models}，每个场景 {repeat} 次）", "",
             "| 场景 | 全部检查通过 | 模型轮次 | 工具调用 | 未通过的检查（第几次） |", "|---|---|---|---|---|"]
    for r in result:
        lines.append(f"| {r['id']} {r['title']} | {r['passed']}/{r['runs']} | {r['turns']} | {r['tools']} | "
                     f"{'；'.join(r['failed_checks']) or '—'} |")
    total = sum(r["passed"] for r in result), sum(r["runs"] for r in result)
    lines += ["", f"合计：{total[0]}/{total[1]} 次场景运行全部检查通过。"]
    _write(out_dir / "stability.md", "\n".join(lines) + "\n")
    _write(out_dir / "stability.json", result)
    return result
