"""Live check of the dentsu AI gateway with the keys in .env, one key at a time:

1. a plain request on the turn model and on the memory model;
2. a streamed request with a tool, read to the end (the gateway appends ``data: [DONE]``);
3. two identical requests with a cached system prompt: the second should read the cache.

Each step prints the HTTP outcome, the reply, the ``X-Token-Budget-*`` headers, and token
usage. Run from the repo root:

    python scripts/gateway_smoke.py              # every configured key
    python scripts/gateway_smoke.py --key fallback
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

import httpx
from anthropic import APIConnectionError, APIStatusError, AsyncAnthropic
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "examples"))

from demo_common.gateway import (  # noqa: E402
    DEFAULT_API_VERSION,
    DEFAULT_GATEWAY_URL,
    GatewayCredential,
    GatewayTransport,
    credentials_from_env,
    env_transport,
)

MODEL = os.environ.get("AGENT_MODEL", "claude-sonnet-5")
MEMORY_MODEL = os.environ.get("AGENT_MEMORY_MODEL", "claude-haiku-4-5")
# Long enough to pass the minimum cacheable prefix on both models.
CACHED_SYSTEM = "You are a terse assistant for an insurance website. " + " ".join(
    f"Rule {i}: answer in one short sentence and never invent prices." for i in range(400)
)
TOOL = {
    "name": "get_premium_factors",
    "description": "Lists the customer details that affect an insurance premium.",
    "input_schema": {"type": "object", "properties": {"product": {"type": "string"}}},
}


class BudgetRecorder(httpx.AsyncBaseTransport):
    """Keeps the last response's budget headers so each step can print them."""

    def __init__(self) -> None:
        self.inner = env_transport()
        self.budget: dict[str, str] = {}

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        response = await self.inner.handle_async_request(request)
        self.budget = {
            k: v for k, v in response.headers.items() if k.lower().startswith("x-token-budget")
        }
        return response


def client_for(credential: GatewayCredential, recorder: BudgetRecorder) -> AsyncAnthropic:
    transport = GatewayTransport(
        [credential],
        api_version=os.environ.get("FOUNDRY_API_VERSION", DEFAULT_API_VERSION),
        inner=recorder,
    )
    return AsyncAnthropic(
        base_url=os.environ.get("FOUNDRY_GATEWAY_URL", DEFAULT_GATEWAY_URL),
        api_key=credential.key,
        http_client=httpx.AsyncClient(transport=transport, timeout=120),
        default_headers={
            "api-version": "v1",
            "x-brand": os.environ.get("FOUNDRY_BRAND", "merkle"),
            "x-service-line": os.environ.get("FOUNDRY_SERVICE_LINE", "cxm"),
        },
        max_retries=0,
    )


def describe(error: Exception) -> str:
    if isinstance(error, APIStatusError):
        return f"HTTP {error.status_code}: {error.message}"
    if isinstance(error, APIConnectionError):
        return f"cannot reach the gateway ({error.__cause__ or error})"
    return f"{type(error).__name__}: {error}"


def report(step: str, ok: bool, detail: str, recorder: BudgetRecorder) -> bool:
    print(f"  [{'OK' if ok else 'FAIL'}] {step}: {detail}")
    for name, value in sorted(recorder.budget.items()):
        print(f"         {name}: {value}")
    return ok


async def check(credential: GatewayCredential) -> bool:
    print(f"\n== {credential.label} key, project {credential.project} ==")
    recorder = BudgetRecorder()
    client = client_for(credential, recorder)
    results = []

    for model in (MODEL, MEMORY_MODEL):
        try:
            message = await client.messages.create(
                model=model,
                max_tokens=50,
                messages=[{"role": "user", "content": "Say hello in five words."}],
            )
            text = "".join(b.text for b in message.content if b.type == "text")
            results.append(report(f"plain {model}", True, repr(text), recorder))
        except Exception as error:
            results.append(report(f"plain {model}", False, describe(error), recorder))

    try:
        async with client.messages.stream(
            model=MODEL,
            max_tokens=300,
            tools=[TOOL],
            messages=[
                {
                    "role": "user",
                    "content": "What affects the premium of a hospital insurance? Use the tool.",
                }
            ],
        ) as stream:
            async for _ in stream:
                pass
            final = await stream.get_final_message()
        tools = [b.name for b in final.content if b.type == "tool_use"]
        results.append(
            report(
                "stream + tool",
                True,
                f"stop_reason={final.stop_reason} tool_calls={tools}",
                recorder,
            )
        )
    except Exception as error:
        results.append(report("stream + tool", False, describe(error), recorder))

    cached = 0
    for turn in (1, 2):
        try:
            message = await client.messages.create(
                model=MODEL,
                max_tokens=30,
                system=[
                    {"type": "text", "text": CACHED_SYSTEM, "cache_control": {"type": "ephemeral"}}
                ],
                messages=[{"role": "user", "content": "Hi"}],
            )
            usage = message.usage
            cached = usage.cache_read_input_tokens or 0
            report(
                f"cache turn {turn}",
                True,
                f"input={usage.input_tokens} cache_write={usage.cache_creation_input_tokens} "
                f"cache_read={cached}",
                recorder,
            )
        except Exception as error:
            results.append(
                report(
                    f"cache turn {turn}",
                    False,
                    describe(error),
                    recorder,
                )
            )
    results.append(
        report("prompt caching", cached > 0, f"second call read {cached} cached tokens", recorder)
    )
    await client.close()
    return all(results)


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", choices=("primary", "fallback"))
    args = parser.parse_args()
    load_dotenv(REPO_ROOT / ".env", override=False)
    credentials = [c for c in credentials_from_env() if not args.key or c.label == args.key]
    if not credentials:
        print("No FOUNDRY_SUBSCRIPTION_KEY (or the requested key) in the environment or .env.")
        return 2
    print(
        f"Gateway: {os.environ.get('FOUNDRY_GATEWAY_URL', DEFAULT_GATEWAY_URL)}  models: {MODEL}, {MEMORY_MODEL}"
    )
    ok = [await check(c) for c in credentials]
    print("\nAll checks passed." if all(ok) else "\nSome checks failed; see above.")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
