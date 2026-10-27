from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis_engine import validate_tariff_live_e2e


def main() -> int:
    passed, evidence, live = validate_tariff_live_e2e()
    print("美国加征25%关税｜真实数据端到端验收")
    for index, item in enumerate(evidence, 1):
        status = "PASS" if item["ok"] else "FAIL"
        print(f"{index}. {status} | {item['step']} | evidence={','.join(item['claim_ids'])}")
    print(f"LIVE_DATA={'AVAILABLE' if live.get('live_ok') else 'UNAVAILABLE'}")
    if live.get("errors"):
        print("ERRORS=" + "；".join(live["errors"]))
    print("RESULT=" + ("PASS" if passed else "FAIL"))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
