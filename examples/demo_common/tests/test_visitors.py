"""Anonymous visitors: each browser gets its own server-issued id, so memory is never
shared between visitors, and a start request cannot claim someone else's id."""

from __future__ import annotations

from pathlib import Path

from conftest import SHOPPING_SKILLS, FakeBackend
from fastapi.testclient import TestClient

from commerce_common.memory import InMemoryMemoryStore
from commerce_common.skills import SkillRegistry
from demo_common import MemorySeeder, build_storefront_host
from demo_common.storefront import anonymous_user_id
from shopping_agent import ShoppingAgentConfig
from shopping_agent_runtime import ShoppingAgent


class Storefront(FakeBackend):
    """The fake storefront plus what the shared routes read (``DemoStorefront``)."""

    store_name = "Test"
    products: dict = {}

    def product(self, product_id: str):
        return None

    def reset_session(self, session_id: str) -> None:
        pass


def test_ids_are_issued_and_only_issued_ids_resume():
    issued = anonymous_user_id(None)
    assert issued.startswith("anon-") and len(issued) == 29
    assert anonymous_user_id(issued) == issued
    for claimed in ("demo-user", "anon-short", "", issued + "x"):
        assert anonymous_user_id(claimed) not in {claimed, "demo-user"}
    assert anonymous_user_id(None) != anonymous_user_id(None)


def test_each_browser_gets_its_own_id_and_keeps_it(tmp_path: Path):
    agent = ShoppingAgent(
        backend=Storefront(),
        skills=SkillRegistry(SHOPPING_SKILLS),
        config=ShoppingAgentConfig(brand_name="Test"),
        memory_store=InMemoryMemoryStore(),
    )
    host = build_storefront_host(
        title="test",
        example_root=tmp_path,
        backend=Storefront(),
        agent=agent,
        memory_seeder=MemorySeeder(tmp_path / "seed.json", marker=tmp_path / "seeded.json"),
    )
    client = TestClient(host.app, base_url="http://localhost")
    first = client.post("/api/session").json()["user_id"]
    second = client.post("/api/session").json()["user_id"]
    assert first != second and first.startswith("anon-")
    returning = client.post("/api/session", json={"user_id": first}).json()["user_id"]
    assert returning == first
    spoofed = client.post("/api/session", json={"user_id": "demo-user"}).json()["user_id"]
    assert spoofed not in {"demo-user", first}
