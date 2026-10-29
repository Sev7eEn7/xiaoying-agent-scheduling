from conftest import REQ_CONFLICT, ScriptedModel

from scheduler_agent.agent import Limits, run_agent
from scheduler_agent.guard import build_report, validate_finish
from scheduler_agent.llm import LLMError
from scheduler_agent.tools import check_rules, save_schedule_draft

SAVE_ITEM = {"material_id": "M01", "channel": "douyin", "slot": "2026-11-03T19:00",
             "confirmation_status": "pending", "note": "18:00 被占用，建议 19:00，待确认"}


def _finish_item(**kw):
    item = {"material_id": "M01", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin",
            "suggested_slot": "2026-11-03T19:00", "confirmation_status": "pending",
            "pending_items": ["18:00 被占用，建议 19:00，待确认"], "in_draft": True}
    item.update(kw)
    return item


def _finish(**kw):
    return {"items": [_finish_item(**kw)], "summary": "建议 19:00，待确认", "reason": "完成"}


def test_finish_cannot_claim_unsaved_draft(make_ctx):
    ctx = make_ctx(REQ_CONFLICT)
    check_rules(ctx, "M01", "2026-11-03T18:00")
    issues = validate_finish(ctx, _finish())
    assert any("没有包含该素材的成功保存记录" in i for i in issues)


def test_finish_rejects_publish_claims_and_wrong_review(make_ctx):
    ctx = make_ctx(REQ_CONFLICT)
    check_rules(ctx, "M01", "2026-11-03T18:00")
    save_schedule_draft(ctx, [SAVE_ITEM])
    assert validate_finish(ctx, _finish()) == []
    bad = _finish(review_status="review")
    bad["summary"] = "M01 已发布到 19:00"
    issues = validate_finish(ctx, bad)
    assert any("已发布" in i for i in issues) and any("不一致" in i for i in issues)
    assert any("与草稿中的时段" in i for i in validate_finish(ctx, _finish(suggested_slot="2026-11-03T18:00")))


def test_report_marks_save_failure_explicitly(make_ctx):
    ctx = make_ctx(REQ_CONFLICT, inject=["save_fail"])
    check_rules(ctx, "M01", "2026-11-03T18:00")
    save_schedule_draft(ctx, [SAVE_ITEM])
    claim = validate_finish(ctx, _finish())
    assert any("成功保存记录" in i for i in claim)
    report = build_report(ctx, _finish(in_draft=False), stats={})
    assert report["task_status"] == "save_failed"
    assert report["draft"]["status"] == "failed" and report["items"][0]["draft_status"] == "save_failed"
    assert report["publish_status"] == "not_published"


def test_happy_path_loop_with_parallel_finish_processed_last(make_ctx):
    ctx = make_ctx(REQ_CONFLICT)
    model = ScriptedModel([
        [("check_rules", {"material_id": "M01", "publish_at": "2026-11-03T18:00", "reason": "r"})],
        # finish 与 save 同一轮返回：循环先执行 save，再校验 finish
        [("finish", _finish()), ("save_schedule_draft", {"items": [SAVE_ITEM], "reason": "r"})],
    ])
    result = run_agent(ctx, model)
    assert result.report["task_status"] == "needs_confirmation"
    assert result.report["draft"]["status"] == "created"
    assert [e["tool"] for e in result.trace] == ["check_rules", "save_schedule_draft", "finish"]


def test_rejected_finish_is_returned_to_model_and_can_be_fixed(make_ctx):
    ctx = make_ctx(REQ_CONFLICT)
    model = ScriptedModel([
        [("check_rules", {"material_id": "M01", "publish_at": "2026-11-03T18:00", "reason": "r"})],
        [("finish", _finish())],  # 还没保存就声称在草稿中
        [("save_schedule_draft", {"items": [SAVE_ITEM], "reason": "按退回意见保存"})],
        [("finish", _finish())],
    ])
    result = run_agent(ctx, model)
    assert result.report["task_status"] == "needs_confirmation"
    assert result.report["stats"]["finish_rejections"] == 1
    assert model.seen[2]["role"] == "tool" and "REPORT_REJECTED" in model.seen[2]["content"]


def test_repeated_bad_finish_ends_incomplete(make_ctx):
    ctx = make_ctx(REQ_CONFLICT)
    model = ScriptedModel([[("finish", _finish())]], repeat_last=True)
    result = run_agent(ctx, model, Limits(max_finish_rejections=2))
    assert result.report["task_status"] == "incomplete"
    assert result.report["incomplete_reason"].startswith("REPORT_REJECTED")
    assert result.report["items"][0]["draft_status"] == "not_saved"


def test_step_limit_returns_incomplete(make_ctx):
    ctx = make_ctx(REQ_CONFLICT)
    model = ScriptedModel([[("get_material", {"material_id": "M01", "reason": "r"})]], repeat_last=True)
    result = run_agent(ctx, model, Limits(max_turns=4))
    assert result.report["task_status"] == "incomplete"
    assert result.report["incomplete_reason"].startswith("STEP_LIMIT_REACHED")
    assert result.report["stats"]["model_turns"] == 4 and result.trace[-1]["type"] == "stopped"


def test_tool_call_limit_returns_incomplete(make_ctx):
    ctx = make_ctx(REQ_CONFLICT)
    burst = [("get_material", {"material_id": "M01", "reason": "r"})] * 5
    result = run_agent(ctx, ScriptedModel([burst], repeat_last=True), Limits(max_tool_calls=7))
    assert result.report["incomplete_reason"].startswith("TOOL_CALL_LIMIT_REACHED")
    assert result.report["stats"]["tool_calls"] == 7


def test_invalid_json_and_text_reply_are_fed_back(make_ctx):
    ctx = make_ctx(REQ_CONFLICT)
    model = ScriptedModel(["我先想一想", [("get_material", "{not json")]], repeat_last=False)
    result = run_agent(ctx, model, Limits(max_turns=3))
    assert result.trace[0]["type"] == "text"
    assert result.trace[1]["result"]["error"]["code"] == "INVALID_JSON"
    assert model.seen[1]["role"] == "user"  # 纯文本回复后提示继续使用工具


def test_model_error_returns_incomplete_with_facts(make_ctx):
    class Broken:
        label = "broken"

        def complete(self, messages, tools):
            raise LLMError("HTTP 401")

    result = run_agent(make_ctx(REQ_CONFLICT), Broken())
    assert result.report["task_status"] == "incomplete"
    assert "MODEL_ERROR" in result.report["incomplete_reason"]


def test_task_status_uses_structured_fields_not_free_text(make_ctx):
    ctx = make_ctx(REQ_CONFLICT)
    check_rules(ctx, "M01", "2026-11-03T18:00")
    item = {**SAVE_ITEM, "slot": "2026-11-03T19:00"}
    save_schedule_draft(ctx, [item])
    info_only = build_report(ctx, _finish(pending_items=["说明：已避开 18:00 的占用"], confirmation_status="pending"),
                             stats={})
    assert info_only["task_status"] == "needs_confirmation"
    ctx2 = make_ctx({"request_id": "REQ-F", "items": [
        {"material_id": "M07", "channel": "douyin", "publish_at": "2026-11-04T19:00"}]})
    check_rules(ctx2, "M07", "2026-11-04T19:00")
    save_schedule_draft(ctx2, [{"material_id": "M07", "channel": "douyin", "slot": "2026-11-04T19:00",
                                "confirmation_status": "not_required"}])
    fin = {"items": [{"material_id": "M07", "review_status": "pass", "risk_reasons": [], "suggested_channel": "douyin",
                      "suggested_slot": "2026-11-04T19:00", "confirmation_status": "not_required",
                      "pending_items": ["说明：按原时段排期"], "in_draft": True}], "summary": "ok"}
    assert validate_finish(ctx2, fin) == []
    assert build_report(ctx2, fin, stats={})["task_status"] == "completed"
