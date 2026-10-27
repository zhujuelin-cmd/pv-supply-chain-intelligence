from data_layer import load_industry_background
from ui_components.pages import PAGES


def test_new_navigation_pages_are_ordered_before_q1():
    names = list(PAGES)
    assert names.index("📖 使用指南") < names.index("🏭 行业背景") < names.index("Q1 产业链证据")


def test_industry_background_sources_and_coverage():
    data = load_industry_background()
    sources = data["sources"]
    required_stages = {"多晶硅", "硅片", "电池片", "组件", "胶膜", "光伏玻璃", "边框与支架", "逆变器", "EPC", "电站运营与电网"}
    assert required_stages == {row["stage"] for row in data["stages"]}
    for row in data["stages"]:
        assert row["function"] and row["competition"] and row["companies"]
        assert row["source_ids"]
        assert all(source_id in sources for source_id in row["source_ids"])
    for source in sources.values():
        assert source["name"]
        assert source["url"].startswith("https://")


def test_industry_metrics_have_sources_and_caveats():
    data = load_industry_background()
    assert len(data["margin_reference"]) >= 10
    assert len(data["price_variables"]) == 4
    assert data["development"]["stage"]
    assert len(data["development"]["changes"]) >= 3
    assert len(data["development"]["markets"]) == 3
    assert "ifind" in data["sources"]
    assert all(item["source_id"] in data["sources"] for item in data["price_variables"])
