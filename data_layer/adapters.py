from __future__ import annotations

import os
from dataclasses import asdict
from typing import Iterable

import requests

from .models import AdapterStatus


class FuyaoAdapter:
    """扶摇 REST 适配器；无凭据或请求失败时只返回不可用状态。"""

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
            "检测到 API Key；可按需请求 A 股利润表",
            "扶摇API",
        )

    def fetch(self, tickers: Iterable[str] = ("600438.SH", "601012.SH", "688223.SH", "300274.SZ")) -> dict:
        key = self._api_key()
        if not key:
            return {"adapter": asdict(self.status()), "data": None}
        rows, errors = [], []
        endpoint = f"{self.base_url}/api/a-share/financials/income-statements"
        for ticker in tickers:
            try:
                response = requests.get(
                    endpoint,
                    params={"thscode": ticker, "period": "annual", "limit": 3},
                    headers={"X-api-key": key},
                    timeout=10,
                )
                response.raise_for_status()
                payload = response.json()
                if payload.get("code") not in (None, 0, 200):
                    raise RuntimeError(f"业务错误 code={payload.get('code')}: {payload.get('message', '')}")
                rows.append({"ticker": ticker, "payload": payload})
            except Exception as exc:  # 网络与供应商错误统一显式降级
                errors.append(f"{ticker}: {exc}")
        available = bool(rows)
        status = AdapterStatus(
            "扶摇", available, "available" if available else "unavailable",
            "；".join(errors) if errors else f"成功读取 {len(rows)} 个标的",
            "扶摇API" if available else "官方公开资料快照",
        )
        return {"adapter": asdict(status), "data": rows or None, "errors": errors}


class IFindAdapter:
    """iFinD MCP HTTP 适配器；URL 与令牌均由部署环境注入。"""

    env_names = ("IFIND_API_KEY", "IFIND_MCP_TOKEN")

    def _token(self) -> str | None:
        return next((os.getenv(name) for name in self.env_names if os.getenv(name)), None)

    def status(self) -> AdapterStatus:
        token, url = self._token(), os.getenv("IFIND_MCP_URL")
        if not token or not url:
            missing = []
            if not token:
                missing.append("IFIND_API_KEY/IFIND_MCP_TOKEN")
            if not url:
                missing.append("IFIND_MCP_URL")
            return AdapterStatus(
                "iFinD", False, "unavailable",
                f"缺少 {'、'.join(missing)}；当前无活动 iFinD MCP，未发起请求",
                "官方公开资料快照",
            )
        return AdapterStatus("iFinD", True, "configured", "MCP URL 与令牌已配置，可执行 tools/list 探测", "iFinD MCP")

    def fetch(self) -> dict:
        token, url = self._token(), os.getenv("IFIND_MCP_URL")
        if not token or not url:
            return {"adapter": asdict(self.status()), "data": None}
        try:
            response = requests.post(
                url,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("error"):
                raise RuntimeError(str(payload["error"]))
            status = AdapterStatus("iFinD", True, "available", "MCP tools/list 探测成功", "iFinD MCP")
            return {"adapter": asdict(status), "data": payload.get("result")}
        except Exception as exc:
            status = AdapterStatus("iFinD", False, "unavailable", f"MCP 探测失败：{exc}", "官方公开资料快照")
            return {"adapter": asdict(status), "data": None}


def interface_statuses() -> list[AdapterStatus]:
    return [FuyaoAdapter().status(), IFindAdapter().status()]
