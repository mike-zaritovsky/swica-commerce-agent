# SWICA insurance agent

A shopping agent on Claude for SWICA's insurance products: it searches and compares the
products in a Shopify store, answers questions from SWICA's published terms, keeps every
price a "from" premium, fills a selection, and hands off to an application. It speaks English
and Swiss Standard German, runs through the dentsu AI gateway, and embeds in swica.ch.

The agent is built on the shopping agent from Anthropic's commerce-agents reference (Messages
API path); this repository keeps that path and the SWICA demo around it.

## Run

Python 3.11+ and Node 22. Create `.env` at the repo root (`.env.example` lists the variables),
then install once:

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
(cd examples && npm ci)
```

Start the API and the storefront in two terminals, and open http://localhost:3000:

```bash
uvicorn shopify_demo.api.main:app --app-dir examples --reload --port 8000
cd examples/shopify_demo/storefront-web && npx next dev -p 3000
```

[`examples/shopify_demo/README.md`](examples/shopify_demo/README.md) covers configuration,
the swica.ch embed and demo launcher, and where each part lives;
[`examples/shopify_demo/DEMO.md`](examples/shopify_demo/DEMO.md) is a demo conversation.

## Layout

| Directory | Contents | pip package, `import` name |
|---|---|---|
| [`commerce-common/`](commerce-common/) | Config, fencing, memory, skills, grounding, presentation, executor frame, events | `commerce-common`, `commerce_common` |
| [`shopping-agent/core/`](shopping-agent/core/) | Shopping types, `StorefrontBackend`, prompt, tool contracts, gates, executor | `shopping-agent-core`, `shopping_agent` |
| [`shopping-agent/runtime-messages-api/`](shopping-agent/runtime-messages-api/) | `ShoppingAgent`, the turn loop on the Messages API | `shopping-agent-runtime`, `shopping_agent_runtime` |
| [`shopping-agent/skills/`](shopping-agent/skills/) | The agent's five flows, one `SKILL.md` each | — |
| [`examples/`](examples/) | The SWICA demo (`shopify_demo/`), its host code (`demo_common/`), shared web code (`web-shared/`) | — |
| [`scripts/`](scripts/) | `gateway_smoke.py` (checks the gateway keys), `swica_demo.py` (swica.ch with the assistant), `install.sh` | — |
| [`tests/`](tests/) | Suites that span packages; each package also has its own `tests/` | — |

## Verify

```bash
pip install -r requirements-dev.txt
ruff check . && ruff format --check . && pytest
(cd examples && npm run build)
python scripts/gateway_smoke.py      # live: each gateway key, streaming, tools, caching
```
