# The SWICA storefront: a Next.js production build served by `next start`.
# Build from the repository root: docker build -f deploy/web.Dockerfile .
# NEXT_PUBLIC_API_URL is fixed at build time; empty means the API is on the same origin
# under /api (the proxy in deploy/nginx.conf routes it).
FROM node:22-slim AS build
ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /app/examples
COPY examples/package.json examples/package-lock.json ./
COPY examples/web-shared ./web-shared
COPY examples/shopify_demo/storefront-web ./shopify_demo/storefront-web
RUN npm ci --no-audit --no-fund
ARG NEXT_PUBLIC_API_URL=""
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
# next/font downloads the Outfit font from Google Fonts during the build.
RUN npm run build --workspace swica-storefront-web

FROM node:22-slim
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1
WORKDIR /app/examples
COPY --from=build --chown=node:node /app/examples ./
USER node
WORKDIR /app/examples/shopify_demo/storefront-web
EXPOSE 3000
CMD ["npx", "next", "start", "-p", "3000", "-H", "0.0.0.0"]
