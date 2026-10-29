"""finish 校验与最终报告组装。

模型负责判断与说明；草稿是否保存、保存到哪个时段等“事实”一律以工具账本为准，
不一致的 finish 会被退回给模型修正，避免虚报保存成功或越权发布。
"""

from __future__ import annotations

import json
import re
from typing import List, Optional

from .domain import request_items
from .tools import ToolContext

FORBIDDEN_CLAIMS = re.compile(r"已发布|已经发布|已正式发布|发布成功|已上线|已推送上线")
REVIEW_MAP = {"pass": "pass", "review": "review", "block": "blocked", "incomplete": "needs_info"}


def _saved_items(ctx: ToolContext) -> dict:
    last = ctx.ledger.last_saved
    return {i["material_id"]: i for i in last["items"]} if last else {}


def _storage_failed_ids(ctx: ToolContext) -> set:
    ids = set()
    for attempt in ctx.ledger.save_attempts:
        if attempt.get("storage_failure"):
            ids.update(attempt["items"])
    return ids


def validate_finish(ctx: ToolContext, args: dict) -> List[str]:
    issues: List[str] = []
    items = args.get("items") or []
    requested = request_items(ctx.request)
    ids = [i.get("material_id") for i in items]
    missing = [m for m in requested if m not in ids]
    if missing:
        issues.append(f"缺少素材 {missing} 的结果，请求中的每个素材都要给出结论")
    for extra in sorted({m for m in ids if m not in requested}):
        issues.append(f"{extra} 不在本次请求中")
    for dup in sorted({m for m in ids if ids.count(m) > 1}):
        issues.append(f"{dup} 重复出现")

    saved = _saved_items(ctx)
    failed = _storage_failed_ids(ctx)
    for item in items:
        mid = item.get("material_id")
        if mid not in requested:
            continue
        p = f"{mid}: "
        rs = item.get("review_status")
        cs = item.get("confirmation_status")
        pending = item.get("pending_items") or []
        check = ctx.ledger.checks.get(mid)
        if check:
            expected = REVIEW_MAP[check["result"]]
            lacks_requirement = not requested[mid].get("publish_at") or not requested[mid].get("channel")
            if rs != expected and not (rs == "needs_info" and lacks_requirement):
                issues.append(p + f"review_status={rs} 与最近一次 check_rules 结果 {check['result']} 不一致")
        elif rs != "needs_info":
            issues.append(p + f"本次会话未对其执行 check_rules，不能给出 {rs} 结论")

        in_draft = bool(item.get("in_draft"))
        if in_draft and mid not in saved:
            issues.append(p + "in_draft=true，但没有包含该素材的成功保存记录")
        if not in_draft and mid in saved:
            issues.append(p + "该素材在成功保存的草稿中，in_draft 应为 true")
        if mid in saved:
            s = saved[mid]
            if item.get("suggested_slot") != s["slot"]:
                issues.append(p + f"suggested_slot={item.get('suggested_slot')} 与草稿中的时段 {s['slot']} 不一致")
            if item.get("suggested_channel") not in (None, s["channel"]):
                issues.append(p + f"suggested_channel 与草稿中的渠道 {s['channel']} 不一致")
            if cs != s["confirmation_status"]:
                issues.append(p + f"confirmation_status={cs} 与草稿中的 {s['confirmation_status']} 不一致")
        if rs in ("blocked", "needs_info") and cs == "confirmed":
            issues.append(p + f"{rs} 的素材不能标记为 confirmed")
        if cs == "pending" and not pending:
            issues.append(p + "confirmation_status=pending 时 pending_items 不能为空")
        if rs in ("blocked", "review") and not item.get("risk_reasons"):
            issues.append(p + f"{rs} 必须给出 risk_reasons")
        if rs == "needs_info" and not pending:
            issues.append(p + "needs_info 必须在 pending_items 中列出需补充的信息")
        if (rs in ("pass", "review") and item.get("suggested_slot") and not in_draft
                and mid not in failed and not pending):
            issues.append(p + "给出了建议时段却未保存草稿，也没有说明原因")

    if FORBIDDEN_CLAIMS.search(json.dumps(args, ensure_ascii=False)):
        issues.append("输出中出现“已发布/上线/发布成功”等表述；本系统只保存草稿，不能声称发布")
    return issues


def _draft_block(ctx: ToolContext) -> dict:
    last = ctx.ledger.last_saved
    attempts = ctx.ledger.save_attempts
    if last:
        r = last["result"]
        return {"status": r["status"], "draft_id": r["draft_id"], "revision": r["revision"],
                "attempts": len(attempts), "state": "draft"}
    errors = [a.get("error") for a in attempts if a.get("error")]
    if any(a.get("storage_failure") for a in attempts):
        return {"status": "failed", "draft_id": None, "attempts": len(attempts), "errors": errors}
    if attempts:
        return {"status": "rejected", "draft_id": None, "attempts": len(attempts), "errors": errors}
    return {"status": "not_attempted", "draft_id": None, "attempts": 0}


def build_report(ctx: ToolContext, finish_args: Optional[dict], stats: dict,
                 incomplete_reason: Optional[str] = None) -> dict:
    model_items = {i.get("material_id"): i for i in (finish_args or {}).get("items") or []}
    saved = _saved_items(ctx)
    failed = _storage_failed_ids(ctx)
    items = []
    for req in ctx.request.get("items", []):
        mid = req["material_id"]
        m = model_items.get(mid, {})
        check = ctx.ledger.checks.get(mid)
        if mid in saved:
            draft_status = "saved"
        elif mid in failed:
            draft_status = "save_failed"
        else:
            draft_status = "not_saved"
        findings = [f for f in (check or {}).get("findings", []) if f["severity"] != "info"]
        items.append({
            "material_id": mid,
            "requested": {k: req.get(k) for k in ("channel", "publish_at", "acceptable_window") if req.get(k)},
            "review_status": m.get("review_status") or (REVIEW_MAP[check["result"]] if check else "unknown"),
            "risk_reasons": m.get("risk_reasons") if m else [f["message"] for f in findings],
            "rule_findings": [f"{f['rule_id']}[{f['severity']}] {f['field']}" for f in findings],
            "suggested_channel": m.get("suggested_channel") or (saved[mid]["channel"] if mid in saved else None),
            "suggested_slot": m.get("suggested_slot") if m else (saved[mid]["slot"] if mid in saved else None),
            "confirmation_status": m.get("confirmation_status")
            or (saved[mid]["confirmation_status"] if mid in saved else "unknown"),
            "pending_items": m.get("pending_items") or [],
            "draft_status": draft_status,
        })

    if incomplete_reason:
        task_status = "incomplete"
    elif any(i["draft_status"] == "save_failed" for i in items):
        task_status = "save_failed"
    elif any(i["confirmation_status"] == "pending" or i["review_status"] == "needs_info" for i in items):
        # 只看结构化状态；pending_items 是自由文本，模型可能写入说明性内容
        task_status = "needs_confirmation"
    else:
        task_status = "completed"

    report = {
        "request_id": ctx.request.get("request_id"),
        "request_key": ctx.key,
        "task_status": task_status,
        "publish_status": "not_published",
        "publish_note": "本 Agent 只保存排期草稿，不调用任何发布接口",
        "draft": _draft_block(ctx),
        "items": items,
        "summary": (finish_args or {}).get("summary") or "",
        "stats": stats,
    }
    if incomplete_reason:
        report["incomplete_reason"] = incomplete_reason
    return report
