from data_layer import load_claims


def test_every_claim_has_required_audit_fields():
    for claim in load_claims().values():
        assert claim.source_url.startswith(("http://", "https://"))
        assert claim.stars in {"⭐⭐⭐⭐", "⭐⭐⭐", "⭐⭐", "⭐"}
        assert claim.as_of and claim.report_period and claim.retrieved_at
        assert claim.evidence_type in {"事实", "计算", "历史数据支撑", "分析师共识", "逻辑推演"}
        assert claim.limitations


def test_source_star_mapping():
    expected = {"财报/公告":"⭐⭐⭐⭐", "扶摇/iFinD/行业权威":"⭐⭐⭐", "头部研报":"⭐⭐", "媒体":"⭐"}
    for claim in load_claims().values():
        assert claim.stars == expected[claim.source_label]
