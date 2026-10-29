"""离线 Mock：手写的规则策略，按与真实模型相同的协议输出工具调用。

边界：它只用于在没有模型 API 时验证循环、工具、校验与落盘流程；
它的“决策”是固定的 if/else，不能证明真实模型的决策效果。
"""

from __future__ import annotations

import json
import re
from typing import List, Optional, Tuple

from .domain import find_confirmation, parse_slot
from .llm import ModelTurn, ToolCall

REVIEW_MAP = {"pass": "pass", "review": "review", "block": "blocked", "incomplete": "needs_info"}


def _request(messages: List[dict]) -> dict:
    match = re.search(r"```json\n(.*?)\n```", messages[1]["content"], re.S)
    return json.loads(match.group(1))


def _history(messages: List[dict]) -> List[Tuple[str, dict, dict]]:
    calls, hist = {}, []
    for m in messages:
        if m["role"] == "assistant":
            for tc in m.get("tool_calls") or []:
                calls[tc["id"]] = (tc["function"]["name"], json.loads(tc["function"]["arguments"]))
        elif m["role"] == "tool":
            name, args = calls[m["tool_call_id"]]
            hist.append((name, args, json.loads(m["content"])))
    return hist


def _in_window(window: Optional[dict], slot: str) -> bool:
    return bool(window) and parse_slot(window["start"]) <= parse_slot(slot) <= parse_slot(window["end"])


class MockModel:
    label = "mock-rule-policy"

    def __init__(self):
        self._n = 0

    def complete(self, messages: List[dict], tools: List[dict]) -> ModelTurn:
        name, args = self._decide(_request(messages), _history(messages))
        self._n += 1
        return ModelTurn(content=None,
                         tool_calls=[ToolCall(f"mock-{self._n}", name, json.dumps(args, ensure_ascii=False))])

    def _decide(self, request: dict, hist: list) -> Tuple[str, dict]:
        if hist:
            name, args, res = hist[-1]
            if name != "finish" and not res.get("ok") and res["error"].get("retryable"):
                failures = 0
                for n, _, r in reversed(hist):
                    if n != name or r.get("ok"):
                        break
                    failures += 1
                if failures <= 2:
                    return name, {**args, "reason": f"{name} 返回可重试错误，重试"}

        reads, checks, lookups, queries, saves = {}, {}, {}, [], []
        for idx, (name, args, res) in enumerate(hist):
            if not res.get("ok") and name != "save_schedule_draft":
                continue
            if name == "get_material":
                reads[args["material_id"]] = res
            elif name == "check_rules":
                checks[args["material_id"]] = (idx, res)
            elif name == "lookup_license":
                lookups[args["material_id"]] = (idx, res)
            elif name == "query_slots":
                queries.append((args, res))
            elif name == "save_schedule_draft":
                saves.append(res)

        planned, outcome = [], {}
        for item in request["items"]:
            mid, channel = item["material_id"], item.get("channel")
            if mid not in reads:
                return "get_material", {"material_id": mid, "reason": "先读取素材元数据"}
            if not reads[mid]["found"]:
                outcome[mid] = self._needs_info(mid, [f"素材库中不存在 {mid}，请确认素材 ID"])
                continue
            conf = find_confirmation(request, mid)
            target = (conf or {}).get("approved_slot") or item.get("publish_at")
            if mid not in checks:
                return "check_rules", {"material_id": mid, "publish_at": target, "reason": "读取成功，按发布时间做规则检查"}
            idx, chk = checks[mid]
            license_missing = any(f["rule_id"] == "R01" and f["field"] == "license" for f in chk["findings"])
            if chk["result"] == "incomplete" and license_missing:
                if mid not in lookups:
                    return "lookup_license", {"material_id": mid, "reason": "版权信息缺失，先查登记库补查"}
                if lookups[mid][1]["found"] and lookups[mid][0] > idx:
                    return "check_rules", {"material_id": mid, "publish_at": target, "reason": "登记库有记录，重新检查"}
            if chk["result"] == "block":
                outcome[mid] = {"material_id": mid, "review_status": "blocked",
                                "risk_reasons": [f["message"] for f in chk["findings"] if f["severity"] in ("block", "review")],
                                "suggested_channel": None, "suggested_slot": None,
                                "confirmation_status": "not_applicable", "pending_items": [], "in_draft": False}
                continue
            if chk["result"] == "incomplete":
                outcome[mid] = self._needs_info(mid, [f"请补充：{f['message']}" for f in chk["findings"]
                                                      if f["severity"] == "missing"])
                continue
            if not target or not channel:
                outcome[mid] = self._needs_info(mid, ["请求缺少发布时间或渠道，请提供"])
                continue

            taken = [{"channel": p["channel"], "slot": p["slot"]} for p in planned]
            query = next((r for a, r in reversed(queries) if a.get("channel") == channel
                          and a.get("publish_at") == target and (a.get("also_taken") or []) == taken), None)
            if query is None:
                return "query_slots", {"channel": channel, "publish_at": target, "also_taken": taken,
                                       "reason": "审核可排期，查询目标时段"}
            note = ""
            if query["requested"]["status"] == "free":
                slot, cs = target, ("confirmed" if conf else "not_required")
            else:
                alts = query.get("alternatives") or []
                in_win = [a for a in alts if _in_window(item.get("acceptable_window"), a["slot"])]
                later = [a for a in alts if a["offset_minutes"] > 0]
                if in_win:
                    slot, cs = in_win[0]["slot"], "not_required"
                elif alts:
                    slot, cs = (later or alts)[0]["slot"], "pending"
                    note = f"{target} 不可用（{query['requested'].get('detail', '')}），建议改为 {slot}，需用户确认"
                else:
                    outcome[mid] = self._needs_info(
                        mid, [f"{target} 当日无可用时段，请指定其他日期"], REVIEW_MAP[chk["result"]],
                        [f["message"] for f in chk["findings"] if f["severity"] == "review"])
                    continue
            if chk["publish_date"] != slot[:10]:
                return "check_rules", {"material_id": mid, "publish_at": slot, "reason": "时段改到其他日期，重新检查"}
            risks = [f["message"] for f in chk["findings"] if f["severity"] == "review"]
            if chk["result"] == "review":
                cs = "pending"
                note = "；".join(filter(None, [note, "需人工复核：" + "、".join(risks)]))
            planned.append({"material_id": mid, "channel": channel, "slot": slot,
                            "confirmation_status": cs, "note": note})
            outcome[mid] = {"material_id": mid, "review_status": REVIEW_MAP[chk["result"]], "risk_reasons": risks,
                            "suggested_channel": channel, "suggested_slot": slot, "confirmation_status": cs,
                            "pending_items": [note] if note else [], "in_draft": False}

        saved = any(r.get("ok") for r in saves)
        if planned and not saved and not saves:
            return "save_schedule_draft", {"items": planned, "reason": "所有素材处理完毕，保存可排期条目为草稿"}
        for p in planned:
            o = outcome[p["material_id"]]
            o["in_draft"] = saved
            if not saved:
                err = saves[-1].get("error", {}).get("code") if saves else "UNKNOWN"
                o["pending_items"].append(f"草稿保存失败（{err}），未写入，请稍后重新提交")
        items = [outcome[i["material_id"]] for i in request["items"]]
        summary = f"共 {len(items)} 个素材，{len(planned)} 个{'已保存为草稿' if saved else '未能保存'}；未发布任何内容。"
        return "finish", {"items": items, "summary": summary, "reason": "全部素材已处理"}

    @staticmethod
    def _needs_info(mid: str, pending: List[str], review_status: str = "needs_info",
                    risks: Optional[List[str]] = None) -> dict:
        return {"material_id": mid, "review_status": review_status, "risk_reasons": risks or [],
                "suggested_channel": None, "suggested_slot": None, "confirmation_status": "not_applicable",
                "pending_items": pending, "in_draft": False}
