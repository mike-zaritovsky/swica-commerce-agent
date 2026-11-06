# examples

The SWICA demo: its API and storefront in `shopify_demo/`, and the host and web code they
build on.

| Path | Contents |
|---|---|
| `shopify_demo/` | The SWICA insurance agent: the API over the Shopify store (`api/`), its terms and memory seed (`data/`), the storefront (`storefront-web/`), and the swica.ch embed (`embed/`); its README says how to run it |
| `demo_common/` | Host code the API uses: app and middleware (`host.py`), session store (`sessions.py`), storefront routes (`storefront.py`), memory routes and seeder (`memory.py`), the help-content search (`storefront_fixtures.py`), and the dentsu gateway client (`gateway.py`) |
| `web-shared/` | The npm package the storefront imports: the API client, the session and turn hooks, the event types (`protocol.ts` mirrors `commerce_common/streaming.py`), the transcript and inspector components, the storefront frame (`storefront/`), interface language (`i18n.ts`), shared primitives and icons |
| `package.json` | The npm workspace: `web-shared` and `shopify_demo/storefront-web` (`npm ci` installs both) |

Sessions and carts live in one process's memory in `demo_common`, so the API runs one worker.
