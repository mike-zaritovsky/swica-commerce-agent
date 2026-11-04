"""An ``AsyncAnthropic`` client for the dentsu AI gateway (Claude on Azure AI Foundry).

The gateway serves the native Anthropic Messages API on its own route: the request body
passes through unchanged and the response comes back in Anthropic format (streaming, tool
use, and prompt caching included). The SDK always calls ``{base_url}/v1/messages``, so
:class:`GatewayTransport` rewrites that path to ``/chat/completions?api-version=...``.

Each subscription key belongs to a gateway project, so a key always travels with its own
``x-project`` header: ``FOUNDRY_SUBSCRIPTION_KEY`` with ``FOUNDRY_PROJECT``, and the
optional ``FOUNDRY_SUBSCRIPTION_KEY_FALLBACK`` with ``FOUNDRY_PROJECT_FALLBACK``. When the
gateway answers a key with 401, 403, or 429 (rejected key or exhausted budget), the
transport resends the same request with the next key and skips the refused one for
``FOUNDRY_FALLBACK_COOLDOWN_S`` seconds.

Environment:

- ``FOUNDRY_SUBSCRIPTION_KEY`` + ``FOUNDRY_PROJECT`` (required to use the gateway)
- ``FOUNDRY_SUBSCRIPTION_KEY_FALLBACK`` + ``FOUNDRY_PROJECT_FALLBACK`` (optional; the
  fallback project defaults to ``FOUNDRY_PROJECT``)
- ``FOUNDRY_GATEWAY_URL`` (default ``https://ai-api-dev.dentsu.com/foundry``)
- ``FOUNDRY_API_VERSION`` (default ``2024-05-01-preview``)
- ``FOUNDRY_BRAND``, ``FOUNDRY_SERVICE_LINE`` (defaults ``merkle``, ``cxm``)
- ``FOUNDRY_FALLBACK_COOLDOWN_S`` (default ``600``)

Each model call logs the gateway's token-budget headers on this module's logger.
"""

from __future__ import annotations

import logging
import os
import ssl
import time
from dataclasses import dataclass, field

import httpx
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)

DEFAULT_GATEWAY_URL = "https://ai-api-dev.dentsu.com/foundry"
DEFAULT_API_VERSION = "2024-05-01-preview"
DEFAULT_PROJECT = "celestyal-poc"
KEY_HEADER = "Ocp-Apim-Subscription-Key"
PROJECT_HEADER = "x-project"
FALLBACK_STATUSES = frozenset({401, 403, 429})
BUDGET_HEADER_PREFIX = "x-token-budget-"


def env_transport() -> httpx.AsyncHTTPTransport:
    """An HTTP transport that honours ``HTTPS_PROXY`` and ``SSL_CERT_FILE`` the way an
    ``httpx.AsyncClient`` does; a transport passed in explicitly would otherwise ignore
    them, which breaks behind a corporate proxy."""
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or None
    cert_file = os.environ.get("SSL_CERT_FILE")
    verify: ssl.SSLContext | bool = (
        ssl.create_default_context(cafile=cert_file) if cert_file else True
    )
    return httpx.AsyncHTTPTransport(proxy=proxy, verify=verify)


@dataclass
class GatewayCredential:
    """One subscription key and the gateway project it belongs to."""

    key: str
    project: str
    label: str
    blocked_until: float = field(default=0.0, compare=False)


class GatewayTransport(httpx.AsyncBaseTransport):
    """Rewrites ``/v1/messages`` to the gateway route, sets each credential's key and
    project, and moves to the next credential when one is refused."""

    def __init__(
        self,
        credentials: list[GatewayCredential],
        *,
        api_version: str = DEFAULT_API_VERSION,
        cooldown_s: float = 600.0,
        inner: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not credentials:
            raise ValueError("the gateway needs at least one subscription key")
        self._credentials = credentials
        self._api_version = api_version
        self._cooldown_s = cooldown_s
        self._inner = inner or env_transport()

    def _order(self) -> list[GatewayCredential]:
        """Credentials outside their cooldown first, in configured order; the cooling ones
        stay as a last resort."""
        now = time.monotonic()
        ready = [c for c in self._credentials if c.blocked_until <= now]
        cooling = [c for c in self._credentials if c.blocked_until > now]
        return ready + cooling

    def _prepare(self, request: httpx.Request, credential: GatewayCredential) -> httpx.Request:
        url = request.url
        if url.path.endswith("/v1/messages"):
            url = url.copy_with(
                path=url.path[: -len("/v1/messages")] + "/chat/completions",
                params={"api-version": self._api_version},
            )
        headers = request.headers.copy()
        headers[KEY_HEADER] = credential.key
        headers["x-api-key"] = credential.key
        headers[PROJECT_HEADER] = credential.project
        return httpx.Request(
            request.method,
            url,
            headers=headers,
            content=request.content,
            extensions=request.extensions,
        )

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        await request.aread()  # the body is resent unchanged if a key is refused
        order = self._order()
        for attempt, credential in enumerate(order):
            response = await self._inner.handle_async_request(self._prepare(request, credential))
            is_last = attempt == len(order) - 1
            if response.status_code not in FALLBACK_STATUSES or is_last:
                self._log_budget(response, credential)
                return response
            await response.aclose()
            credential.blocked_until = time.monotonic() + self._cooldown_s
            logger.warning(
                "gateway refused the %s key (%s) with HTTP %s; retrying with the %s key (%s)",
                credential.label,
                credential.project,
                response.status_code,
                order[attempt + 1].label,
                order[attempt + 1].project,
            )
        raise AssertionError("unreachable")  # the loop always returns on its last attempt

    def _log_budget(self, response: httpx.Response, credential: GatewayCredential) -> None:
        budget = {
            name[len(BUDGET_HEADER_PREFIX) :]: value
            for name, value in response.headers.items()
            if name.lower().startswith(BUDGET_HEADER_PREFIX)
        }
        if budget:
            logger.info(
                "gateway %s key=%s project=%s budget %s",
                response.status_code,
                credential.label,
                credential.project,
                " ".join(f"{name}={value}" for name, value in sorted(budget.items())),
            )

    async def aclose(self) -> None:
        await self._inner.aclose()


def credentials_from_env() -> list[GatewayCredential]:
    """The configured key/project pairs, primary first; empty when no key is set."""
    project = os.environ.get("FOUNDRY_PROJECT", "").strip() or DEFAULT_PROJECT
    pairs = [
        ("primary", "FOUNDRY_SUBSCRIPTION_KEY", project),
        (
            "fallback",
            "FOUNDRY_SUBSCRIPTION_KEY_FALLBACK",
            os.environ.get("FOUNDRY_PROJECT_FALLBACK", "").strip() or project,
        ),
    ]
    return [
        GatewayCredential(key=os.environ[name].strip(), project=proj, label=label)
        for label, name, proj in pairs
        if os.environ.get(name, "").strip()
    ]


def gateway_configured() -> bool:
    return bool(os.environ.get("FOUNDRY_SUBSCRIPTION_KEY", "").strip())


def build_gateway_client(timeout_s: float = 120.0) -> AsyncAnthropic | None:
    """The gateway client when ``FOUNDRY_SUBSCRIPTION_KEY`` is set, else ``None`` (the
    agent then builds its default client from ``ANTHROPIC_API_KEY``). Call it after
    ``load_demo_env`` so the ``.env`` files have been read."""
    if not gateway_configured():
        return None
    credentials = credentials_from_env()
    transport = GatewayTransport(
        credentials,
        api_version=os.environ.get("FOUNDRY_API_VERSION", DEFAULT_API_VERSION),
        cooldown_s=float(os.environ.get("FOUNDRY_FALLBACK_COOLDOWN_S", "600")),
    )
    logger.info(
        "model calls go through the dentsu gateway; keys: %s",
        ", ".join(f"{c.label} ({c.project})" for c in credentials),
    )
    return AsyncAnthropic(
        base_url=os.environ.get("FOUNDRY_GATEWAY_URL", DEFAULT_GATEWAY_URL),
        api_key=credentials[0].key,
        http_client=httpx.AsyncClient(transport=transport, timeout=timeout_s),
        default_headers={
            "api-version": "v1",
            "x-brand": os.environ.get("FOUNDRY_BRAND", "merkle"),
            "x-service-line": os.environ.get("FOUNDRY_SERVICE_LINE", "cxm"),
        },
        # Key fallback happens inside the transport; the SDK's own retries cover the rest.
        max_retries=2,
    )
