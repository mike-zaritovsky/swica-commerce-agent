"""The SWICA rules in the Shopify backend that need no network: the terms always carry
SWICA's contact entry, only the configured vendor's products are listed, and the cart
holds one basic insurance (KVG)."""

from __future__ import annotations

import pytest

from shopify_demo.api.shopify_backend import ShopifyBackend
from shopping_agent import ProductDetails, ShoppingSessionContext

SESSION = ShoppingSessionContext(session_id="s", user_id="u")


@pytest.fixture
def backend(monkeypatch: pytest.MonkeyPatch) -> ShopifyBackend:
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "example.myshopify.com")
    monkeypatch.setenv("SHOPIFY_STOREFRONT_TOKEN", "token")
    monkeypatch.delenv("SHOPIFY_VENDOR", raising=False)
    monkeypatch.delenv("SHOPIFY_COUNTRY", raising=False)
    return ShopifyBackend()


async def test_terms_answer_and_always_include_contact(backend: ShopifyBackend) -> None:
    found = [p.policy_id for p in await backend.search_policies(SESSION, "Franchise ändern")]
    assert found[0] == "excess" and "contact" in found
    unanswered = await backend.search_policies(SESSION, "cosmetic surgery abroad")
    assert "contact" in [p.policy_id for p in unanswered]
    contact = next(p for p in unanswered if p.policy_id == "contact")
    assert (
        "+41 58 800 99 33" in contact.content and "Source: https://www.swica.ch" in contact.content
    )


def test_only_the_vendor_products_are_listed(backend: ShopifyBackend) -> None:
    assert backend._is_listed({"vendor": "SWICA"})
    assert not backend._is_listed({"vendor": "Some Fashion Brand"})


def test_queries_run_in_switzerland(backend: ShopifyBackend) -> None:
    assert backend._country == "CH"
    assert backend._currency(None) == "CHF"


def test_variant_resolves_to_family_category(backend: ShopifyBackend) -> None:
    backend.products["1"] = ProductDetails(
        product_id="1", title="Standard", price=250, category="KVG"
    )
    backend.variants["11"] = ProductDetails(
        product_id="11", title="Standard", price=250, variant_of="1"
    )
    assert backend._category_of("11") == "KVG"
    assert backend._category_of("missing") == ""
