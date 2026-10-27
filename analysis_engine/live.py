from __future__ import annotations

from typing import Any

from data_layer.adapters import FuyaoAdapter, IFindAdapter


def fetch_live_pv_data() -> dict[str, Any]:
    """拉取关税情景需要的真实公司财务与产业链数据。"""
    fuyao_result = FuyaoAdapter().fetch_longi()
    ifind = IFindAdapter()
    ifind_probe = ifind.fetch()

    result: dict[str, Any] = {
        "fuyao": fuyao_result,
        "ifind_probe": ifind_probe,
        "ifind_longi": None,
        "ifind_chain": None,
        "errors": [],
    }
    if fuyao_result.get("errors"):
        result["errors"].extend(fuyao_result["errors"])

    if ifind_probe.get("adapter", {}).get("available"):
        try:
            result["ifind_longi"] = ifind.fetch_longi_financials()
        except Exception as exc:
            result["errors"].append(f"iFinD 隆基财务：{exc}")
        try:
            result["ifind_chain"] = ifind.fetch_pv_chain()
        except Exception as exc:
            result["errors"].append(f"iFinD 光伏产业链：{exc}")

    result["live_ok"] = bool(
        fuyao_result.get("adapter", {}).get("available")
        and result["ifind_longi"]
        and result["ifind_chain"]
    )
    return result


def validate_tariff_live_e2e() -> tuple[bool, list[dict[str, Any]], dict[str, Any]]:
    """验证关税情景的静态证据链与两条实时数据链。"""
    from .q2 import validate_tariff_e2e

    static_ok, evidence = validate_tariff_e2e()
    live = fetch_live_pv_data()
    checks = evidence + [
        {
            "step": "扶摇：隆基绿能最新年度财务",
            "ok": bool(live.get("fuyao", {}).get("adapter", {}).get("available")),
            "claim_ids": ["FUYAO-601012-LIVE"],
        },
        {
            "step": "iFinD：隆基财务与光伏产业链",
            "ok": bool(live.get("ifind_longi") and live.get("ifind_chain")),
            "claim_ids": ["IFIND-LONGI-LIVE", "IFIND-PV-CHAIN-LIVE"],
        },
    ]
    return static_ok and live.get("live_ok", False), checks, live
