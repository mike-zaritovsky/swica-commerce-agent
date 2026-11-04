# SWICA insurance agent (Shopify demo)

The shopping agent over a Shopify store whose products are SWICA insurance products. The
API (`api/main.py`, port 8000) serves the storefront routes and the merchant routes under
`/api/merchant`; the UI is `examples/retail/storefront-web` (port 3000), themed for
embedding on swica.ch.

## Configure

Create `.env` at the repo root (never committed; `.env.example` lists every variable):

```
SHOPIFY_STORE_DOMAIN=...
SHOPIFY_STOREFRONT_TOKEN=...
FOUNDRY_SUBSCRIPTION_KEY=...           # dentsu AI gateway, primary key
FOUNDRY_PROJECT=...                    # the gateway project that key belongs to
FOUNDRY_SUBSCRIPTION_KEY_FALLBACK=...  # used when the primary is refused (401/403/429)
FOUNDRY_PROJECT_FALLBACK=...           # the fallback key's project
```

Check the keys before the first run; it sends a plain request on both models, a streamed
request with a tool, and two cached requests, per key:

```bash
python scripts/gateway_smoke.py
```

The backend lists only the `SHOPIFY_VENDOR` products (default `SWICA`; the store's other
items never surface) and runs every Shopify query in `SHOPIFY_COUNTRY` (default `CH`), so
prices come back in Swiss francs.

With `FOUNDRY_SUBSCRIPTION_KEY` set, model calls go through the gateway
(`examples/demo_common/gateway.py`); without it, through `ANTHROPIC_API_KEY`. Models default
to `claude-sonnet-5` and `claude-haiku-4-5` (`AGENT_MODEL`, `AGENT_MEMORY_MODEL`).

## Run

From the repo root, in two terminals:

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
uvicorn shopify_demo.api.main:app --app-dir examples --reload --port 8000
```

```bash
cd examples && npm ci
cd retail/storefront-web && npx next dev -p 3000
```

Open http://localhost:3000. Each model call logs the gateway's `X-Token-Budget-*` headers
on the `demo_common.gateway` logger, and the turn's `cache_read_input_tokens` on the
runtime logger; from the second turn the cached figure should be above zero.

## Where things are

- `api/agent_profile.py`: the agent's name, voice, and insurance rules ("from" premiums,
  personal premium calculated separately).
- `api/shopify_backend.py`: `StorefrontBackend` over the Shopify Storefront API.
- `examples/retail/storefront-web/app/brand-theme.css`: colours, radii, and type taken from
  swica.ch's design tokens; Outfit stands in for the licensed SWICA typeface.
- `examples/retail/storefront-web/lib/price.ts`: the "from" price label and the CHF default.
- `examples/retail/storefront-web/components/views/HomeView.tsx`: the start prompts.
