# joblab web — Vite/React dev container
# Purpose: serve the Vite dev server with HMR; bind-mounted source in dev.
# Created: 2026-05-19

# ---- deps ----
FROM node:20-alpine AS deps
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@9.15.0 --activate
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile || pnpm install

# ---- runtime ----
FROM node:20-alpine AS runtime
ENV NODE_ENV=development \
    HOST=0.0.0.0 \
    PORT=5173

# Enable corepack as root so /usr/local/bin/pnpm symlink exists before we drop privileges.
RUN corepack enable && corepack prepare pnpm@9.15.0 --activate \
    && deluser --remove-home node 2>/dev/null || true \
    && addgroup -g 1000 app && adduser -D -u 1000 -G app app

WORKDIR /app
COPY --from=deps --chown=app:app /app/node_modules ./node_modules
COPY --chown=app:app . .

USER app
EXPOSE 5173
CMD ["pnpm", "dev", "--host", "0.0.0.0", "--port", "5173"]
