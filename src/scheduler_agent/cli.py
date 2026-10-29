"""命令行入口：run（单次请求）/ suite（场景回放 + 验收）/ drafts（查看草稿）。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .agent import Limits, run_agent
from .domain import PROJECT_ROOT, load_json
from .evaluation import build_context, run_repeats, run_suite, write_run
from .llm import LLMError, load_dotenv, make_model
from .store import DraftStore
from .tools import FAULT_MODES

DEFAULT_STORE = PROJECT_ROOT / ".runtime" / "drafts.json"


def _print_report(report: dict) -> None:
    print(f"任务状态: {report['task_status']}    发布状态: {report['publish_status']}（只保存草稿）")
    d = report["draft"]
    print(f"草稿: {d['status']}" + (f"  {d['draft_id']} 修订 {d['revision']}" if d.get("draft_id") else ""))
    if report.get("incomplete_reason"):
        print(f"未完成原因: {report['incomplete_reason']}")
    for it in report["items"]:
        req = it["requested"]
        sug = f"{it.get('suggested_channel') or ''} {it.get('suggested_slot') or ''}".strip() or "—"
        print(f"  {it['material_id']}: 审核={it['review_status']}  要求={req.get('channel')} {req.get('publish_at')}  "
              f"建议={sug}  确认={it['confirmation_status']}  草稿={it['draft_status']}")
        if it.get("existing_draft"):
            e = it["existing_draft"]
            print(f"      已在草稿: {e['draft_id']}（请求 {e['request_key']}，{e['channel']} {e['slot']}，"
                  f"{e['confirmation_status']}）")
        for r in it["risk_reasons"]:
            print(f"      风险: {r}")
        for p in it["pending_items"]:
            print(f"      待确认: {p}")
    if report.get("summary"):
        print(f"总结: {report['summary']}")
    st = report["stats"]
    print(f"[{st['model']}] 模型轮次 {st['model_turns']}  工具调用 {st['tool_calls']}  "
          f"finish 退回 {st['finish_rejections']}  用时 {st['elapsed_sec']}s")


def main(argv=None) -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    parser = argparse.ArgumentParser(prog="scheduler_agent", description="素材审核与发布排期 Agent（只保存草稿）")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="处理一个排期请求 JSON")
    p_run.add_argument("input", type=Path)
    p_run.add_argument("--provider", default="deepseek", choices=["deepseek", "openai", "mock"])
    p_run.add_argument("--schedule", type=Path, help="已有排期文件，默认 data/schedule.json")
    p_run.add_argument("--store", type=Path, default=DEFAULT_STORE, help="草稿存储文件")
    p_run.add_argument("--inject", action="append", default=[], choices=FAULT_MODES, help="故障注入，可多次指定")
    p_run.add_argument("--max-turns", type=int, default=Limits.max_turns)
    p_run.add_argument("--max-tool-calls", type=int, default=Limits.max_tool_calls)
    p_run.add_argument("--out", type=Path, help="把 report/trace 写到该目录")
    p_run.add_argument("--json", action="store_true", help="以 JSON 输出最终报告")

    p_suite = sub.add_parser("suite", help="回放 examples/scenarios.json 中的全部场景并做验收检查")
    p_suite.add_argument("--provider", default="mock", choices=["deepseek", "openai", "mock"])
    p_suite.add_argument("--out", type=Path, help="输出目录，默认 examples/runs/<provider>")
    p_suite.add_argument("--only", nargs="*", help="只跑指定场景 ID（共享 store 的场景须一起指定）")
    p_suite.add_argument("--repeat", type=int, default=1, help="重复回放 N 次并统计每个场景的通过率")

    p_drafts = sub.add_parser("drafts", help="查看草稿存储")
    p_drafts.add_argument("--store", type=Path, default=DEFAULT_STORE)

    args = parser.parse_args(argv)
    try:
        if args.cmd == "run":
            request = load_json(args.input)
            ctx = build_context(request, args.store, args.schedule, tuple(args.inject))
            result = run_agent(ctx, make_model(args.provider), Limits(args.max_turns, args.max_tool_calls))
            if args.out:
                write_run(args.out, result, ctx, f"Trace · {args.input.name}", str(args.input), " ".join(sys.argv))
            if args.json:
                print(json.dumps(result.report, ensure_ascii=False, indent=2))
            else:
                _print_report(result.report)
                if args.out:
                    print(f"trace: {args.out / 'trace.md'}")
            return 0 if result.report["task_status"] != "incomplete" else 2
        if args.cmd == "suite":
            out = args.out or PROJECT_ROOT / "examples" / "runs" / args.provider
            if args.repeat > 1:
                rows = run_repeats(args.provider, out, args.repeat, args.only)
                print(f"\n稳定性汇总：{out / 'stability.md'}")
                return 0 if all(r["passed"] == r["runs"] for r in rows) else 1
            summary = run_suite(args.provider, out, args.only)
            failed = [s["id"] for s in summary if s["failed_checks"]]
            print(f"\n{len(summary) - len(failed)}/{len(summary)} 个场景全部检查通过；输出目录 {out}")
            return 1 if failed else 0
        if args.cmd == "drafts":
            drafts = DraftStore(args.store).list_drafts()
            print(json.dumps(drafts, ensure_ascii=False, indent=2))
            print(f"共 {len(drafts)} 份草稿", file=sys.stderr)
            return 0
    except LLMError as exc:
        print(f"模型错误：{exc}", file=sys.stderr)
        return 3
    return 1
