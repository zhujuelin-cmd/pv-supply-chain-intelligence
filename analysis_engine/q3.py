from __future__ import annotations

from data_layer.repository import load_q3


def validate_sunpower_break() -> list[str]:
    pair = next((item for item in load_q3() if item["pair_id"] == "JINKO_SUNPOWER"), None)
    if not pair:
        return ["缺少晶科—SunPower组"]
    errors: list[str] = []
    if not pair.get("continuity_break"):
        errors.append("SunPower主体断点未标记")
    if "Q3-SUNPOWER-BREAK" not in pair.get("claim_ids", []):
        errors.append("SunPower主体断点缺少证据")
    return errors
