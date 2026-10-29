"""数据加载与时段格式工具。"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

SLOT_FORMAT = "%Y-%m-%dT%H:%M"
CHANNELS = ("douyin", "xiaohongshu")


def load_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_materials(path: Optional[Path] = None) -> Dict[str, dict]:
    raw = load_json(path or DATA_DIR / "materials.json")
    return {m["id"]: m for m in raw["materials"]}


def load_rules(path: Optional[Path] = None) -> dict:
    return load_json(path or DATA_DIR / "rules.json")


def load_registry(path: Optional[Path] = None) -> Dict[str, dict]:
    return load_json(path or DATA_DIR / "license_registry.json")["records"]


def load_schedule(path: Optional[Path] = None) -> list:
    return load_json(path or DATA_DIR / "schedule.json")["slots"]


def parse_slot(value: str) -> datetime:
    """解析 'YYYY-MM-DDTHH:MM'，格式错误抛出 ValueError。"""
    return datetime.strptime(value, SLOT_FORMAT)


def format_slot(value: datetime) -> str:
    return value.strftime(SLOT_FORMAT)


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def request_items(request: dict) -> Dict[str, dict]:
    return {item["material_id"]: item for item in request.get("items", [])}


def find_confirmation(request: dict, material_id: str) -> Optional[dict]:
    for c in request.get("confirmations") or []:
        if c.get("material_id") == material_id:
            return c
    return None
