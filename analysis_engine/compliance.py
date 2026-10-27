from __future__ import annotations

import re

FORBIDDEN = [r"建议买入", r"建议卖出", r"强烈推荐", r"目标价", r"稳赚", r"保证收益"]


def compliance_violations(text: str) -> list[str]:
    return [pattern for pattern in FORBIDDEN if re.search(pattern, text, flags=re.IGNORECASE)]


def assert_compliant(text: str) -> None:
    violations = compliance_violations(text)
    if violations:
        raise ValueError("发现投资建议或收益承诺措辞：" + ", ".join(violations))
