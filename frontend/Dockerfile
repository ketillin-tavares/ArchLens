# syntax=docker/dockerfile:1.7

# ══════════════════════════════════════════════════════════════════════
#  Stage 1 — builder: instala deps e gera /app/dist (Vite)
# ══════════════════════════════════════════════════════════════════════
FROM node:24-alpine AS builder

WORKDIR /app

COPY package.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm install --no-audit --no-fund

COPY . .

# Variáveis do Vite precisam existir em build-time
ARG VITE_KONG_BASE_URL
ARG VITE_CLERK_PUBLISHABLE_KEY
ARG VITE_CLERK_JWT_TEMPLATE=""

ENV VITE_KONG_BASE_URL=$VITE_KONG_BASE_URL \
    VITE_CLERK_PUBLISHABLE_KEY=$VITE_CLERK_PUBLISHABLE_KEY \
    VITE_CLERK_JWT_TEMPLATE=$VITE_CLERK_JWT_TEMPLATE

RUN npm run build

# ══════════════════════════════════════════════════════════════════════
#  Stage 2 — runtime: nginx servindo /app/dist + proxy para Kong
# ══════════════════════════════════════════════════════════════════════
FROM nginx:1.27-alpine AS runtime

# hadolint ignore=DL3018
RUN apk add --no-cache curl \
 && rm -rf /usr/share/nginx/html/* \
 && mkdir -p /var/cache/nginx/client_temp \
             /var/cache/nginx/proxy_temp \
             /var/cache/nginx/fastcgi_temp \
             /var/cache/nginx/uwsgi_temp \
             /var/cache/nginx/scgi_temp \
 && chown -R nginx:nginx /var/cache/nginx \
                         /var/log/nginx \
 && touch /var/run/nginx.pid \
 && chown nginx:nginx /var/run/nginx.pid

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS http://localhost:8080/health || exit 1

USER nginx

CMD ["nginx", "-g", "daemon off;"]
