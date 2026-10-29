"""时段占用查询：已确认排期 + 其他请求的草稿占位 + 本批次已规划时段。"""

from __future__ import annotations

from datetime import timedelta
from typing import Iterable, List, Optional, Tuple

from .domain import CHANNELS, format_slot, parse_slot


class SlotBook:
    def __init__(self, schedule: list, rules: dict, holds: Optional[list] = None):
        policy = rules["slot_policy"]
        self.first_hour = policy["publish_hours"]["first"]
        self.last_hour = policy["publish_hours"]["last"]
        self.occupied = {(s["channel"], s["slot"]): s for s in schedule}
        self.held = {(h["channel"], h["slot"]): h for h in holds or []}

    def validate(self, channel: str, slot: str) -> Optional[str]:
        """返回错误说明；合法时返回 None。"""
        if channel not in CHANNELS:
            return f"未知渠道 {channel}，可选：{', '.join(CHANNELS)}"
        try:
            dt = parse_slot(slot)
        except (TypeError, ValueError):
            return f"时间格式应为 YYYY-MM-DDTHH:MM，收到 {slot!r}"
        if dt.minute != 0:
            return "发布时间须为整点"
        if not (self.first_hour <= dt.hour <= self.last_hour):
            return f"{dt.hour:02d}:00 不在可发布时段 {self.first_hour:02d}:00-{self.last_hour:02d}:00"
        return None

    def status(self, channel: str, slot: str, also_taken: Iterable[Tuple[str, str]] = ()) -> dict:
        error = self.validate(channel, slot)
        if error:
            return {"slot": slot, "status": "invalid", "detail": error}
        key = (channel, slot)
        if key in self.occupied:
            s = self.occupied[key]
            return {"slot": slot, "status": "occupied",
                    "detail": f"已被排期 {s['schedule_id']}（{s['material_id']} {s['title']}）占用"}
        if key in self.held:
            h = self.held[key]
            return {"slot": slot, "status": "held_by_draft",
                    "detail": f"已被其他请求的草稿 {h['draft_id']}（{h['material_id']}）占位"}
        if key in set(also_taken):
            return {"slot": slot, "status": "planned_in_batch", "detail": "本批次已规划给其他素材"}
        return {"slot": slot, "status": "free"}

    def alternatives(self, channel: str, slot: str, also_taken: Iterable[Tuple[str, str]] = (),
                     limit: int = 4) -> List[dict]:
        """同日最近的空闲整点；距离相同优先晚于原时间（素材可能尚未就绪）。同日无空位时看次日。"""
        taken = list(also_taken)
        requested = parse_slot(slot)
        for day_offset in (0, 1):
            day = requested.replace(hour=0) + timedelta(days=day_offset)
            candidates = []
            for hour in range(self.first_hour, self.last_hour + 1):
                cand = day.replace(hour=hour)
                if cand == requested:
                    continue
                cand_str = format_slot(cand)
                if self.status(channel, cand_str, taken)["status"] != "free":
                    continue
                offset = int((cand - requested).total_seconds() // 60)
                candidates.append((abs(offset), 0 if offset > 0 else 1, cand_str, offset))
            if candidates:
                candidates.sort()
                return [{"slot": c[2], "offset_minutes": c[3]} for c in candidates[:limit]]
        return []
