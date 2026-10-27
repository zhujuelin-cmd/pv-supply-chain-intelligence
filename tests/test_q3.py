from analysis_engine.q3 import validate_sunpower_break


def test_sunpower_continuity_break():
    assert validate_sunpower_break() == []
