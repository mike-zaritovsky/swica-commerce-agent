"""Shopify StorefrontBackend: maps the Shopify Storefront API (GraphQL) to the
commerce-agents StorefrontBackend interface.

Requires: httpx (pip install httpx)
Env vars: SHOPIFY_STORE_DOMAIN, SHOPIFY_STOREFRONT_TOKEN; optional SHOPIFY_COUNTRY (the
buyer country every query runs in, which sets the prices' currency; default CH),
SHOPIFY_CURRENCY (the currency assumed when a response names none; default CHF), and
SHOPIFY_VENDOR (only products from this vendor are listed; default SWICA, empty lists all).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import httpx

from demo_common.storefront_fixtures import search_help
from shopping_agent import (
    Cart,
    CartItem,
    CheckoutHandoff,
    FulfillmentOption,
    Order,
    Policy,
    Product,
    ProductDetails,
    SearchFilters,
    ShoppingSessionContext,
    StorefrontBackend,
    Unavailable,
    UserPreferences,
)

# Categories a cart holds one product of: a person has one basic insurance (KVG).
SINGLE_LINE_CATEGORIES = frozenset({"KVG"})

POLICIES_FILE = Path(__file__).resolve().parent.parent / "data" / "policies.json"


def load_policies(path: Path) -> list[Policy]:
    """The help entries, each with its source page appended so the agent can cite it."""
    rows = json.loads(path.read_text(encoding="utf-8"))["policies"]
    return [
        Policy(
            policy_id=row["policy_id"],
            title=row["title"],
            category=row.get("category"),
            content=f"{row['content']} (Source: {row['source']})"
            if row.get("source")
            else row["content"],
        )
        for row in rows
    ]


# Replaced in every query with SHOPIFY_COUNTRY (see ``ShopifyBackend._gql``).
COUNTRY_TOKEN = "__COUNTRY__"


class ShopifyBackend(StorefrontBackend):
    """A StorefrontBackend that talks to a real Shopify store via the Storefront API."""

    def __init__(
        self,
        store_domain: str | None = None,
        storefront_token: str | None = None,
    ) -> None:
        self._domain = store_domain or os.environ["SHOPIFY_STORE_DOMAIN"]
        self._token = storefront_token or os.environ["SHOPIFY_STOREFRONT_TOKEN"]
        self._api_url = f"https://{self._domain}/api/2024-10/graphql.json"
        self._client = httpx.AsyncClient(timeout=15.0)
        self._session_carts: dict[str, str] = {}
        self.products: dict[str, ProductDetails] = {}
        self.variants: dict[str, ProductDetails] = {}
        self.store_name: str = store_domain or "the store"
        country = os.environ.get("SHOPIFY_COUNTRY", "CH").strip().upper()
        if not re.fullmatch(r"[A-Z]{2}", country):
            raise ValueError(f"SHOPIFY_COUNTRY must be a two-letter country code, not {country!r}")
        self._country = country
        self._default_currency = os.environ.get("SHOPIFY_CURRENCY", "CHF").strip().upper()
        self._vendor = os.environ.get("SHOPIFY_VENDOR", "SWICA").strip().lower()
        self._policies = load_policies(POLICIES_FILE)

    def _is_listed(self, node: dict) -> bool:
        """Whether a product belongs to the catalog this agent sells: the configured
        vendor's products only, so other items in the same store never surface."""
        return not self._vendor or (node.get("vendor") or "").strip().lower() == self._vendor

    # ------------------------------------------------------------------
    # GraphQL helper
    # ------------------------------------------------------------------

    async def _gql(self, query: str, variables: dict[str, Any] | None = None) -> dict:
        resp = await self._client.post(
            self._api_url,
            json={
                "query": query.replace(COUNTRY_TOKEN, self._country),
                "variables": variables or {},
            },
            headers={
                "X-Shopify-Storefront-Access-Token": self._token,
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        body = resp.json()
        if "errors" in body:
            raise RuntimeError(f"Shopify GraphQL error: {body['errors']}")
        return body.get("data", {})

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_gid(gid: str) -> str:
        return gid.rsplit("/", 1)[-1] if gid else gid

    @staticmethod
    def _money(price_obj: dict | None) -> float:
        if not price_obj:
            return 0.0
        return float(price_obj.get("amount", 0))

    def _currency(self, price_obj: dict | None) -> str:
        if not price_obj:
            return self._default_currency
        return price_obj.get("currencyCode", self._default_currency)

    def _map_product_summary(self, node: dict) -> Product:
        price_range = node.get("priceRange", {})
        min_price = price_range.get("minVariantPrice", {})
        first_image = None
        images = node.get("images", {}).get("nodes", [])
        if images:
            first_image = images[0].get("url")

        attributes: dict[str, str] = {}
        if node.get("productType"):
            attributes["type"] = node["productType"]
        for tag in node.get("tags", []):
            attributes[tag.lower()] = tag

        in_stock = node.get("availableForSale", True)

        return Product(
            product_id=self._parse_gid(node["id"]),
            title=node.get("title", ""),
            brand=node.get("vendor"),
            price=self._money(min_price),
            currency=self._currency(min_price),
            image_url=first_image,
            category=node.get("productType") or None,
            attributes=attributes,
            in_stock=in_stock,
            short_description=(node.get("description") or "")[:200] or None,
        )

    def _map_product_details(self, node: dict) -> ProductDetails:
        summary = self._map_product_summary(node)
        description_html = node.get("descriptionHtml", "")
        long_desc = re.sub(r"<[^>]+>", "", description_html).strip() if description_html else None

        variants: list[Product] = []
        variant_nodes = node.get("variants", {}).get("nodes", [])
        has_real_options = len(variant_nodes) > 1

        for v in variant_nodes:
            v_price = v.get("price", {})
            option_values: dict[str, str] = {}
            for opt in v.get("selectedOptions", []):
                option_values[opt["name"]] = opt["value"]

            v_image = None
            if v.get("image"):
                v_image = v["image"].get("url")

            variants.append(
                Product(
                    product_id=self._parse_gid(v["id"]),
                    title=v.get("title", ""),
                    price=self._money(v_price),
                    currency=self._currency(v_price),
                    in_stock=v.get("availableForSale", True),
                    image_url=v_image,
                    option_values=option_values,
                    variant_of=summary.product_id if has_real_options else None,
                )
            )

        options: dict[str, list[str]] = {}
        if has_real_options:
            for v in variant_nodes:
                for opt in v.get("selectedOptions", []):
                    options.setdefault(opt["name"], [])
                    if opt["value"] not in options[opt["name"]]:
                        options[opt["name"]].append(opt["value"])

        details = ProductDetails(
            product_id=summary.product_id,
            title=summary.title,
            brand=summary.brand,
            price=summary.price,
            currency=summary.currency,
            image_url=summary.image_url,
            category=summary.category,
            attributes=summary.attributes,
            in_stock=summary.in_stock,
            short_description=summary.short_description,
            long_description=long_desc,
            options=options,
            variants=variants if has_real_options else [],
        )
        self.products[details.product_id] = details
        # Each variant only lives inside `details.variants` above — cache it by its own
        # id too, or `self.product(variant_id)` (and merchant.py's alerts/pricing/stock
        # logic, which looks a variant up by its own id) can never resolve it: every
        # variant would silently read back as "not found", and a family product's real
        # per-size/per-color stock would never be visible.
        for v in variants:
            self.variants[v.product_id] = v
        return details

    # ------------------------------------------------------------------
    # Catalog — every query runs in SHOPIFY_COUNTRY, which sets the prices' currency
    # ------------------------------------------------------------------

    _SEARCH_QUERY = """
    query SearchProducts($query: String!, $first: Int!) @inContext(country: __COUNTRY__) {
      search(query: $query, first: $first, types: PRODUCT) {
        nodes {
          ... on Product {
            id
            title
            vendor
            productType
            tags
            description
            descriptionHtml
            availableForSale
            priceRange {
              minVariantPrice { amount currencyCode }
            }
            images(first: 5) {
              nodes { url }
            }
            variants(first: 50) {
              nodes {
                id
                title
                price { amount currencyCode }
                availableForSale
                selectedOptions { name value }
                image { url }
              }
            }
          }
        }
      }
    }
    """

    async def search_products(
        self,
        session: ShoppingSessionContext,
        query: str,
        filters: SearchFilters | None = None,
        limit: int = 8,
    ) -> list[Product]:
        del session
        data = await self._gql(self._SEARCH_QUERY, {"query": query, "first": min(limit, 20)})
        nodes = data.get("search", {}).get("nodes", [])

        products: list[Product] = []
        for n in nodes:
            if not n.get("id") or not self._is_listed(n):
                continue
            details = self._map_product_details(n)
            products.append(
                Product(
                    product_id=details.product_id,
                    title=details.title,
                    brand=details.brand,
                    price=details.price,
                    currency=details.currency,
                    image_url=details.image_url,
                    category=details.category,
                    attributes=details.attributes,
                    in_stock=details.in_stock,
                    short_description=details.short_description,
                    options=details.options,
                )
            )

        if filters:
            if filters.min_price is not None:
                products = [p for p in products if p.price >= filters.min_price]
            if filters.max_price is not None:
                products = [p for p in products if p.price <= filters.max_price]
            if filters.category:
                cat = filters.category.lower()
                products = [p for p in products if (p.category or "").lower() == cat]

        return products[:limit]

    _PRODUCT_QUERY = """
    query GetProduct($id: ID!) @inContext(country: __COUNTRY__) {
      product(id: $id) {
        id
        title
        vendor
        productType
        tags
        description
        descriptionHtml
        availableForSale
        priceRange {
          minVariantPrice { amount currencyCode }
        }
        images(first: 5) {
          nodes { url }
        }
        variants(first: 50) {
          nodes {
            id
            title
            price { amount currencyCode }
            availableForSale
            selectedOptions { name value }
            image { url }
          }
        }
      }
    }
    """

    def product(self, product_id: str) -> ProductDetails | None:
        return self.products.get(product_id) or self.variants.get(product_id)

    async def get_product_details(
        self, session: ShoppingSessionContext, product_id: str
    ) -> ProductDetails | None:
        del session
        if product_id in self.products:
            return self.products[product_id]
        gid = f"gid://shopify/Product/{product_id}"
        data = await self._gql(self._PRODUCT_QUERY, {"id": gid})
        node = data.get("product")
        if not node or not self._is_listed(node):
            return None
        return self._map_product_details(node)

    # ------------------------------------------------------------------
    # Cart — mutations run in SHOPIFY_COUNTRY too, so the cart's currency matches
    # ------------------------------------------------------------------

    _CART_FIELDS = """
        id checkoutUrl
        lines(first: 50) { nodes {
          id quantity
          merchandise { ... on ProductVariant {
            id title price { amount currencyCode }
            product { id title }
            image { url }
            selectedOptions { name value }
          }}
        }}
        cost { subtotalAmount { amount currencyCode } }
    """

    _CART_CREATE = f"""
    mutation CartCreate($lines: [CartLineInput!]!) @inContext(country: __COUNTRY__) {{
      cartCreate(input: {{ lines: $lines }}) {{
        cart {{ {_CART_FIELDS} }}
        userErrors {{ field message }}
      }}
    }}
    """

    _CART_LINES_ADD = f"""
    mutation CartLinesAdd($cartId: ID!, $lines: [CartLineInput!]!) @inContext(country: __COUNTRY__) {{
      cartLinesAdd(cartId: $cartId, lines: $lines) {{
        cart {{ {_CART_FIELDS} }}
        userErrors {{ field message }}
      }}
    }}
    """

    _CART_LINES_UPDATE = f"""
    mutation CartLinesUpdate($cartId: ID!, $lines: [CartLineUpdateInput!]!) @inContext(country: __COUNTRY__) {{
      cartLinesUpdate(cartId: $cartId, lines: $lines) {{
        cart {{ {_CART_FIELDS} }}
        userErrors {{ field message }}
      }}
    }}
    """

    _CART_LINES_REMOVE = f"""
    mutation CartLinesRemove($cartId: ID!, $lineIds: [ID!]!) @inContext(country: __COUNTRY__) {{
      cartLinesRemove(cartId: $cartId, lineIds: $lineIds) {{
        cart {{ {_CART_FIELDS} }}
        userErrors {{ field message }}
      }}
    }}
    """

    _CART_QUERY = f"""
    query GetCart($id: ID!) @inContext(country: __COUNTRY__) {{
      cart(id: $id) {{ {_CART_FIELDS} }}
    }}
    """

    def _map_cart(self, cart_data: dict | None) -> Cart:
        if not cart_data:
            return Cart()
        items: list[CartItem] = []
        for line in cart_data.get("lines", {}).get("nodes", []):
            merch = line.get("merchandise", {})
            product = merch.get("product", {})
            option_values = {o["name"]: o["value"] for o in merch.get("selectedOptions", [])}
            items.append(
                CartItem(
                    product_id=self._parse_gid(merch.get("id", "")),
                    title=product.get("title", merch.get("title", "")),
                    price=self._money(merch.get("price")),
                    quantity=line.get("quantity", 1),
                    image_url=(merch.get("image") or {}).get("url"),
                    option_values=option_values,
                    variant_of=self._parse_gid(product.get("id", "")),
                )
            )
        currency = self._default_currency
        cost = cart_data.get("cost", {})
        subtotal = cost.get("subtotalAmount", {})
        if subtotal:
            currency = subtotal.get("currencyCode", self._default_currency)
        return Cart(items=items, currency=currency)

    def _find_line_id(self, cart_data: dict, variant_id: str) -> str | None:
        for line in cart_data.get("lines", {}).get("nodes", []):
            merch = line.get("merchandise", {})
            if self._parse_gid(merch.get("id", "")) == variant_id:
                return line["id"]
        return None

    async def _get_or_create_cart_id(self, session_id: str) -> str | None:
        return self._session_carts.get(session_id)

    async def _get_raw_cart(self, cart_id: str) -> dict | None:
        data = await self._gql(self._CART_QUERY, {"id": cart_id})
        return data.get("cart")

    async def get_cart(self, session: ShoppingSessionContext) -> Cart:
        cart_id = await self._get_or_create_cart_id(session.session_id)
        if not cart_id:
            return Cart()
        raw = await self._get_raw_cart(cart_id)
        return self._map_cart(raw)

    async def _resolve_first_variant_id(self, product_id: str) -> str:
        cached = self.products.get(product_id)
        if cached and cached.variants:
            for v in cached.variants:
                if v.in_stock:
                    return f"gid://shopify/ProductVariant/{v.product_id}"
        gid = f"gid://shopify/Product/{product_id}"
        data = await self._gql(
            """query ($id: ID!) @inContext(country: __COUNTRY__) { product(id: $id) {
                variants(first: 1) { nodes { id availableForSale } }
            }}""",
            {"id": gid},
        )
        product = data.get("product")
        if not product:
            raise KeyError(f"Product {product_id} not found")
        variants = product.get("variants", {}).get("nodes", [])
        if not variants:
            raise KeyError(f"No variants for product {product_id}")
        if not variants[0].get("availableForSale", False):
            raise Unavailable(f"Product {product_id} is out of stock")
        return variants[0]["id"]

    async def add_to_cart(
        self, session: ShoppingSessionContext, product_id: str, quantity: int
    ) -> Cart:
        """Insurance rules, as telecom's single-line plans: each product is held once
        (quantity 1), and one basic insurance (KVG) per cart, so a new KVG model replaces
        the one already there. Supplementary products (VVG) combine freely."""
        del quantity
        variant_gid = await self._resolve_first_variant_id(product_id)
        variant_id = self._parse_gid(variant_gid)
        cart_id = await self._get_or_create_cart_id(session.session_id)
        line = {"merchandiseId": variant_gid, "quantity": 1}

        if not cart_id:
            data = await self._gql(self._CART_CREATE, {"lines": [line]})
            cart_data = data.get("cartCreate", {}).get("cart")
            if cart_data:
                self._session_carts[session.session_id] = cart_data["id"]
            return self._map_cart(cart_data)

        raw = await self._get_raw_cart(cart_id) or {}
        if self._find_line_id(raw, variant_id):
            return self._map_cart(raw)  # already held; an insurance is taken once
        if self._category_of(product_id) in SINGLE_LINE_CATEGORIES:
            replaced = [
                node["id"]
                for node in raw.get("lines", {}).get("nodes", [])
                if self._category_of(
                    self._parse_gid(node.get("merchandise", {}).get("product", {}).get("id", ""))
                )
                in SINGLE_LINE_CATEGORIES
            ]
            if replaced:
                await self._gql(self._CART_LINES_REMOVE, {"cartId": cart_id, "lineIds": replaced})
        data = await self._gql(self._CART_LINES_ADD, {"cartId": cart_id, "lines": [line]})
        return self._map_cart(data.get("cartLinesAdd", {}).get("cart"))

    def _category_of(self, product_id: str) -> str:
        product = self.product(product_id)
        if product is not None and product.variant_of:
            product = self.product(product.variant_of) or product
        return (product.category or "") if product else ""

    async def update_cart_item(
        self, session: ShoppingSessionContext, product_id: str, quantity: int
    ) -> Cart:
        cart_id = await self._get_or_create_cart_id(session.session_id)
        if not cart_id:
            return Cart()
        raw = await self._get_raw_cart(cart_id)
        if not raw:
            return Cart()
        line_id = self._find_line_id(raw, product_id)
        if not line_id:
            return self._map_cart(raw)
        data = await self._gql(
            self._CART_LINES_UPDATE,
            # Each insurance is held once: a quantity above 1 is capped, 0 removes it.
            {"cartId": cart_id, "lines": [{"id": line_id, "quantity": min(quantity, 1)}]},
        )
        return self._map_cart(data.get("cartLinesUpdate", {}).get("cart"))

    async def remove_from_cart(self, session: ShoppingSessionContext, product_id: str) -> Cart:
        cart_id = await self._get_or_create_cart_id(session.session_id)
        if not cart_id:
            return Cart()
        raw = await self._get_raw_cart(cart_id)
        if not raw:
            return Cart()
        line_id = self._find_line_id(raw, product_id)
        if not line_id:
            return self._map_cart(raw)
        data = await self._gql(self._CART_LINES_REMOVE, {"cartId": cart_id, "lineIds": [line_id]})
        return self._map_cart(data.get("cartLinesRemove", {}).get("cart"))

    async def checkout_handoff(
        self, session: ShoppingSessionContext, cart: Cart
    ) -> list[CheckoutHandoff]:
        cart_id = await self._get_or_create_cart_id(session.session_id)
        if not cart_id:
            return []
        raw = await self._get_raw_cart(cart_id)
        if not raw or not raw.get("checkoutUrl"):
            return []
        return [CheckoutHandoff(url=raw["checkoutUrl"], label="Continue to application")]

    # ------------------------------------------------------------------
    # Customer context (stubbed for demo)
    # ------------------------------------------------------------------

    async def get_preferences(self, session: ShoppingSessionContext) -> UserPreferences:
        return UserPreferences(
            user_id=session.user_id,
            display_name="Shopper",
        )

    # ------------------------------------------------------------------
    # Orders and policies (stubbed for demo)
    # ------------------------------------------------------------------

    async def get_orders(self, session: ShoppingSessionContext, limit: int = 5) -> list[Order]:
        return []

    async def get_order(self, session: ShoppingSessionContext, order_id: str) -> Order | None:
        return None

    async def search_policies(self, session: ShoppingSessionContext, query: str) -> list[Policy]:
        """SWICA's terms from ``data/policies.json``, ranked by term overlap. The contact
        entry always comes back too, so a question the terms do not answer still gets a
        way to reach SWICA."""
        del session
        found = search_help(self._policies, query)
        contact = next((p for p in self._policies if p.policy_id == "contact"), None)
        if contact and contact not in found:
            found.append(contact)
        return found

    # ------------------------------------------------------------------
    # Fulfillment (simplified)
    # ------------------------------------------------------------------

    async def get_fulfillment_options(
        self, session: ShoppingSessionContext, product_ids: list[str]
    ) -> list[FulfillmentOption]:
        return [
            FulfillmentOption(method="delivery", eta="3-5 business days", fee=5.99),
            FulfillmentOption(method="delivery", eta="1-2 business days (express)", fee=12.99),
        ]

    # ------------------------------------------------------------------
    # Full catalog — search_products only fetches what a query matches, but the
    # merchant portal (inventory alerts, browse, SQL analysis) needs the whole
    # store. This walks products(first, after) rather than search(), and fills
    # self.products the same way search/get_product_details do.
    # ------------------------------------------------------------------

    _CATALOG_PAGE_QUERY = """
    query CatalogPage($first: Int!, $after: String) @inContext(country: __COUNTRY__) {
      products(first: $first, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          vendor
          productType
          tags
          description
          descriptionHtml
          availableForSale
          priceRange {
            minVariantPrice { amount currencyCode }
          }
          images(first: 5) {
            nodes { url }
          }
          variants(first: 50) {
            nodes {
              id
              title
              price { amount currencyCode }
              availableForSale
              selectedOptions { name value }
              image { url }
            }
          }
        }
      }
    }
    """

    async def list_catalog(
        self, *, page_size: int = 50, max_products: int = 250
    ) -> list[ProductDetails]:
        """Fetch every product (paginated), caching each into ``self.products`` exactly
        as ``search_products``/``get_product_details`` do. Call once at merchant-backend
        startup and again whenever the portal needs a fresher view; there is no
        change-notification from Shopify here, so staleness is bounded by how often the
        caller re-fetches, not tracked automatically."""
        collected: list[ProductDetails] = []
        cursor: str | None = None
        while len(collected) < max_products:
            data = await self._gql(
                self._CATALOG_PAGE_QUERY,
                {"first": min(page_size, max_products - len(collected)), "after": cursor},
            )
            page = data.get("products", {})
            for node in page.get("nodes", []):
                if not node.get("id") or not self._is_listed(node):
                    continue
                collected.append(self._map_product_details(node))
            page_info = page.get("pageInfo", {})
            if not page_info.get("hasNextPage"):
                break
            cursor = page_info.get("endCursor")
        return collected

    # ------------------------------------------------------------------
    # DemoStorefront protocol extras (demo_common.host) — required to mount the
    # shared merchant portal router alongside the storefront routes.
    # ------------------------------------------------------------------

    def reset_session(self, session_id: str) -> None:
        self._session_carts.pop(session_id, None)

    def recent_orders(self, limit: int = 6) -> list[Order]:
        # Order history lives in Shopify's Admin API, which this demo backend does not
        # call (only the Storefront API). The merchant portal's "recent orders" panel
        # reads the merchant backend's own orders.json instead — see api/merchant.py.
        # Sync on purpose: the shared merchant router calls this without ``await``
        # (matching examples/retail/api/mock_retail.py's own recent_orders, which is
        # sync too) — the DemoStorefront Protocol's "async def" in host.py doesn't match
        # how it's actually called, so the real contract is: keep this synchronous.
        return []
