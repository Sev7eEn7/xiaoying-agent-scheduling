import json
import os

from scheduler_agent.evaluation import run_suite
from scheduler_agent.llm import LLMError, OpenAICompatModel, load_dotenv, make_model


def test_all_scenarios_pass_with_offline_mock(tmp_path):
    """离线 Mock 只证明循环、工具、校验、落盘的流程正确，不代表真实模型的决策效果。"""
    summary = run_suite("mock", tmp_path)
    failed = {s["id"]: s["failed_checks"] for s in summary if s["failed_checks"]}
    assert not failed, failed
    assert len(summary) == 11
    assert (tmp_path / "02_conflict" / "trace.md").exists()


def test_openai_compat_parses_tool_calls(monkeypatch):
    model = OpenAICompatModel("https://example.invalid/v1", "sk-test", "m")
    captured = {}

    def fake_post(body):
        captured["body"] = json.loads(body)
        return {"choices": [{"message": {"content": None, "tool_calls": [
            {"id": "call_1", "type": "function",
             "function": {"name": "get_material", "arguments": "{\"material_id\": \"M01\"}"}}]}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}}

    monkeypatch.setattr(model, "_post", fake_post)
    turn = model.complete([{"role": "user", "content": "hi"}], [{"type": "function", "function": {"name": "x"}}])
    assert captured["body"]["tool_choice"] == "auto" and captured["body"]["model"] == "m"
    assert turn.tool_calls[0].name == "get_material"
    msg = turn.to_message()
    assert msg["content"] == "" and msg["tool_calls"][0]["id"] == "call_1"
    assert turn.usage["prompt_tokens"] == 10


def test_missing_key_and_unknown_provider(monkeypatch):
    for k in ("LLM_API_KEY", "DEEPSEEK_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    try:
        make_model("deepseek")
        raise AssertionError("expected LLMError")
    except LLMError as exc:
        assert "--provider mock" in str(exc)
    try:
        make_model("gpt-x")
        raise AssertionError("expected LLMError")
    except LLMError:
        pass


def test_dotenv_does_not_override_existing_env(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("LLM_MODEL=from-file\nLLM_TEMPERATURE=0.3\n# comment\nEMPTY=\n", encoding="utf-8")
    monkeypatch.setenv("LLM_MODEL", "from-shell")
    monkeypatch.delenv("LLM_TEMPERATURE", raising=False)
    load_dotenv(env)
    assert os.environ["LLM_MODEL"] == "from-shell" and os.environ["LLM_TEMPERATURE"] == "0.3"
    assert "EMPTY" not in os.environ
