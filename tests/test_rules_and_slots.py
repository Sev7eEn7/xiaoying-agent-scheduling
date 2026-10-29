import copy
from datetime import date

from scheduler_agent.domain import load_materials, load_registry, load_rules, load_schedule
from scheduler_agent.rules import check_material
from scheduler_agent.slots import SlotBook

MATERIALS = load_materials()
RULES = load_rules()
PUBLISH = date(2026, 11, 7)


def _rule_ids(outcome):
    return {(f["rule_id"], f["severity"]) for f in outcome["findings"]}


def test_clean_material_passes():
    assert check_material(MATERIALS["M01"], RULES, PUBLISH)["result"] == "pass"
    assert check_material(MATERIALS["M02"], RULES, PUBLISH)["result"] == "pass"


def test_absolute_terms_block_and_claims_need_review():
    out = check_material(MATERIALS["M04"], RULES, PUBLISH)
    assert out["result"] == "block"
    ids = _rule_ids(out)
    assert ("R04", "block") in ids and ("R05", "review") in ids and ("R06", "review") in ids
    r04 = next(f for f in out["findings"] if f["rule_id"] == "R04")
    assert "最有效" in r04["evidence"] and "100%" in r04["evidence"]


def test_ordinary_words_do_not_trigger_absolute_terms():
    # “第一次带娃露营”含“第一”，但不是“销量第一”之类的极限用语
    out = check_material(MATERIALS["M05"], RULES, PUBLISH)
    assert "R04" not in {f["rule_id"] for f in out["findings"]}


def test_missing_license_is_incomplete_until_registry_supplements_it():
    out = check_material(MATERIALS["M03"], RULES, PUBLISH)
    assert out["result"] == "incomplete" and out["license_source"] == "none"
    supplemented = check_material(MATERIALS["M03"], RULES, PUBLISH, registry_license=load_registry()["M03"])
    assert supplemented["result"] == "pass" and supplemented["license_source"] == "registry"


def test_user_submission_missing_owner_license_and_music_license():
    out = check_material(MATERIALS["M05"], RULES, PUBLISH)
    assert out["result"] == "incomplete"
    fields = {f["field"] for f in out["findings"] if f["severity"] == "missing"}
    assert fields == {"owner", "license", "music.license_id"}


def test_portrait_release_not_returned_needs_review():
    out = check_material(MATERIALS["M06"], RULES, PUBLISH)
    assert out["result"] == "review" and ("R07", "review") in _rule_ids(out)


def test_license_and_music_expiry_depend_on_publish_date():
    m = copy.deepcopy(MATERIALS["M07"])
    m["license"]["expires_at"] = "2026-11-05"
    m["music"]["expires_at"] = "2026-11-06"
    assert check_material(m, RULES, date(2026, 11, 4))["result"] == "pass"
    late = check_material(m, RULES, date(2026, 11, 8))
    assert late["result"] == "block" and {("R02", "block"), ("R03", "block")} <= _rule_ids(late)


def test_occupied_slot_suggests_nearest_later_free_slot():
    book = SlotBook(load_schedule(), RULES)
    status = book.status("douyin", "2026-11-03T18:00")
    assert status["status"] == "occupied" and "S-1001" in status["detail"]
    alts = book.alternatives("douyin", "2026-11-03T18:00")
    assert alts[0] == {"slot": "2026-11-03T19:00", "offset_minutes": 60}
    assert "2026-11-03T17:00" not in [a["slot"] for a in alts]  # 17:00 也被占用


def test_slot_validation_and_batch_and_draft_holds():
    holds = [{"channel": "douyin", "slot": "2026-11-05T21:00", "draft_id": "D-OTHER", "material_id": "M99"}]
    book = SlotBook(load_schedule(), RULES, holds)
    assert book.status("douyin", "2026-11-05T03:00")["status"] == "invalid"
    assert book.status("douyin", "2026-11-05T20:30")["status"] == "invalid"
    assert book.status("weibo", "2026-11-05T20:00")["status"] == "invalid"
    assert book.status("douyin", "2026-11-05T21:00")["status"] == "held_by_draft"
    taken = [("douyin", "2026-11-05T20:00")]
    assert book.status("douyin", "2026-11-05T20:00", taken)["status"] == "planned_in_batch"
    alts = [a["slot"] for a in book.alternatives("douyin", "2026-11-05T20:00", taken)]
    assert "2026-11-05T19:00" not in alts and "2026-11-05T21:00" not in alts
    assert alts[0] == "2026-11-05T22:00"
