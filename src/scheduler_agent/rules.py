"""确定性审核规则引擎：给出事实性的风险发现，审核结论由 Agent 基于这些发现给出。"""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from .domain import parse_date


def _finding(rule_id: str, severity: str, field: str, message: str, evidence: str = "") -> dict:
    out = {"rule_id": rule_id, "severity": severity, "field": field, "message": message}
    if evidence:
        out["evidence"] = evidence
    return out


def _empty(value) -> bool:
    return value is None or value == "" or value == [] or value == {}


def check_material(
    material: dict,
    rules: dict,
    publish_date: Optional[date] = None,
    registry_license: Optional[dict] = None,
) -> dict:
    """返回 {result, findings, license_source}。

    result: block（存在阻断项）> incomplete（资料缺失）> review（需人工复核）> pass。
    registry_license 仅在本次会话通过 lookup_license 查到登记记录时由工具层传入，
    模型不能自行提供版权信息。
    """
    cfg = rules["rules"]
    findings: List[dict] = []

    license_info = material.get("license")
    license_source = "metadata"
    if _empty(license_info) and registry_license:
        license_info = registry_license
        license_source = "registry"
    elif _empty(license_info):
        license_source = "none"

    # R01 必填字段
    for field in rules["required_fields"]:
        value = license_info if field == "license" else material.get(field)
        if _empty(value):
            hint = "；可查询版权登记库补查" if field == "license" else ""
            findings.append(_finding("R01", cfg["R01"]["severity"], field, f"缺少必填字段 {field}{hint}"))

    # R02 版权授权有效期
    if not _empty(license_info) and license_info.get("expires_at"):
        if publish_date is None:
            findings.append(_finding("R02", "info", "license.expires_at", "未提供发布日期，未校验版权有效期"))
        elif parse_date(license_info["expires_at"]) < publish_date:
            findings.append(_finding(
                "R02", cfg["R02"]["severity"], "license.expires_at",
                "版权授权在发布日前到期", f"授权到期 {license_info['expires_at']}，发布日 {publish_date}",
            ))

    # R03 背景音乐授权
    music = material.get("music") or {}
    if music.get("used"):
        if _empty(music.get("license_id")):
            findings.append(_finding("R03", cfg["R03"]["severity_missing"], "music.license_id", "使用了背景音乐但缺少音乐授权编号"))
        elif music.get("expires_at") and publish_date and parse_date(music["expires_at"]) < publish_date:
            findings.append(_finding(
                "R03", cfg["R03"]["severity_expired"], "music.expires_at",
                "音乐授权在发布日前到期", f"音乐授权到期 {music['expires_at']}，发布日 {publish_date}",
            ))

    text = f"{material.get('title') or ''} {material.get('caption') or ''}"

    # R04 广告法极限用语
    hits = [p for p in cfg["R04"]["phrases"] if p in text]
    if hits:
        findings.append(_finding("R04", cfg["R04"]["severity"], "caption", "包含广告法禁用的极限用语", "、".join(hits)))

    # R05 功效/医疗宣称（限定品类）
    if material.get("category") in cfg["R05"]["categories"]:
        hits = [p for p in cfg["R05"]["phrases"] if p in text]
        if hits:
            findings.append(_finding("R05", cfg["R05"]["severity"], "caption", "疑似功效/医疗宣称，需法务复核", "、".join(hits)))

    # R06 商业合作须标注广告
    if material.get("is_commercial") and not material.get("ad_label"):
        findings.append(_finding("R06", cfg["R06"]["severity"], "ad_label", "商业合作内容未标注“广告”"))

    # R07 肖像授权
    if material.get("has_person") and material.get("portrait_release") is not True:
        state = "未提供" if material.get("portrait_release") is None else "未回传"
        findings.append(_finding("R07", cfg["R07"]["severity"], "portrait_release", f"出镜人物肖像授权{state}"))

    severities = {f["severity"] for f in findings}
    if "block" in severities:
        result = "block"
    elif "missing" in severities:
        result = "incomplete"
    elif "review" in severities:
        result = "review"
    else:
        result = "pass"
    return {"result": result, "findings": findings, "license_source": license_source}
