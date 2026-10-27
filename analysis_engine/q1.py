from __future__ import annotations

from data_layer.repository import load_q1


def validate_levels(rows: list[dict] | None = None) -> list[str]:
    rows = rows or load_q1()
    return [f"{row['company']}: 无收入证据却标记L1" for row in rows if row["level"] == "L1" and not row.get("income_evidence")]


def chain_summary() -> dict[str, int]:
    rows = load_q1()
    return {"公司数": len(rows), "L1收入证据": sum(row["level"] == "L1" for row in rows), "覆盖主环节": len({row["stage"] for row in rows})}
