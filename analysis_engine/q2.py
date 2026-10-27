from __future__ import annotations

from data_layer.repository import load_claims, load_q2

REQUIRED_SCENARIOS = {"POLY_20", "US_TARIFF_25", "EU_TARGET_UP", "PEROVSKITE_BREAK"}
TARIFF_STEPS = ["组件出口与税率口径", "晶科/隆基暴露", "海外收入/毛利/库存指标", "First Solar美国本土制造与范围差异", "45X与关税保护分离"]


def graphviz_for(scenario: dict) -> str:
    nodes = scenario["graph"]
    lines = ["digraph G {", 'rankdir=LR; bgcolor="transparent";', 'node [shape=box, style="rounded,filled", fillcolor="white", color="#123B66", fontname="Arial", fontsize=10];', 'edge [color="#123B66"];']
    for index, node in enumerate(nodes):
        safe = node.replace('"', "'")
        lines.append(f'n{index} [label="{safe}"];')
        if index:
            lines.append(f"n{index-1} -> n{index};")
    lines.append("}")
    return "\n".join(lines)


def validate_scenarios() -> list[str]:
    rows = load_q2()
    errors: list[str] = []
    if {row["scenario_id"] for row in rows} != REQUIRED_SCENARIOS:
        errors.append("四个固定情景不完整")
    for row in rows:
        if {item["period"] for item in row["matrix"]} != {"0–3月", "3–12月", "1年以上"}:
            errors.append(f"{row['scenario_id']}: 三时间段不完整")
        if not row.get("graph") or not row.get("claim_ids"):
            errors.append(f"{row['scenario_id']}: 图或证据缺失")
    return errors


def validate_tariff_e2e() -> tuple[bool, list[dict]]:
    scenario = next(item for item in load_q2() if item["scenario_id"] == "US_TARIFF_25")
    claims = load_claims()
    evidence = []
    for expected, row in zip(TARIFF_STEPS, scenario.get("e2e_steps", [])):
        ids = row.get("claim_ids", [])
        ok = row.get("step") == expected and bool(ids) and all(item in claims for item in ids)
        evidence.append({"step": expected, "ok": ok, "claim_ids": ids})
    return len(evidence) == 5 and all(item["ok"] for item in evidence), evidence
