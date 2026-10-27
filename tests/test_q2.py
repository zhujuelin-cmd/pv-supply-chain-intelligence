from analysis_engine.q2 import validate_scenarios, validate_tariff_e2e


def test_four_scenarios_and_three_periods_complete():
    assert validate_scenarios() == []


def test_us_tariff_end_to_end():
    passed, evidence = validate_tariff_e2e()
    assert passed
    assert len(evidence) == 5
    assert all(row["claim_ids"] for row in evidence)
