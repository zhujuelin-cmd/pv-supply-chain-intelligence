from data_layer.adapters import FuyaoAdapter, IFindAdapter


def test_missing_credentials_unavailable_and_fallback(monkeypatch):
    for key in ("FUYAO_API_KEY", "API_KEY", "IFIND_API_KEY", "IFIND_MCP_TOKEN"):
        monkeypatch.delenv(key, raising=False)
    for adapter in (FuyaoAdapter(), IFindAdapter()):
        result = adapter.fetch()
        assert result["adapter"]["status"] == "unavailable"
        assert result["adapter"]["available"] is False
        assert result["adapter"]["fallback"] == "官方公开资料快照"
        assert result["data"] is None
