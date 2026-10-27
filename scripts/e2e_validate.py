from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis_engine.q2 import validate_tariff_e2e


def main() -> int:
    passed, evidence = validate_tariff_e2e()
    print("美国加征25%关税｜五步端到端证据验收")
    for index, item in enumerate(evidence, 1):
        status = "PASS" if item["ok"] else "FAIL"
        print(f"{index}. {status} | {item['step']} | evidence={','.join(item['claim_ids'])}")
    print("RESULT=" + ("PASS" if passed else "FAIL"))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
