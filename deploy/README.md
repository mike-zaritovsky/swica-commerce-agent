# Deploying the SWICA demo

Three containers serve the demo on one origin:

| Service | Image | Port | What it is |
|---|---|---|---|
| `api` | `deploy/api.Dockerfile` | 8000 | The agent API (FastAPI, Python 3.12). One instance only: sessions and memory live in the process. Health: `GET /api/health`. |
| `web` | `deploy/web.Dockerfile` | 3000 | The storefront (Next.js production build, Node 22). |
| `proxy` | `nginx:1.27-alpine` with `deploy/nginx.conf` | 80 (published as 8080) | Routes `/api/` to `api` and everything else to `web`, so the browser talks to one origin and needs no CORS. Streams chat replies unbuffered. |

## Run

On a host with Docker, from the repository root, with the variables below in a `.env` file
next to `docker-compose.yml` (or in the environment):

```bash
docker compose up -d --build
```

The demo is then on `http://<host>:8080` (`PROXY_PORT` changes the port). Put TLS and access
control in front of the proxy: a load balancer or ingress with HTTPS, and basic auth, an IP
allowlist, or the company VPN. The demo has no login of its own, and every conversation spends
the gateway budget.

On a platform that runs containers without compose, build the two images from the repository
root and run them with the same variables; the routing in `deploy/nginx.conf` (or the
platform's equivalent) maps `/api/` to the API and `/` to the storefront.

## Variables

The `api` service reads these at start-up; `docker compose` fails with a named error when a
required one is missing.

| Variable | Required | Secret | Meaning |
|---|---|---|---|
| `SHOPIFY_STORE_DOMAIN` | yes | no | The Shopify store, `<name>.myshopify.com` |
| `SHOPIFY_STOREFRONT_TOKEN` | yes | yes | Storefront API access token |
| `FOUNDRY_SUBSCRIPTION_KEY` | yes | yes | dentsu AI gateway subscription key (primary) |
| `FOUNDRY_PROJECT` | yes | no | The gateway project of the primary key |
| `FOUNDRY_SUBSCRIPTION_KEY_FALLBACK` | no | yes | A second key, used when the gateway refuses the primary |
| `FOUNDRY_PROJECT_FALLBACK` | no | no | The gateway project of the fallback key |
| `FOUNDRY_GATEWAY_URL` | no | no | Default `https://ai-api-dev.dentsu.com/foundry` |
| `AGENT_MODEL`, `AGENT_MEMORY_MODEL` | no | no | Defaults `claude-sonnet-5`, `claude-haiku-4-5` |

The storefront takes one build argument, `NEXT_PUBLIC_API_URL`. It is empty by default, which
means the API is on the same origin under `/api/`; set it only when the API is served from a
different origin (that origin then also needs CORS on the API).

## Network

- At run time the `api` container calls `ai-api-dev.dentsu.com` (or `FOUNDRY_GATEWAY_URL`) and
  the Shopify store domain over HTTPS. It honours `HTTPS_PROXY` when a proxy is required.
- The builds download from PyPI, the npm registry, and Google Fonts (the storefront's font).

## Operations

- Logs: one line per model call on the `api` service, with the gateway's remaining budget.
- A restart clears conversations and the assistant's memory of visitors.
- To embed the deployed demo on swica.ch, set `AGENT_URL` in
  `examples/shopify_demo/embed/swica-embed.js` to the public URL, or pass
  `--agent-url https://<host>/` to `scripts/swica_demo.py`.
