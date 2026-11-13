# swica-commerce-agent

For agents working in this repo: the SWICA insurance agent, a shopping agent on the Messages
API over a Shopify store, with its storefront and swica.ch embed.

## Layout

- `commerce-common/commerce_common/`: the shared mechanisms; its `__init__` lists the modules.
- `shopping-agent/core/shopping_agent/`: types, `StorefrontBackend`, config, prompt, `tools/`, gates, enrichment, executor.
- `shopping-agent/runtime-messages-api/`: `ShoppingAgent`, the turn loop.
- `shopping-agent/skills/`: five flows, one `SKILL.md` each.
- `examples/shopify_demo/`: the SWICA demo: `api/` (Shopify backend, agent profile, wiring), `data/` (terms, memory seed), `storefront-web/` (Next.js), `embed/` (swica.ch script); its README says how to run it, `DEMO.md` is a demo conversation.
- `examples/demo_common/`: host code the API uses; `gateway.py` is the `AsyncAnthropic` client for the dentsu AI gateway, with key fallback.
- `examples/web-shared/`: the storefront's shared web code; `i18n.ts` is the interface language (`tr`, `setLocale`, `detectLanguage`).
- `deploy/` and `docker-compose.yml`: the containers (API, storefront, nginx proxy on one origin); `deploy/README.md` lists the variables.
- `scripts/`: `gateway_smoke.py`, `swica_demo.py`, `install.sh`.
- `tests/`: suites that span packages; each package keeps its own `tests/`.

`requirements.txt` installs the three packages and their pinned dependencies
(`requirements-dev.txt` adds pytest and ruff).

## Design rules

- One model owns the conversation; a rule goes in a tool description, the prompt, or a skill by how often it applies.
- The static prompt and `tools[]` are the same bytes on every turn; per-request data goes in the fenced block after the breakpoint.
- UI is presentation tool calls, validated and filled in on the server, streamed as `ui` events.
- Third-party content is fenced data; writes are provenance-gated and capped in code; `checkout` charges nothing.
- Core is domain-neutral; SWICA specifics live in `examples/shopify_demo/` (`agent_profile.py`, the backend, the storefront).
- Secrets live in `.env` only, never in the repository.

## Conventions

- Python 3.11+, `ruff` (root `ruff.toml`), `pytest` (root `pytest.ini`), type hints, `pydantic` schemas; the storefront is Next.js and TypeScript.
- `examples/package-lock.json` is regenerated only from scratch (delete `node_modules` and the lockfile, then `npm install`); regenerating over an installed tree drops other platforms' native packages and breaks macOS and Windows installs.
- Interface text goes through `tr()`; German entries in `storefront-web/lib/i18n-de.ts` are Swiss Standard German (no sharp s).
- Prose: plain declarative sentences; a README says what a thing is, how to run it, and where its interfaces are.
- A new module updates this file and its README.

## Verify

```bash
ruff check . && ruff format --check . && pytest
(cd examples && npm run build)
```
