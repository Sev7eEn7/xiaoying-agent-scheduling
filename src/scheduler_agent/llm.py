"""模型接入：OpenAI 兼容 Chat Completions（函数调用），仅用标准库 urllib。"""

from __future__ import annotations

import json
import os
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-flash"


class LLMError(RuntimeError):
    pass


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: str  # 模型返回的原始 JSON 字符串


@dataclass
class ModelTurn:
    content: Optional[str]
    tool_calls: List[ToolCall] = field(default_factory=list)
    usage: dict = field(default_factory=dict)

    def to_message(self) -> dict:
        msg = {"role": "assistant", "content": self.content or ""}
        if self.tool_calls:
            msg["tool_calls"] = [
                {"id": c.id, "type": "function", "function": {"name": c.name, "arguments": c.arguments}}
                for c in self.tool_calls
            ]
        return msg


class OpenAICompatModel:
    def __init__(self, base_url: str, api_key: str, model: str, temperature: float = 0.0,
                 timeout: float = 90, max_retries: int = 3):
        if not api_key:
            raise LLMError("缺少 LLM_API_KEY：请复制 .env.example 为 .env 并填写，或使用 --provider mock 离线运行")
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries

    @property
    def label(self) -> str:
        return self.model

    def complete(self, messages: List[dict], tools: List[dict]) -> ModelTurn:
        body = json.dumps({
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": self.temperature,
        }, ensure_ascii=False).encode("utf-8")
        data = self._post(body)
        try:
            msg = data["choices"][0]["message"]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"模型响应格式异常：{str(data)[:300]}") from exc
        calls = [ToolCall(c["id"], c["function"]["name"], c["function"].get("arguments") or "{}")
                 for c in msg.get("tool_calls") or []]
        return ModelTurn(content=msg.get("content"), tool_calls=calls, usage=data.get("usage") or {})

    def _post(self, body: bytes) -> dict:
        """网络层重试（429/5xx/超时）。这只是传输重试，不参与业务决策。"""
        delay = 2.0
        for attempt in range(self.max_retries + 1):
            req = urllib.request.Request(self.url, data=body, method="POST", headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            })
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", "replace")[:500]
                if exc.code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise LLMError(f"模型接口返回 HTTP {exc.code}：{detail}") from exc
            except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
                if attempt < self.max_retries:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise LLMError(f"无法连接模型接口 {self.url}：{exc}") from exc
        raise LLMError("模型接口重试耗尽")


def load_dotenv(path: Path) -> None:
    """极简 .env 解析；不覆盖已存在的环境变量。"""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip('"').strip("'")
        if value:
            os.environ.setdefault(key.strip(), value)


def make_model(provider: str):
    if provider == "mock":
        from .mock_model import MockModel
        return MockModel()
    if provider in ("deepseek", "openai"):
        default_base = DEEPSEEK_BASE_URL if provider == "deepseek" else None
        default_model = DEEPSEEK_MODEL if provider == "deepseek" else None
        base_url = os.environ.get("LLM_BASE_URL") or default_base
        model = os.environ.get("LLM_MODEL") or default_model
        if not base_url or not model:
            raise LLMError("--provider openai 需要在 .env 中设置 LLM_BASE_URL 和 LLM_MODEL")
        return OpenAICompatModel(
            base_url=base_url,
            api_key=os.environ.get("LLM_API_KEY") or os.environ.get("DEEPSEEK_API_KEY", ""),
            model=model,
            temperature=float(os.environ.get("LLM_TEMPERATURE", "0")),
            timeout=float(os.environ.get("LLM_TIMEOUT_SEC", "90")),
        )
    raise LLMError(f"未知 provider {provider}，可选 mock / deepseek / openai")
