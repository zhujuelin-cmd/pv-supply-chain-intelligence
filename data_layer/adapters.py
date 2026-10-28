from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

import requests

from .models import AdapterStatus

ROOT = Path(__file__).resolve().parents[1]
HTTP = requests.Session()
HTTP.trust_env = False
IFIND_BASE = "https://api-mcp.51ifind.com:8643/ds-mcp-servers"
IFIND_SERVERS = {
    "stock": f"{IFIND_BASE}/hexin-ifind-ds-stock-mcp",
    "edb": f"{IFIND_BASE}/hexin-ifind-ds-edb-mcp",
}


def _load_project_env() -> None:
    """加载本地 .env 及 Streamlit Secrets；已由部署环境注入的变量优先。"""
    try:
        import streamlit as st
        for k, v in st.secrets.items():
            if isinstance(v, str):
                os.environ.setdefault(k, v)
    except Exception:
        pass
    path = ROOT / ".env"
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


_load_project_env()


class FuyaoAdapter:
    """扶摇 A 股财务数据 REST 适配器。"""

    env_names = ("FUYAO_API_KEY", "API_KEY")
    base_url = "https://fuyao.aicubes.cn"

    def _api_key(self) -> str | None:
        return next((os.getenv(name) for name in self.env_names if os.getenv(name)), None)

    def status(self) -> AdapterStatus:
        if not self._api_key():
            return AdapterStatus(
                "扶摇", False, "unavailable",
                "缺少 FUYAO_API_KEY/API_KEY；未发起网络请求",
                "官方公开资料快照",
            )
        return AdapterStatus(
            "扶摇", True, "configured",
            "API Key 已配置，可读取 A 股利润表",
            "扶摇 API",
        )

    def fetch(self, tickers: Iterable[str] = ("600438.SH", "601012.SH", "688223.SH", "300274.SZ")) -> dict[str, Any]:
        key = self._api_key()
        if not key:
            return {"adapter": asdict(self.status()), "data": None, "errors": []}
        rows: list[dict[str, Any]] = []
        errors: list[str] = []
        endpoint = f"{self.base_url}/api/a-share/financials/income-statements"
        for ticker in tickers:
            try:
                response = HTTP.get(
                    endpoint,
                    params={"thscode": ticker, "period": "annual", "limit": 3},
                    headers={"X-api-key": key},
                    timeout=20,
                )
                response.raise_for_status()
                payload = response.json()
                if payload.get("code") not in (None, 0, 200):
                    raise RuntimeError(f"业务错误 code={payload.get('code')}: {payload.get('message', '')}")
                items = payload.get("data", {}).get("item", [])
                rows.append({"ticker": ticker, "items": items, "raw": payload})
            except Exception as exc:
                errors.append(f"{ticker}: {exc}")
        available = any(row.get("items") for row in rows)
        status = AdapterStatus(
            "扶摇", available, "available" if available else "unavailable",
            "；".join(errors) if errors and not available else f"成功读取 {sum(len(row['items']) for row in rows)} 条财务记录",
            "扶摇 API" if available else "官方公开资料快照",
        )
        return {"adapter": asdict(status), "data": rows or None, "errors": errors}

    def fetch_longi(self) -> dict[str, Any]:
        return self.fetch(("601012.SH",))


class IFindAdapter:
    """iFinD Streamable HTTP MCP 客户端，支持股票财务与行业经济数据。"""

    env_names = ("IFIND_API_KEY", "IFIND_MCP_TOKEN")

    def __init__(self) -> None:
        self._sessions: dict[str, str] = {}
        self._request_ids: dict[str, int] = {}

    def _token(self) -> str | None:
        return next((os.getenv(name) for name in self.env_names if os.getenv(name)), None)

    def _url(self, server_type: str) -> str:
        custom = os.getenv("IFIND_MCP_URL")
        if custom and server_type == "stock":
            return custom
        return IFIND_SERVERS[server_type]

    def _next_id(self, server_type: str) -> int:
        self._request_ids[server_type] = self._request_ids.get(server_type, 0) + 1
        return self._request_ids[server_type]

    def _headers(self, server_type: str) -> dict[str, str]:
        headers = {
            "Authorization": self._token() or "",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "Aime",
        }
        if server_type in self._sessions:
            headers["Mcp-Session-Id"] = self._sessions[server_type]
        return headers

    def _post(self, server_type: str, payload: dict[str, Any], timeout: int = 60) -> tuple[requests.Response, Any]:
        response = HTTP.post(
            self._url(server_type),
            headers=self._headers(server_type),
            json=payload,
            timeout=timeout,
        )
        data: Any = None
        if response.text.strip():
            try:
                data = response.json()
            except ValueError:
                data = response.text
        return response, data

    def _initialize(self, server_type: str) -> None:
        if server_type in self._sessions:
            return
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(server_type),
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "pv-supply-chain-intelligence", "version": "2.0.0"},
            },
        }
        response, data = self._post(server_type, payload, timeout=30)
        response.raise_for_status()
        session_id = response.headers.get("Mcp-Session-Id")
        if not session_id:
            raise RuntimeError(f"initialize 未返回 Mcp-Session-Id: {data}")
        self._sessions[server_type] = session_id
        notify = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        response, _ = self._post(server_type, notify, timeout=15)
        response.raise_for_status()

    def _rpc(self, server_type: str, method: str, params: dict[str, Any]) -> Any:
        self._initialize(server_type)
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(server_type),
            "method": method,
            "params": params,
        }
        response, data = self._post(server_type, payload)
        response.raise_for_status()
        if isinstance(data, dict) and data.get("error"):
            raise RuntimeError(str(data["error"]))
        return data

    @staticmethod
    def _extract_answer(payload: Any) -> dict[str, Any]:
        try:
            content = payload["result"]["content"]
            text = next(item["text"] for item in content if item.get("type") == "text")
            parsed = json.loads(text)
            body = parsed.get("data", {})
            return {
                "answer": body.get("answer") or body.get("data") or text,
                "indicator_description": body.get("indicator_description", []),
                "raw": parsed,
            }
        except (KeyError, TypeError, StopIteration, json.JSONDecodeError):
            return {"answer": str(payload), "indicator_description": [], "raw": payload}

    def status(self) -> AdapterStatus:
        if not self._token():
            return AdapterStatus(
                "iFinD", False, "unavailable",
                "缺少 IFIND_API_KEY/IFIND_MCP_TOKEN；未发起网络请求",
                "官方公开资料快照",
            )
        return AdapterStatus("iFinD", True, "configured", "API Key 已配置，可连接官方 MCP", "iFinD MCP")

    def list_tools(self, server_type: str = "stock") -> dict[str, Any]:
        return self._rpc(server_type, "tools/list", {})

    def call(self, server_type: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        payload = self._rpc(server_type, "tools/call", {"name": tool_name, "arguments": arguments})
        return self._extract_answer(payload)

    def fetch(self) -> dict[str, Any]:
        if not self._token():
            return {"adapter": asdict(self.status()), "data": None, "errors": []}
        try:
            payload = self.list_tools("stock")
            tools = payload.get("result", {}).get("tools", [])
            status = AdapterStatus("iFinD", True, "available", f"MCP 探测成功，可用工具 {len(tools)} 个", "iFinD MCP")
            return {"adapter": asdict(status), "data": {"tools_count": len(tools)}, "errors": []}
        except Exception as exc:
            status = AdapterStatus("iFinD", False, "unavailable", f"MCP 探测失败：{exc}", "官方公开资料快照")
            return {"adapter": asdict(status), "data": None, "errors": [str(exc)]}

    def fetch_longi_financials(self) -> dict[str, Any]:
        return self.call(
            "stock",
            "get_stock_financials",
            {"query": "隆基绿能601012最新年度营业收入、净利润、毛利率、海外收入和存货"},
        )

    def fetch_pv_chain(self) -> dict[str, Any]:
        return self.call(
            "edb",
            "get_edb_data",
            {"query": "多晶硅产量当月值、太阳能电池产量当月值、太阳能电池出口数量累计值（202501-202609）"},
        )


def interface_statuses() -> list[AdapterStatus]:
    return [FuyaoAdapter().status(), IFindAdapter().status()]
