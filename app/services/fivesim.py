"""
FiveSim API client (async) for both public and user/vendor endpoints.
All code is in English as requested.

Documentation reference: see api.md in project root (5sim official endpoints).
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class FiveSimError(Exception):
    """Generic error wrapper for FiveSim client with context."""

    def __init__(self, message: str, *, status_code: Optional[int] = None, payload: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class FiveSimClient:
    """
    Async client for 5SIM API.

    Usage:
        async with FiveSimClient(token="BearerToken") as fs:
            profile = await fs.get_user_profile()

    Or inject an external httpx.AsyncClient:
        client = httpx.AsyncClient(timeout=10)
        fs = FiveSimClient(token="BearerToken", client=client)
        ...
    """

    BASE_URL = "https://5sim.net"

    def __init__(
        self,
        *,
        token: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
        default_headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0,
        retries: int = 2,
    ) -> None:
        self._token = token.strip() if token else None
        self._client = client
        self._owns_client = client is None
        self._timeout = timeout
        self._retries = max(0, retries)
        self._default_headers = {
            "Accept": "application/json",
        }
        if default_headers:
            self._default_headers.update(default_headers)

    # ---------------------- context management ----------------------
    async def __aenter__(self) -> "FiveSimClient":
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(self._timeout, connect=5.0))
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._client and self._owns_client:
            try:
                await self._client.aclose()
            except Exception as e:
                logger.warning("Error closing http client: %s", e)
            finally:
                self._client = None

    # ---------------------- internal request helper ----------------------
    def _auth_headers(self) -> Dict[str, str]:
        headers = dict(self._default_headers)
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        require_ok: bool = True,
    ) -> Any:
        if self._client is None:
            # Lazy create if not provided
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(self._timeout, connect=5.0))
            self._owns_client = True

        url = self.BASE_URL.rstrip("/") + path
        merged_headers = self._auth_headers()
        if headers:
            merged_headers.update(headers)

        last_exc: Optional[Exception] = None
        for attempt in range(self._retries + 1):
            try:
                resp = await self._client.request(
                    method,
                    url,
                    params=params,
                    json=json_body,
                    headers=merged_headers,
                )
                if require_ok and resp.status_code >= 400:
                    # Try extract error payload
                    try:
                        payload = resp.json()
                    except Exception:
                        payload = resp.text
                    raise FiveSimError(
                        f"5SIM {method} {path} failed with status {resp.status_code}",
                        status_code=resp.status_code,
                        payload=payload,
                    )
                # try return json
                try:
                    return resp.json()
                except Exception:
                    return resp.text
            except FiveSimError as e:
                # No retry on 4xx except 429
                if e.status_code and 400 <= e.status_code < 500 and e.status_code != 429:
                    raise
                last_exc = e
            except httpx.HTTPError as e:
                last_exc = e

            # backoff
            if attempt < self._retries:
                await asyncio.sleep(min(2.0, 0.5 * (2 ** attempt)))

        assert last_exc is not None
        raise last_exc

    # ---------------------- Public (guest) endpoints ----------------------
    async def get_guest_prices(
        self,
        *,
        country: Optional[str] = None,
        product: Optional[str] = None,
    ) -> Any:
        """GET /v1/guest/prices with optional country/product filters."""
        params: Dict[str, Any] = {}
        if country:
            params["country"] = country
        if product:
            params["product"] = product
        return await self._request("GET", "/v1/guest/prices", params=params)

    async def get_guest_products(self, *, country: str, operator: str) -> Any:
        """GET /v1/guest/products/{country}/{operator}"""
        path = f"/v1/guest/products/{country}/{operator}"
        return await self._request("GET", path)

    async def get_countries(self) -> Any:
        """GET /v1/guest/countries"""
        return await self._request("GET", "/v1/guest/countries")

    async def get_notifications(self, *, lang: str) -> Any:
        """GET /v1/guest/flash/{lang} (ru/en)"""
        path = f"/v1/guest/flash/{lang}"
        # Docs show Authorization in headers but endpoint is guest; keep optional.
        return await self._request("GET", path, require_ok=True)

    # ---------------------- User endpoints ----------------------
    async def get_user_profile(self) -> Any:
        """GET /v1/user/profile"""
        return await self._request("GET", "/v1/user/profile")

    async def buy_activation(
        self,
        *,
        country: str,
        operator: str,
        product: str,
        forwarding: Optional[int] = None,  # 0/1
        number: Optional[str] = None,
        reuse: Optional[int] = None,  # 1
        voice: Optional[int] = None,  # 1
        ref: Optional[str] = None,
        max_price: Optional[float] = None,  # works only if operator="any"
    ) -> Any:
        """GET /v1/user/buy/activation/{country}/{operator}/{product}?..."""
        path = f"/v1/user/buy/activation/{country}/{operator}/{product}"
        params: Dict[str, Any] = {}
        if forwarding is not None:
            params["forwarding"] = str(forwarding)
        if number is not None:
            params["number"] = number
        if reuse is not None:
            params["reuse"] = str(reuse)
        if voice is not None:
            params["voice"] = str(voice)
        if ref is not None:
            params["ref"] = ref
        if max_price is not None:
            params["maxPrice"] = str(max_price)
        return await self._request("GET", path, params=params)

    async def buy_hosting(self, *, country: str, operator: str, product: str) -> Any:
        """GET /v1/user/buy/hosting/{country}/{operator}/{product}"""
        path = f"/v1/user/buy/hosting/{country}/{operator}/{product}"
        return await self._request("GET", path)

    async def reuse(self, *, product: str, number: str) -> Any:
        """GET /v1/user/reuse/{product}/{number}"""
        path = f"/v1/user/reuse/{product}/{number}"
        return await self._request("GET", path)

    async def order_check(self, *, order_id: str) -> Any:
        """GET /v1/user/check/{id}"""
        return await self._request("GET", f"/v1/user/check/{order_id}")

    async def order_finish(self, *, order_id: str) -> Any:
        """GET /v1/user/finish/{id}"""
        return await self._request("GET", f"/v1/user/finish/{order_id}")

    async def order_cancel(self, *, order_id: str) -> Any:
        """GET /v1/user/cancel/{id}"""
        return await self._request("GET", f"/v1/user/cancel/{order_id}")

    async def order_ban(self, *, order_id: str) -> Any:
        """GET /v1/user/ban/{id}"""
        return await self._request("GET", f"/v1/user/ban/{order_id}")

    async def order_sms_inbox(self, *, order_id: str) -> Any:
        """GET /v1/user/sms/inbox/{id}"""
        return await self._request("GET", f"/v1/user/sms/inbox/{order_id}")

    async def get_user_orders(self, *, category: str, **query: Any) -> Any:
        """GET /v1/user/orders?category=activation|hosting&..."""
        params = {"category": category}
        params.update({k: v for k, v in query.items() if v is not None})
        return await self._request("GET", "/v1/user/orders", params=params)

    async def get_user_payments(self, **query: Any) -> Any:
        """GET /v1/user/payments?limit=...&offset=..."""
        params = {k: v for k, v in query.items() if v is not None}
        return await self._request("GET", "/v1/user/payments", params=params)

    # ---------------------- Prices limit ----------------------
    async def get_max_prices(self) -> Any:
        """GET /v1/user/max-prices"""
        return await self._request("GET", "/v1/user/max-prices")

    async def set_max_price(self, *, product_name: str, price: float) -> Any:
        """POST /v1/user/max-prices {product_name, price}"""
        body = {"product_name": product_name, "price": price}
        return await self._request("POST", "/v1/user/max-prices", json_body=body)

    async def delete_max_price(self, *, product_name: str) -> Any:
        """DELETE /v1/user/max-prices {product_name}"""
        body = {"product_name": product_name}
        return await self._request("DELETE", "/v1/user/max-prices", json_body=body)

    # ---------------------- Vendor (partner) endpoints ----------------------
    async def get_vendor_profile(self) -> Any:
        """GET /v1/user/vendor"""
        return await self._request("GET", "/v1/user/vendor")

    async def get_vendor_wallets(self) -> Any:
        """GET /v1/vendor/wallets"""
        return await self._request("GET", "/v1/vendor/wallets")

    async def get_vendor_orders(self, *, category: str, **query: Any) -> Any:
        """GET /v1/vendor/orders?category=..."""
        params = {"category": category}
        params.update({k: v for k, v in query.items() if v is not None})
        return await self._request("GET", "/v1/vendor/orders", params=params)

    async def get_vendor_payments(self, **query: Any) -> Any:
        """GET /v1/vendor/payments?limit=...&offset=..."""
        params = {k: v for k, v in query.items() if v is not None}
        return await self._request("GET", "/v1/vendor/payments", params=params)

    async def vendor_withdraw(self, *, receiver: str, method: str, amount: str, fee: str) -> Any:
        """POST /v1/vendor/withdraw {receiver, method, amount, fee}"""
        body = {
            "receiver": receiver,
            "method": method,  # visa / qiwi / yandex
            "amount": amount,
            "fee": fee,  # fkwallet / payeer / unitpay
        }
        return await self._request("POST", "/v1/vendor/withdraw", json_body=body)


__all__ = [
    "FiveSimClient",
    "FiveSimError",
]
