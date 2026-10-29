"""排期草稿存储：按请求键幂等 upsert，原子写入 JSON 文件。只有草稿，没有发布。"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# 只有这些字段决定排期是否变化；note 等自由文本由模型生成、每次措辞不同，不参与判重
SEMANTIC_FIELDS = ("material_id", "channel", "slot", "confirmation_status", "review_result")


def content_hash(items: List[dict]) -> str:
    ordered = sorted(({k: i.get(k) for k in SEMANTIC_FIELDS} for i in items), key=lambda i: i["material_id"])
    return _sha(json.dumps(ordered, ensure_ascii=False, sort_keys=True))[:16]


def request_key(request: dict) -> str:
    """幂等键：优先使用调用方给的 request_id，否则用请求条目的规范化哈希。

    confirmations 不参与哈希：用户确认后的再次提交更新同一份草稿，而不是新建一份。
    """
    if request.get("request_id"):
        return str(request["request_id"])
    items = sorted(request.get("items", []), key=lambda i: i.get("material_id", ""))
    return "auto-" + _sha(json.dumps(items, ensure_ascii=False, sort_keys=True))[:12]


def draft_id_for(key: str) -> str:
    return "D-" + _sha(key)[:8].upper()


class DraftStore:
    def __init__(self, path: Path, clock: Optional[Callable[[], str]] = None):
        self.path = Path(path)
        self._clock = clock or (lambda: datetime.now().isoformat(timespec="seconds"))

    def _load(self) -> dict:
        if not self.path.exists():
            return {"drafts": {}}
        with open(self.path, encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), prefix=".drafts-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    def list_drafts(self) -> List[dict]:
        return list(self._load()["drafts"].values())

    def get(self, key: str) -> Optional[dict]:
        return self._load()["drafts"].get(draft_id_for(key))

    def holds(self, exclude_key: Optional[str] = None) -> List[dict]:
        """其他请求的草稿已排入的素材及其占用的时段（草稿占位，未发布）。"""
        out = []
        for draft in self._load()["drafts"].values():
            if draft["request_key"] == exclude_key:
                continue
            for item in draft["items"]:
                out.append({"channel": item["channel"], "slot": item["slot"], "draft_id": draft["draft_id"],
                            "material_id": item["material_id"], "request_key": draft["request_key"],
                            "confirmation_status": item.get("confirmation_status"),
                            "requested_channel": item.get("requested_channel"),
                            "requested_slot": item.get("requested_slot")})
        return out

    def upsert(self, key: str, items: List[dict]) -> dict:
        """同一请求键只保留一份草稿：内容相同返回 duplicate，内容不同产生新修订 updated。"""
        data = self._load()
        draft_id = draft_id_for(key)
        digest = content_hash(items)
        now = self._clock()
        existing = data["drafts"].get(draft_id)
        if existing and existing["content_hash"] == digest:
            return {"status": "duplicate", "draft_id": draft_id, "revision": existing["revision"],
                    "content_hash": digest}
        if existing:
            revision = existing["revision"] + 1
            history = existing["history"] + [{"revision": revision, "content_hash": digest, "at": now}]
            created_at = existing["created_at"]
            status = "updated"
        else:
            revision = 1
            history = [{"revision": 1, "content_hash": digest, "at": now}]
            created_at = now
            status = "created"
        data["drafts"][draft_id] = {
            "draft_id": draft_id,
            "request_key": key,
            "state": "draft",
            "revision": revision,
            "content_hash": digest,
            "items": sorted(items, key=lambda i: i["material_id"]),
            "created_at": created_at,
            "updated_at": now,
            "history": history,
        }
        self._write(data)
        return {"status": status, "draft_id": draft_id, "revision": revision, "content_hash": digest}
