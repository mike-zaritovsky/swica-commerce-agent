"""Shopify demo API: a real Shopify store behind the shared storefront routes, plus the
merchant portal (MerchantBackend over the same Shopify catalog) under /api/merchant.

    uvicorn shopify_demo.api.main:app --app-dir examples --reload --port 8000
    (cd examples/shopify_demo/merchant-web && npm run dev)   # :3100, once that app exists

Set SHOPIFY_STORE_DOMAIN and SHOPIFY_STOREFRONT_TOKEN in .env before running. With
FOUNDRY_SUBSCRIPTION_KEY set, model calls go through the dentsu gateway
(``demo_common.gateway``); without it, through ANTHROPIC_API_KEY. The agent's wording lives
in ``agent_profile.py``.
"""

from __future__ import annotations

import contextlib
from pathlib import Path

from fastapi import FastAPI

from commerce_common.memory import InMemoryMemoryStore
from demo_common import (
    REPO_ROOT,
    CartAddRequest,
    MemorySeeder,
    build_storefront_host,
    load_demo_env,
)
from demo_common.gateway import build_gateway_client
from shopping_agent import ShoppingAgentConfig
from shopping_agent_runtime import ShoppingAgent

from . import agent_profile as profile
from .merchant import create_merchant_router
from .shopify_backend import ShopifyBackend

EXAMPLE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = EXAMPLE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

load_demo_env(EXAMPLE_DIR)

backend = ShopifyBackend()

# The gateway client when FOUNDRY_SUBSCRIPTION_KEY is set, else None (default client).
client = build_gateway_client()

config = ShoppingAgentConfig(
    brand_name=profile.BRAND_NAME,
    assistant_name=profile.ASSISTANT_NAME,
    brand_voice=profile.BRAND_VOICE,
    domain_search_notes=profile.DOMAIN_SEARCH_NOTES,
    model=profile.MODEL,
    memory_model=profile.MEMORY_MODEL,
)

agent = ShoppingAgent(
    backend=backend,
    skills_dir=REPO_ROOT / "shopping-agent" / "skills",
    config=config,
    memory_store=InMemoryMemoryStore(),
    client=client,
)

host = build_storefront_host(
    title="SWICA Insurance Agent Demo",
    example_root=EXAMPLE_DIR,
    backend=backend,
    agent=agent,
    memory_seeder=MemorySeeder(
        DATA_DIR / "memory-seed.json", marker=DATA_DIR / ".memory-seeded.json"
    ),
)
app = host.app

# `build_storefront_host` gives its FastAPI app a `lifespan=` context manager (for
# seeding memory at boot) — and once an app has `lifespan=`, the older `@app.on_event`
# API is simply never called, no error, no warning. So instead of `@app.on_event`,
# wrap the existing lifespan: warm the merchant catalog first, then hand off to it.
_host_lifespan = app.router.lifespan_context


@contextlib.asynccontextmanager
async def _lifespan_with_catalog_warmup(app: FastAPI):
    await backend.list_catalog()
    async with _host_lifespan(app):
        yield


app.router.lifespan_context = _lifespan_with_catalog_warmup

app.include_router(
    create_merchant_router(backend, InMemoryMemoryStore(), client=client), prefix="/api/merchant"
)


@app.post("/api/cart/add")
async def cart_add(request: CartAddRequest, record: host.CurrentSession) -> dict:
    return await host.direct_add(
        record,
        request,
        note="[Already completed] The customer used the add-to-cart button to add {title} ({product_id}), quantity {quantity}. The item is already in the cart — do NOT add it again.",
    )
