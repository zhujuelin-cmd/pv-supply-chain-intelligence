from analysis_engine.q1 import validate_levels
from data_layer import load_q1


def test_no_income_cannot_be_l1():
    assert validate_levels() == []
    for row in load_q1():
        if row["level"] == "L1":
            assert row["income_evidence"] is True


def test_required_chain_stages():
    stages = {row["stage"] for row in load_q1()}
    assert stages == {"多晶硅", "硅片", "电池片", "组件", "胶膜/玻璃/支架", "逆变器", "EPC", "运营"}
