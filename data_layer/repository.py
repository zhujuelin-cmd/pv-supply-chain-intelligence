from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from .models import Claim

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DATA = ROOT / "data" / "public"


def _read_json(name: str) -> Any:
    with (PUBLIC_DATA / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def load_claims() -> dict[str, Claim]:
    claims = {row["claim_id"]: Claim.from_dict(row) for row in _read_json("claims.json")}
    errors = [error for claim in claims.values() for error in claim.validate()]
    if errors:
        raise ValueError("证据账本校验失败：" + "; ".join(errors))
    return claims


def load_q1() -> list[dict[str, Any]]:
    return _read_json("q1_chain.json")


def load_q2() -> list[dict[str, Any]]:
    return _read_json("q2_scenarios.json")


def load_q3() -> list[dict[str, Any]]:
    return _read_json("q3_comparables.json")


def resolve_claims(ids: list[str]) -> list[Claim]:
    ledger = load_claims()
    return [ledger[item] for item in ids]


def snapshot_metadata() -> dict[str, str]:
    return _read_json("metadata.json")
