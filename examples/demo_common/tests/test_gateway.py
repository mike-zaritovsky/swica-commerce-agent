"""The gateway transport: path rewrite, key headers, fallback to the second key, and a
streamed turn that ends with the gateway's ``data: [DONE]`` marker."""

from __future__ import annotations

import json

import httpx
import pytest
from anthropic import AsyncAnthropic

from demo_common.gateway import GatewayTransport, build_gateway_client

MESSAGE = {
    "id": "msg_1",
    "type": "message",
    "role": "assistant",
    "model": "claude-haiku-4-5",
    "content": [{"type": "text", "text": "Hi"}],
    "stop_reason": "end_turn",
    "stop_sequence": None,
    "usage": {"input_tokens": 5, "output_tokens": 1},
}


def _sse(*events: dict) -> bytes:
    lines = [f"event: {event['type']}\ndata: {json.dumps(event)}\n\n" for event in events]
    return ("".join(lines) + "data: [DONE]\n\n").encode()


STREAM = _sse(
    {"type": "message_start", "message": {**MESSAGE, "content": [], "stop_reason": None}},
    {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
    {
        "type": "content_block_delta",
        "index": 0,
        "delta": {"type": "text_delta", "text": "Hi"},
    },
    {"type": "content_block_stop", "index": 0},
    {
        "type": "message_delta",
        "delta": {"stop_reason": "end_turn", "stop_sequence": None},
        "usage": {"output_tokens": 1},
    },
    {"type": "message_stop"},
)


class Recorder:
    """A fake gateway: answers each key with the status configured for it."""

    def __init__(self, statuses: dict[str, int], stream: bool = False) -> None:
        self.statuses = statuses
        self.stream = stream
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        status = self.statuses[request.headers["Ocp-Apim-Subscription-Key"]]
        if status != 200:
            return httpx.Response(status, json={"type": "error", "error": {"type": "x"}})
        headers = {"X-Token-Budget-Remaining": "4.20"}
        if self.stream:
            return httpx.Response(
                200, content=STREAM, headers={**headers, "content-type": "text/event-stream"}
            )
        return httpx.Response(200, json=MESSAGE, headers=headers)


def _client(recorder: Recorder, fallback: str | None = "k2") -> AsyncAnthropic:
    transport = GatewayTransport("k1", fallback, inner=httpx.MockTransport(recorder))
    return AsyncAnthropic(
        base_url="https://gw.example/foundry",
        api_key="k1",
        http_client=httpx.AsyncClient(transport=transport),
        max_retries=0,
    )


async def _ask(client: AsyncAnthropic) -> str:
    message = await client.messages.create(
        model="claude-haiku-4-5", max_tokens=10, messages=[{"role": "user", "content": "Hello"}]
    )
    return message.content[0].text  # type: ignore[union-attr]


async def test_rewrites_path_and_sets_key() -> None:
    recorder = Recorder({"k1": 200, "k2": 200})
    assert await _ask(_client(recorder)) == "Hi"
    (request,) = recorder.requests
    assert request.url.path == "/foundry/chat/completions"
    assert request.url.params["api-version"] == "2024-05-01-preview"
    assert request.headers["Ocp-Apim-Subscription-Key"] == "k1"
    assert json.loads(request.content)["messages"][0]["content"] == "Hello"


async def test_falls_back_to_second_key_and_stays_on_it() -> None:
    recorder = Recorder({"k1": 429, "k2": 200})
    client = _client(recorder)
    assert await _ask(client) == "Hi"
    assert [r.headers["Ocp-Apim-Subscription-Key"] for r in recorder.requests] == ["k1", "k2"]
    assert recorder.requests[0].content == recorder.requests[1].content
    await _ask(client)  # within the cooldown the fallback key goes first
    assert recorder.requests[2].headers["Ocp-Apim-Subscription-Key"] == "k2"


async def test_without_fallback_the_error_reaches_the_caller() -> None:
    recorder = Recorder({"k1": 401})
    with pytest.raises(Exception, match="401"):
        await _ask(_client(recorder, fallback=None))


async def test_stream_ending_in_done_marker_completes() -> None:
    client = _client(Recorder({"k1": 200, "k2": 200}, stream=True))
    async with client.messages.stream(
        model="claude-sonnet-5", max_tokens=10, messages=[{"role": "user", "content": "Hello"}]
    ) as stream:
        text = "".join([chunk async for chunk in stream.text_stream])
        final = await stream.get_final_message()
    assert text == "Hi"
    assert final.stop_reason == "end_turn"


def test_client_only_when_key_is_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FOUNDRY_SUBSCRIPTION_KEY", raising=False)
    assert build_gateway_client() is None
    monkeypatch.setenv("FOUNDRY_SUBSCRIPTION_KEY", "k1")
    client = build_gateway_client()
    assert client is not None
    assert str(client.base_url).startswith("https://ai-api-dev.dentsu.com/foundry")
