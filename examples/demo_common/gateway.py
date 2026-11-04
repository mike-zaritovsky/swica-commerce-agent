"""An ``AsyncAnthropic`` client for the dentsu AI gateway (Claude on Azure AI Foundry).

The gateway serves the native Anthropic Messages API on its own route: the request body
passes through unchanged and the response comes back in Anthropic format (streaming, tool
use, and prompt caching included). The SDK always calls ``{base_url}/v1/messages``, so
:class:`GatewayTransport` rewrites that path to ``/chat/completions?api-version=...`` and
puts the subscription key on every request.

Two keys: ``FOUNDRY_SUBSCRIPTION_KEY`` is primary, ``FOUNDRY_SUBSCRIPTION_KEY_FALLBACK``
is optional. When the gateway answers the primary key with 401, 403, or 429 (rejected key or
exhausted budget), the transport resends the same request with the fallback key and keeps
using it for ``FOUNDRY_FALLBACK_COOLDOWN_S`` seconds before trying the primary again.

Environment:

- ``FOUNDRY_SUBSCRIPTION_KEY`` (required to use the gateway)
- ``FOUNDRY_SUBSCRIPTION_KEY_FALLBACK`` (optional)
- ``FOUNDRY_GATEWAY_URL`` (default ``https://ai-api-dev.dentsu.com/foundry``)
- ``FOUNDRY_API_VERSION`` (default ``2024-05-01-preview``)
- ``FOUNDRY_BRAND``, ``FOUNDRY_SERVICE_LINE``, ``FOUNDRY_PROJECT`` (the cost-attribution
  headers; defaults ``merkle``, ``cxm``, ``celestyal-poc``)
- ``FOUNDRY_FALLBACK_COOLDOWN_S`` (default ``600``)

Each model call logs the gateway's token-budget headers on this module's logger.
"""

from __future__ import annotations

import logging
import os
import time

import httpx
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)

DEFAULT_GATEWAY_URL = "https://ai-api-dev.dentsu.com/foundry"
DEFAULT_API_VERSION = "2024-05-01-preview"
KEY_HEADER = "Ocp-Apim-Subscription-Key"
FALLBACK_STATUSES = frozenset({401, 403, 429})
BUDGET_HEADER_PREFIX = "x-token-budget-"


class GatewayTransport(httpx.AsyncBaseTransport):
    """Rewrites ``/v1/messages`` to the gateway route, sets the subscription key, and
    falls back to the second key when the first is refused."""

    def __init__(
        self,
        primary_key: str,
        fallback_key: str | None = None,
        *,
        api_version: str = DEFAULT_API_VERSION,
        cooldown_s: float = 600.0,
        inner: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._keys = [primary_key] + ([fallback_key] if fallback_key else [])
        self._api_version = api_version
        self._cooldown_s = cooldown_s
        self._inner = inner or httpx.AsyncHTTPTransport()
        self._primary_blocked_until = 0.0

    def _key_order(self) -> list[str]:
        if len(self._keys) > 1 and time.monotonic() < self._primary_blocked_until:
            return [self._keys[1], self._keys[0]]
        return list(self._keys)

    def _prepare(self, request: httpx.Request, key: str) -> httpx.Request:
        url = request.url
        if url.path.endswith("/v1/messages"):
            url = url.copy_with(
                path=url.path[: -len("/v1/messages")] + "/chat/completions",
                params={"api-version": self._api_version},
            )
        headers = request.headers.copy()
        headers[KEY_HEADER] = key
        headers["x-api-key"] = key
        return httpx.Request(
            request.method,
            url,
            headers=headers,
            content=request.content,
            extensions=request.extensions,
        )

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        await request.aread()  # the body is resent unchanged if the first key is refused
        order = self._key_order()
        for attempt, key in enumerate(order):
            response = await self._inner.handle_async_request(self._prepare(request, key))
            is_last = attempt == len(order) - 1
            if response.status_code not in FALLBACK_STATUSES or is_last:
                self._log_budget(response, key)
                return response
            await response.aclose()
            if key == self._keys[0]:
                self._primary_blocked_until = time.monotonic() + self._cooldown_s
            logger.warning(
                "gateway refused key %s with HTTP %s; retrying with key %s",
                _key_label(key, self._keys),
                response.status_code,
                _key_label(order[attempt + 1], self._keys),
            )
        raise AssertionError("unreachable")  # the loop always returns on its last attempt

    def _log_budget(self, response: httpx.Response, key: str) -> None:
        budget = {
            name[len(BUDGET_HEADER_PREFIX) :]: value
            for name, value in response.headers.items()
            if name.lower().startswith(BUDGET_HEADER_PREFIX)
        }
        if budget:
            logger.info(
                "gateway %s key=%s budget %s",
                response.status_code,
                _key_label(key, self._keys),
                " ".join(f"{name}={value}" for name, value in sorted(budget.items())),
            )

    async def aclose(self) -> None:
        await self._inner.aclose()


def _key_label(key: str, keys: list[str]) -> str:
    return "primary" if key == keys[0] else "fallback"


def gateway_configured() -> bool:
    return bool(os.environ.get("FOUNDRY_SUBSCRIPTION_KEY"))


def build_gateway_client(timeout_s: float = 120.0) -> AsyncAnthropic | None:
    """The gateway client when ``FOUNDRY_SUBSCRIPTION_KEY`` is set, else ``None`` (the
    agent then builds its default client from ``ANTHROPIC_API_KEY``). Call it after
    ``load_demo_env`` so the ``.env`` files have been read."""
    primary = os.environ.get("FOUNDRY_SUBSCRIPTION_KEY", "").strip()
    if not primary:
        return None
    fallback = os.environ.get("FOUNDRY_SUBSCRIPTION_KEY_FALLBACK", "").strip() or None
    transport = GatewayTransport(
        primary,
        fallback,
        api_version=os.environ.get("FOUNDRY_API_VERSION", DEFAULT_API_VERSION),
        cooldown_s=float(os.environ.get("FOUNDRY_FALLBACK_COOLDOWN_S", "600")),
    )
    logger.info(
        "model calls go through the dentsu gateway (%s key%s)",
        "two" if fallback else "one",
        "s" if fallback else "",
    )
    return AsyncAnthropic(
        base_url=os.environ.get("FOUNDRY_GATEWAY_URL", DEFAULT_GATEWAY_URL),
        api_key=primary,
        http_client=httpx.AsyncClient(transport=transport, timeout=timeout_s),
        default_headers={
            "api-version": "v1",
            "x-brand": os.environ.get("FOUNDRY_BRAND", "merkle"),
            "x-service-line": os.environ.get("FOUNDRY_SERVICE_LINE", "cxm"),
            "x-project": os.environ.get("FOUNDRY_PROJECT", "celestyal-poc"),
        },
        # Key fallback happens inside the transport; the SDK's own retries cover the rest.
        max_retries=2,
    )
