"""CustomCat API client."""

from __future__ import annotations

from typing import Any

import httpx

CUSTOMCAT_BASE = "https://customcat-beta.mylocker.net/api/v1"


class CustomCatAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class CustomCatClient:
    def __init__(self, api_key: str, *, sandbox: bool = False, timeout: float = 60.0):
        self._api_key = api_key
        self._sandbox = sandbox
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{CUSTOMCAT_BASE}{path}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.request(method, url, headers=self._headers(), json=json)
        try:
            data = resp.json()
        except Exception:
            data = {"raw": resp.text}
        if resp.status_code >= 400:
            message = resp.text
            if isinstance(data, dict):
                message = str(data.get("message") or data.get("error") or resp.text)
            raise CustomCatAPIError(message, status_code=resp.status_code, body=data)
        return data

    async def get_catalog(self) -> Any:
        return await self._request("GET", "/catalog")

    async def create_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self._sandbox:
            payload = {**payload, "sandbox": 1}
        data = await self._request("POST", "/order", json=payload)
        return data if isinstance(data, dict) else {"result": data}

    async def get_order(self, order_id: str) -> dict[str, Any]:
        data = await self._request("GET", f"/order/{order_id}")
        return data if isinstance(data, dict) else {"result": data}
