# SWICA insurance agent (Shopify demo)

The shopping agent over a Shopify store whose products are SWICA insurance products. The
API (`api/main.py`, port 8000) serves the storefront routes; the UI is `storefront-web/`
(port 3000), themed for embedding on swica.ch.

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
cd shopify_demo/storefront-web && npx next dev -p 3000
```

Open http://localhost:3000. Each model call logs the gateway's `X-Token-Budget-*` headers
on the `demo_common.gateway` logger, and the turn's `cache_read_input_tokens` on the
runtime logger; from the second turn the cached figure should be above zero.

## Embed on swica.ch

`embed/swica-embed.js` adds an "AI Assistant" / "KI-Assistent" entry to the "How can we help
you?" menu of www.swica.ch, cloned from the site's own entries so it keeps their style; it
opens the storefront (`AGENT_URL`, default `http://localhost:3000/`) in a side panel, in the
page's language. `BUBBLE = true` adds a floating button as well.

swica.ch sends a Content-Security-Policy header whose `frame-src` lists the sites it allows in
iframes; a script on the page (the console, a userscript, or a tag manager) cannot relax it.
Where the iframe is blocked, the embed opens the assistant in a popup window instead. For a
demo on the live site, `scripts/swica_demo.py` opens swica.ch in a browser window that runs the
embed on every page and ignores the CSP, so the side panel works; the site is unchanged:

```bash
pip install playwright && playwright install chromium     # once
python scripts/swica_demo.py                               # --lang en for the English site
```

In production the panel needs `AGENT_URL` on a public https origin that SWICA adds to its
`frame-src`. On localhost the assistant reaches only the machine the storefront runs on.

## Behaviour

- Languages: English and German (Swiss Standard German). The EN | DE switch in the app bar
  sets the interface language and sends it as `page.extra.ui_language` with each message;
  a message written in the other language switches both.
- Terms: `data/policies.json` holds facts from swica.ch (excess, discounts, switching,
  payment, contact), each with its source page. `search_policies` always returns the
  contact entry, so a question the terms do not answer ends with SWICA's phone number,
  consultation booking, contact form, or premium calculator.
- Selection and application: each product is held once, and one basic insurance (KVG) per
  cart, so a new KVG model replaces the previous one. Checkout hands off to the Shopify
  checkout as the application; prices stay "from" premiums throughout.

- Visitors and memory: visitors are anonymous. The API issues each browser a random id
  (`anon-…`), which the browser keeps and sends back on later visits; memory is keyed by it,
  so it follows one visitor and is never shared. A start request can only resume an issued
  id, never claim another. Memory lives in the API process and clears on restart.

## Where things are

- `DEMO.md`: a demo conversation and what each answer shows.
- `api/agent_profile.py`: the agent's name, voice, and insurance rules ("from" premiums,
  personal premium calculated separately).
- `api/shopify_backend.py`: `StorefrontBackend` over the Shopify Storefront API, with the
  cart rules and the terms search.
- `data/policies.json`: SWICA's terms and contact details.
- `storefront-web/app/brand-theme.css`: colours, radii, and type taken from
  swica.ch's design tokens; Outfit stands in for the licensed SWICA typeface.
- `storefront-web/lib/price.ts`: the "from" price label and the CHF default.
- `storefront-web/components/views/HomeView.tsx`: the start prompts.
- `storefront-web/lib/i18n-de.ts`: the German interface text;
  `examples/web-shared/i18n.ts` is the shared `tr` and language switch.
