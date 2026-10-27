from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

EvidenceType = Literal["事实", "计算", "历史数据支撑", "分析师共识", "逻辑推演"]


@dataclass(frozen=True)
class Claim:
    claim_id: str
    statement: str
    source_label: str
    stars: str
    source_name: str
    source_url: str
    as_of: str
    report_period: str
    retrieved_at: str
    evidence_type: EvidenceType
    limitations: str
    metrics: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> "Claim":
        return cls(**row)

    def validate(self) -> list[str]:
        errors: list[str] = []
        required = ("claim_id", "statement", "source_label", "stars", "source_name", "source_url", "as_of", "report_period", "retrieved_at", "evidence_type", "limitations")
        for field in required:
            if not getattr(self, field):
                errors.append(f"{self.claim_id or '<unknown>'}: {field} 缺失")
        if not self.source_url.startswith(("https://", "http://")):
            errors.append(f"{self.claim_id}: URL 非 HTTP(S)")
        allowed = {"财报/公告": "⭐⭐⭐⭐", "扶摇/iFinD/行业权威": "⭐⭐⭐", "头部研报": "⭐⭐", "媒体": "⭐"}
        if allowed.get(self.source_label) != self.stars:
            errors.append(f"{self.claim_id}: 星级与来源标签不匹配")
        return errors


@dataclass(frozen=True)
class AdapterStatus:
    name: str
    available: bool
    status: str
    reason: str
    fallback: str
