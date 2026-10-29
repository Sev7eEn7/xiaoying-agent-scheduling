import json

from conftest import REQ_CONFLICT

from scheduler_agent.store import DraftStore, request_key
from scheduler_agent.tools import check_rules, dispatch, query_slots, save_schedule_draft


def _item(slot="2026-11-03T19:00", cs="pending", note="18:00 被占用，建议 19:00，待确认", **kw):
    return {"material_id": "M01", "channel": "douyin", "slot": slot, "confirmation_status": cs, "note": note, **kw}


def test_store_upsert_is_idempotent_per_request(tmp_path):
    store = DraftStore(tmp_path / "d.json")
    a = [{"material_id": "M01", "channel": "douyin", "slot": "2026-11-03T19:00"}]
    b = [{"material_id": "M01", "channel": "douyin", "slot": "2026-11-03T18:00"}]
    assert store.upsert("REQ-X", a)["status"] == "created"
    dup = store.upsert("REQ-X", a)
    assert dup["status"] == "duplicate" and dup["revision"] == 1
    upd = store.upsert("REQ-X", b)
    assert upd["status"] == "updated" and upd["revision"] == 2 and upd["draft_id"] == dup["draft_id"]
    assert len(store.list_drafts()) == 1
    assert [h["revision"] for h in store.get("REQ-X")["history"]] == [1, 2]


def test_request_key_prefers_id_and_ignores_confirmations():
    assert request_key({"request_id": "R1", "items": []}) == "R1"
    base = {"items": [{"material_id": "M01", "channel": "douyin", "publish_at": "2026-11-03T18:00"}]}
    confirmed = {**base, "confirmations": [{"material_id": "M01", "approved_slot": "2026-11-03T19:00"}]}
    assert request_key(base) == request_key(confirmed)


def test_save_requires_rule_check_first(make_ctx):
    ctx = make_ctx(REQ_CONFLICT)
    res = save_schedule_draft(ctx, [_item()])
    assert not res["ok"] and res["saved"] is False
    assert "check_rules" in res["error"]["issues"][0]
    assert not ctx.store.path.exists()


def test_changing_user_slot_requires_pending(make_ctx):
    ctx = make_ctx(REQ_CONFLICT)
    check_rules(ctx, "M01", "2026-11-03T18:00")
    res = save_schedule_draft(ctx, [_item(cs="not_required", note="")])
    assert not res["ok"] and any("未经用户同意" in i for i in res["error"]["issues"])
    ok = save_schedule_draft(ctx, [_item()])
    assert ok["ok"] and ok["status"] == "created" and ok["state"] == "draft"


def test_occupied_slot_and_unconfirmed_claims_are_rejected(make_ctx):
    ctx = make_ctx(REQ_CONFLICT)
    check_rules(ctx, "M01", "2026-11-03T18:00")
    occupied = save_schedule_draft(ctx, [_item(slot="2026-11-03T18:00", cs="not_required", note="")])
    assert any("不可用" in i for i in occupied["error"]["issues"])
    fake = save_schedule_draft(ctx, [_item(cs="confirmed")])
    assert any("不能标记为 confirmed" in i for i in fake["error"]["issues"])


def test_user_confirmation_allows_confirmed(make_ctx):
    req = {**REQ_CONFLICT, "confirmations": [{"material_id": "M01", "approved_slot": "2026-11-03T19:00"}]}
    ctx = make_ctx(req)
    check_rules(ctx, "M01", "2026-11-03T19:00")
    assert save_schedule_draft(ctx, [_item(cs="confirmed", note="")])["ok"]


def test_acceptable_window_allows_change_without_confirmation(make_ctx):
    req = {"request_id": "REQ-W", "items": [
        {"material_id": "M09", "channel": "douyin", "publish_at": "2026-11-05T20:00"},
        {"material_id": "M10", "channel": "douyin", "publish_at": "2026-11-05T20:00",
         "acceptable_window": {"start": "2026-11-05T18:00", "end": "2026-11-05T22:00"}}]}
    ctx = make_ctx(req)
    check_rules(ctx, "M09", "2026-11-05T20:00")
    check_rules(ctx, "M10", "2026-11-05T20:00")
    clash = save_schedule_draft(ctx, [
        {"material_id": "M09", "channel": "douyin", "slot": "2026-11-05T20:00", "confirmation_status": "not_required"},
        {"material_id": "M10", "channel": "douyin", "slot": "2026-11-05T20:00", "confirmation_status": "not_required"}])
    assert any("本批次" in i for i in clash["error"]["issues"])
    ok = save_schedule_draft(ctx, [
        {"material_id": "M09", "channel": "douyin", "slot": "2026-11-05T20:00", "confirmation_status": "not_required"},
        {"material_id": "M10", "channel": "douyin", "slot": "2026-11-05T21:00", "confirmation_status": "not_required"}])
    assert ok["ok"]


def test_blocked_and_review_items(make_ctx):
    req = {"request_id": "REQ-R", "items": [
        {"material_id": "M04", "channel": "douyin", "publish_at": "2026-11-07T20:00"},
        {"material_id": "M06", "channel": "xiaohongshu", "publish_at": "2026-11-07T12:00"}]}
    ctx = make_ctx(req)
    check_rules(ctx, "M04", "2026-11-07T20:00")
    check_rules(ctx, "M06", "2026-11-07T12:00")
    blocked = save_schedule_draft(ctx, [{"material_id": "M04", "channel": "douyin", "slot": "2026-11-07T20:00",
                                         "confirmation_status": "pending", "note": "x"}])
    assert any("block" in i for i in blocked["error"]["issues"])
    review = save_schedule_draft(ctx, [{"material_id": "M06", "channel": "xiaohongshu", "slot": "2026-11-07T12:00",
                                        "confirmation_status": "not_required"}])
    assert any("人工复核" in i for i in review["error"]["issues"])
    ok = save_schedule_draft(ctx, [{"material_id": "M06", "channel": "xiaohongshu", "slot": "2026-11-07T12:00",
                                    "confirmation_status": "pending", "note": "肖像授权未回传，需人工复核"}])
    assert ok["ok"]


def test_moving_to_another_date_requires_recheck(make_ctx):
    ctx = make_ctx(REQ_CONFLICT)
    check_rules(ctx, "M01", "2026-11-03T18:00")
    res = save_schedule_draft(ctx, [_item(slot="2026-11-04T18:00")])
    assert any("重新 check_rules" in i for i in res["error"]["issues"])


def test_storage_failure_writes_nothing_and_is_reported(make_ctx):
    ctx = make_ctx(REQ_CONFLICT, inject=["save_fail"])
    check_rules(ctx, "M01", "2026-11-03T18:00")
    for _ in range(3):
        res = save_schedule_draft(ctx, [_item()])
        assert res == {"ok": False, "saved": False, "error": {
            "code": "STORAGE_UNAVAILABLE", "message": res["error"]["message"], "retryable": True}}
    assert not ctx.store.path.exists() and ctx.ledger.last_saved is None


def test_transient_failures_recover(make_ctx):
    ctx = make_ctx(REQ_CONFLICT, inject=["save_fail_once", "slots_fail_once"])
    assert not query_slots(ctx, "douyin", "2026-11-03T18:00")["ok"]
    assert query_slots(ctx, "douyin", "2026-11-03T18:00")["requested"]["status"] == "occupied"
    check_rules(ctx, "M01", "2026-11-03T18:00")
    assert not save_schedule_draft(ctx, [_item()])["ok"]
    assert save_schedule_draft(ctx, [_item()])["ok"]


def test_drafts_of_other_requests_hold_slots(make_ctx):
    first = make_ctx(REQ_CONFLICT)
    check_rules(first, "M01", "2026-11-03T18:00")
    assert save_schedule_draft(first, [_item()])["ok"]
    other = make_ctx({"request_id": "REQ-OTHER", "items": [
        {"material_id": "M07", "channel": "douyin", "publish_at": "2026-11-03T19:00"}]})
    res = query_slots(other, "douyin", "2026-11-03T19:00")
    assert res["requested"]["status"] == "held_by_draft"
    same = make_ctx(REQ_CONFLICT)  # 同一请求再次提交时不被自己的草稿挡住
    assert query_slots(same, "douyin", "2026-11-03T19:00")["requested"]["status"] == "free"


def test_dispatch_handles_bad_arguments(make_ctx):
    ctx = make_ctx(REQ_CONFLICT)
    assert dispatch(ctx, "nope", {})["error"]["code"] == "UNKNOWN_TOOL"
    assert dispatch(ctx, "get_material", {"wrong": 1})["error"]["code"] == "INVALID_ARGUMENT"
    assert dispatch(ctx, "query_slots", {"channel": "douyin", "publish_at": "tomorrow"})["error"]["code"] == "INVALID_ARGUMENT"
    assert dispatch(ctx, "get_material", {"material_id": "M404", "reason": "x"}) == {
        "ok": True, "found": False, "material_id": "M404"}
    json.dumps(dispatch(ctx, "check_rules", {"material_id": "M01"}))  # 结果可序列化


def test_note_wording_change_is_still_duplicate(tmp_path):
    # 真实模型每次写的 note 措辞不同；排期语义没变就不应产生新修订
    store = DraftStore(tmp_path / "d.json")
    base = {"material_id": "M01", "channel": "douyin", "slot": "2026-11-03T19:00",
            "confirmation_status": "pending", "review_result": "pass"}
    assert store.upsert("REQ-X", [{**base, "note": "18:00 被占用，建议 19:00"}])["status"] == "created"
    assert store.upsert("REQ-X", [{**base, "note": "原时段冲突，改到同日 19:00 待确认"}])["status"] == "duplicate"
    assert store.upsert("REQ-X", [{**base, "confirmation_status": "confirmed"}])["status"] == "updated"
