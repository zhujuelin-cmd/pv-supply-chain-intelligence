from analysis_engine.compliance import compliance_violations
from data_layer import load_claims, load_industry_background, load_q1, load_q2, load_q3


def test_forbidden_advice_detected():
    assert compliance_violations("建议买入并保证收益")


def test_product_data_has_no_trading_advice():
    corpus = " ".join([str(load_q1()), str(load_q2()), str(load_q3()), str(load_industry_background())] + [claim.statement for claim in load_claims().values()])
    assert compliance_violations(corpus) == []
