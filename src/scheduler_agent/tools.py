"""业务工具（本地函数）与会话账本。

工具只返回事实；所有写操作（保存草稿）在工具层做二次校验，
即使模型出错也无法越权改期、保存被阻断素材或伪造“已确认”。
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional

from .domain import CHANNELS, find_confirmation, parse_slot, request_items
from .rules import check_material
from .slots import SlotBook
from .store import DraftStore, request_key

CONFIRMATION_STATUSES = ("not_required", "pending", "confirmed")

FAULT_KEYS = {
    "get_material": "material",
    "check_rules": "rules",
    "lookup_license": "license",
    "query_slots": "slots",
    "save_schedule_draft": "save",
}
FAULT_MODES = tuple(f"{k}_fail{s}" for k in FAULT_KEYS.values() for s in ("", "_once"))


class FaultInjector:
    """故障注入：<tool>_fail 持续失败，<tool>_fail_once 仅首次失败。"""

    def __init__(self, modes: Iterable[str] = ()):
        self.modes = set(modes)
        unknown = self.modes - set(FAULT_MODES)
        if unknown:
            raise ValueError(f"未知故障模式 {sorted(unknown)}，可选：{', '.join(FAULT_MODES)}")
        self._fired: Counter = Counter()

    def should_fail(self, tool: str) -> bool:
        key = FAULT_KEYS.get(tool)
        if key is None:
            return False
        if f"{key}_fail" in self.modes:
            return True
        if f"{key}_fail_once" in self.modes and self._fired[key] == 0:
            self._fired[key] += 1
            return True
        return False


@dataclass
class Ledger:
    """本次运行中工具观察到的事实，供保存校验与最终报告核对。"""

    materials: Dict[str, bool] = field(default_factory=dict)
    checks: Dict[str, dict] = field(default_factory=dict)
    registry: Dict[str, Optional[dict]] = field(default_factory=dict)
    save_attempts: List[dict] = field(default_factory=list)
    last_saved: Optional[dict] = None


@dataclass
class ToolContext:
    request: dict
    materials: Dict[str, dict]
    rules: dict
    registry: Dict[str, dict]
    schedule: list
    store: DraftStore
    faults: FaultInjector = field(default_factory=FaultInjector)
    ledger: Ledger = field(default_factory=Ledger)

    @property
    def key(self) -> str:
        return request_key(self.request)

    def slot_book(self) -> SlotBook:
        return SlotBook(self.schedule, self.rules, self.store.holds(exclude_key=self.key))


def _error(code: str, message: str, retryable: bool = False, **extra) -> dict:
    err = {"code": code, "message": message, "retryable": retryable}
    err.update(extra)
    return {"ok": False, "error": err}


# ---------------------------------------------------------------- tools


def get_material(ctx: ToolContext, material_id: str) -> dict:
    if ctx.faults.should_fail("get_material"):
        return _error("TOOL_TIMEOUT", "素材库读取超时", retryable=True)
    material = ctx.materials.get(material_id)
    ctx.ledger.materials[material_id] = material is not None
    if material is None:
        return {"ok": True, "found": False, "material_id": material_id}
    return {"ok": True, "found": True, "material": material}


def check_rules(ctx: ToolContext, material_id: str, publish_at: Optional[str] = None) -> dict:
    if ctx.faults.should_fail("check_rules"):
        return _error("TOOL_TIMEOUT", "规则服务超时", retryable=True)
    material = ctx.materials.get(material_id)
    if material is None:
        return _error("NOT_FOUND", f"素材 {material_id} 不存在")
    publish_date = None
    if publish_at:
        try:
            publish_date = parse_slot(publish_at).date()
        except ValueError:
            return _error("INVALID_ARGUMENT", f"publish_at 格式应为 YYYY-MM-DDTHH:MM，收到 {publish_at!r}")
    registry_license = ctx.ledger.registry.get(material_id)
    outcome = check_material(material, ctx.rules, publish_date, registry_license)
    ctx.ledger.checks[material_id] = {**outcome, "publish_date": str(publish_date) if publish_date else None}
    return {"ok": True, "material_id": material_id, "rules_version": ctx.rules["version"],
            "publish_date": str(publish_date) if publish_date else None, **outcome}


def lookup_license(ctx: ToolContext, material_id: str) -> dict:
    if ctx.faults.should_fail("lookup_license"):
        return _error("TOOL_TIMEOUT", "版权登记库查询超时", retryable=True)
    record = ctx.registry.get(material_id)
    ctx.ledger.registry[material_id] = record
    return {"ok": True, "material_id": material_id, "found": record is not None, "record": record}


def query_slots(ctx: ToolContext, channel: str, publish_at: str, also_taken: Optional[list] = None) -> dict:
    if ctx.faults.should_fail("query_slots"):
        return _error("TOOL_TIMEOUT", "排期服务超时", retryable=True)
    if channel not in CHANNELS:
        return _error("INVALID_ARGUMENT", f"未知渠道 {channel}，可选：{', '.join(CHANNELS)}")
    try:
        parse_slot(publish_at)
    except (TypeError, ValueError):
        return _error("INVALID_ARGUMENT", f"publish_at 格式应为 YYYY-MM-DDTHH:MM，收到 {publish_at!r}")
    book = ctx.slot_book()
    taken = [(t.get("channel"), t.get("slot")) for t in also_taken or []]
    requested = book.status(channel, publish_at, taken)
    out = {"ok": True, "channel": channel, "requested": requested}
    if requested["status"] != "free":
        out["alternatives"] = book.alternatives(channel, publish_at, taken)
    return out


def _within_window(window: Optional[dict], slot: str) -> bool:
    if not window:
        return False
    try:
        return parse_slot(window["start"]) <= parse_slot(slot) <= parse_slot(window["end"])
    except (KeyError, TypeError, ValueError):
        return False


def _validate_save_items(ctx: ToolContext, items: list) -> tuple:
    requested = request_items(ctx.request)
    book = ctx.slot_book()
    issues: List[str] = []
    stored: List[dict] = []
    seen_ids = set()
    taken: List[tuple] = []
    for item in items:
        mid = item.get("material_id")
        prefix = f"{mid}: "
        if mid not in requested:
            issues.append(prefix + "不在本次请求中，不能加入草稿")
            continue
        if mid in seen_ids:
            issues.append(prefix + "在草稿中重复出现")
            continue
        seen_ids.add(mid)
        req = requested[mid]
        channel, slot = item.get("channel"), item.get("slot")
        cs = item.get("confirmation_status")
        note = (item.get("note") or "").strip()

        check = ctx.ledger.checks.get(mid)
        if check is None:
            issues.append(prefix + "本次会话尚未执行 check_rules，不能保存")
            continue
        if check["result"] == "block":
            issues.append(prefix + "审核结果为 block（阻断），不能加入草稿")
            continue
        if check["result"] == "incomplete":
            issues.append(prefix + "审核结果为 incomplete（资料缺失），补齐前不能加入草稿")
            continue

        error = book.validate(channel, slot) if channel and slot else "缺少 channel 或 slot"
        if error:
            issues.append(prefix + error)
            continue
        if check["publish_date"] != str(parse_slot(slot).date()):
            issues.append(prefix + f"规则检查基于发布日 {check['publish_date']}，草稿时段为 {slot}，"
                                   "请用该时段重新 check_rules")
        status = book.status(channel, slot, taken)
        if status["status"] != "free":
            issues.append(prefix + f"{channel} {slot} 不可用：{status.get('detail', status['status'])}")
        taken.append((channel, slot))

        if cs not in CONFIRMATION_STATUSES:
            issues.append(prefix + f"confirmation_status 须为 {CONFIRMATION_STATUSES} 之一")
        conf = find_confirmation(ctx.request, mid)
        approved = bool(conf) and conf.get("approved_slot") == slot and \
            conf.get("approved_channel", req.get("channel")) == channel
        changed = channel != req.get("channel") or slot != req.get("publish_at")
        in_window = channel == req.get("channel") and _within_window(req.get("acceptable_window"), slot)
        if not req.get("publish_at") and not approved and cs != "pending":
            issues.append(prefix + "用户未给出发布时间，建议时段必须标记为 pending 待确认")
        elif changed and not in_window and not approved and cs != "pending":
            issues.append(prefix + f"改动了用户的发布要求（{req.get('channel')} {req.get('publish_at')} → "
                                   f"{channel} {slot}），未经用户同意必须标记为 pending")
        if cs == "confirmed" and not approved:
            issues.append(prefix + "请求中没有用户对该时段的确认，不能标记为 confirmed")
        if check["result"] == "review" and cs != "pending":
            issues.append(prefix + "审核结果为 review，须标记 pending 等待人工复核")
        if cs == "pending" and not note:
            issues.append(prefix + "pending 条目须在 note 中写明待确认内容")

        stored.append({
            "material_id": mid,
            "channel": channel,
            "slot": slot,
            "requested_channel": req.get("channel"),
            "requested_slot": req.get("publish_at"),
            "review_result": check["result"],
            "confirmation_status": cs,
            "note": note,
        })
    return issues, stored


def save_schedule_draft(ctx: ToolContext, items: list) -> dict:
    attempt = {"items": [i.get("material_id") for i in items or []]}
    ctx.ledger.save_attempts.append(attempt)
    if not items:
        attempt["error"] = "NO_ITEMS"
        return {**_error("NO_ITEMS", "没有可保存的条目；若全部素材都不可排期，无需保存草稿"), "saved": False}
    issues, stored = _validate_save_items(ctx, items)
    if issues:
        attempt["error"] = "VALIDATION_FAILED"
        return {**_error("VALIDATION_FAILED", "草稿未保存：存在不合规条目，未写入任何数据", issues=issues),
                "saved": False}
    if ctx.faults.should_fail("save_schedule_draft"):
        attempt["error"] = "STORAGE_UNAVAILABLE"
        attempt["storage_failure"] = True
        return {**_error("STORAGE_UNAVAILABLE", "草稿存储服务不可用，本次未写入任何数据", retryable=True),
                "saved": False}
    result = ctx.store.upsert(ctx.key, stored)
    attempt["ok"] = True
    attempt["result"] = result
    ctx.ledger.last_saved = {"items": stored, "result": result}
    return {"ok": True, "saved": True, **result, "state": "draft", "items_saved": len(stored),
            "note": "仅保存为排期草稿，未发布；duplicate 表示同一请求已存在相同草稿，未重复创建"}


TOOL_FUNCS: Dict[str, Callable] = {
    "get_material": get_material,
    "check_rules": check_rules,
    "lookup_license": lookup_license,
    "query_slots": query_slots,
    "save_schedule_draft": save_schedule_draft,
}


def dispatch(ctx: ToolContext, name: str, args: dict) -> dict:
    func = TOOL_FUNCS.get(name)
    if func is None:
        return _error("UNKNOWN_TOOL", f"没有工具 {name}")
    params = {k: v for k, v in args.items() if k != "reason"}
    try:
        return func(ctx, **params)
    except TypeError as exc:
        return _error("INVALID_ARGUMENT", f"参数错误：{exc}")


# ---------------------------------------------------------------- schemas

_REASON = {"type": "string", "description": "一句话说明本次调用的依据（基于已观察到的结果）"}
_SLOT = {"type": "string", "description": "整点时间，格式 YYYY-MM-DDTHH:MM"}

TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "get_material",
        "description": "读取素材元数据。found=false 表示素材库中不存在该 ID。",
        "parameters": {"type": "object", "properties": {
            "material_id": {"type": "string"}, "reason": _REASON},
            "required": ["material_id", "reason"]}}},
    {"type": "function", "function": {
        "name": "check_rules",
        "description": ("按审核规则检查素材。result: pass / review（需人工复核）/ block（阻断）/ "
                        "incomplete（资料缺失）。publish_at 用于校验授权有效期；时段变更到其他日期后需重新检查。"
                        "若本次会话已通过 lookup_license 查到登记记录，元数据缺失的版权信息会使用该记录。"),
        "parameters": {"type": "object", "properties": {
            "material_id": {"type": "string"}, "publish_at": _SLOT, "reason": _REASON},
            "required": ["material_id", "reason"]}}},
    {"type": "function", "function": {
        "name": "lookup_license",
        "description": "补查：在版权登记库中查询素材的版权登记记录（用于元数据缺少版权信息时）。",
        "parameters": {"type": "object", "properties": {
            "material_id": {"type": "string"}, "reason": _REASON},
            "required": ["material_id", "reason"]}}},
    {"type": "function", "function": {
        "name": "query_slots",
        "description": ("查询渠道某整点是否可用。status: free / occupied（已有排期）/ held_by_draft（其他请求草稿占位）/ "
                        "planned_in_batch（also_taken 中已规划）/ invalid。不可用时返回最近的空闲备选时段。"),
        "parameters": {"type": "object", "properties": {
            "channel": {"type": "string", "enum": ["douyin", "xiaohongshu"]},
            "publish_at": _SLOT,
            "also_taken": {"type": "array", "description": "本批次已规划给其他素材的时段",
                           "items": {"type": "object", "properties": {
                               "channel": {"type": "string"}, "slot": _SLOT},
                               "required": ["channel", "slot"]}},
            "reason": _REASON},
            "required": ["channel", "publish_at", "reason"]}}},
    {"type": "function", "function": {
        "name": "save_schedule_draft",
        "description": ("把可排期素材保存为一份排期草稿（不会发布）。同一请求重复保存是幂等的：内容相同返回 duplicate，"
                        "内容变化返回 updated（同一份草稿的新修订）。工具会校验审核结果、时段占用与确认状态，"
                        "不合规时整体不写入。"),
        "parameters": {"type": "object", "properties": {
            "items": {"type": "array", "items": {"type": "object", "properties": {
                "material_id": {"type": "string"},
                "channel": {"type": "string", "enum": ["douyin", "xiaohongshu"]},
                "slot": _SLOT,
                "confirmation_status": {"type": "string", "enum": list(CONFIRMATION_STATUSES),
                                        "description": "not_required=与用户要求一致或在其允许窗口内；"
                                                       "pending=待用户/人工确认；confirmed=请求中已有用户确认"},
                "note": {"type": "string", "description": "pending 时写明待确认内容"}},
                "required": ["material_id", "channel", "slot", "confirmation_status"]}},
            "reason": _REASON},
            "required": ["items", "reason"]}}},
    {"type": "function", "function": {
        "name": "finish",
        "description": ("提交最终结果并结束。系统会用工具记录核对：审核结论须与 check_rules 一致，"
                        "in_draft 须与成功保存的草稿一致。被拒绝时按 issues 修正后重新提交。"),
        "parameters": {"type": "object", "properties": {
            "items": {"type": "array", "items": {"type": "object", "properties": {
                "material_id": {"type": "string"},
                "review_status": {"type": "string", "enum": ["pass", "review", "blocked", "needs_info"]},
                "risk_reasons": {"type": "array", "items": {"type": "string"},
                                 "description": "内容/合规风险原因（依据 check_rules 的 findings）；没有风险时为空数组，"
                                                "时段调整等排期说明写在 summary"},
                "suggested_channel": {"type": ["string", "null"]},
                "suggested_slot": {"type": ["string", "null"], "description": "建议时段；阻断或无法给出时为 null"},
                "confirmation_status": {"type": "string",
                                        "enum": ["not_required", "pending", "confirmed", "not_applicable"]},
                "pending_items": {"type": "array", "items": {"type": "string"},
                                  "description": "仍需用户确认或补充的事项；无需任何人处理时为空数组"},
                "in_draft": {"type": "boolean", "description": "该素材是否在成功保存的草稿中"}},
                "required": ["material_id", "review_status", "risk_reasons", "suggested_slot",
                             "confirmation_status", "pending_items", "in_draft"]}},
            "summary": {"type": "string", "description": "给内容团队的简短说明"}},
            "required": ["items", "summary"]}}},
]


# ---------------------------------------------------------------- trace summaries


def summarize(name: str, args: dict, result: dict) -> str:
    if not result.get("ok"):
        err = result.get("error", {})
        text = f"失败 {err.get('code')}：{err.get('message')}"
        if err.get("issues"):
            text += "；" + "；".join(err["issues"])
        return text
    if name == "get_material":
        if not result["found"]:
            return f"素材库中不存在 {result['material_id']}"
        m = result["material"]
        return f"找到 {m['id']}《{m['title']}》，license={'有' if m.get('license') else '缺失'}"
    if name == "check_rules":
        parts = [f"{f['rule_id']}[{f['severity']}] {f['message']}" + (f"（{f['evidence']}）" if f.get("evidence") else "")
                 for f in result["findings"] if f["severity"] != "info"]
        src = "，版权信息来自登记库补查" if result["license_source"] == "registry" else ""
        return f"{result['material_id']} 审核 {result['result']}{src}" + ("：" + "；".join(parts) if parts else "")
    if name == "lookup_license":
        if not result["found"]:
            return f"登记库无 {result['material_id']} 的版权记录"
        r = result["record"]
        return f"登记库命中 {r['registry_id']}（{r['type']}，持有方 {r['holder']}，到期 {r.get('expires_at') or '长期'}）"
    if name == "query_slots":
        req = result["requested"]
        text = f"{result['channel']} {req['slot']} {req['status']}"
        if req.get("detail"):
            text += f"（{req['detail']}）"
        if result.get("alternatives"):
            text += "；备选 " + "、".join(a["slot"][-5:] if a["slot"][:10] == req["slot"][:10] else a["slot"]
                                        for a in result["alternatives"])
        return text
    if name == "save_schedule_draft":
        return (f"草稿 {result['draft_id']} {result['status']}（修订 {result['revision']}，"
                f"{result['items_saved']} 条，未发布）")
    return "ok"
