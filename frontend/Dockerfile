# Frontend Dockerfile: build with Node, serve with nginx
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ---- runtime ----
FROM nginx:1.27-alpine AS runtime

# Drop privileges
RUN addgroup -g 1000 app && adduser -G app -u 1000 -D -H -s /sbin/nologin app

# SPA-friendly nginx config
COPY --chown=app:app nginx.conf /etc/nginx/conf.d/default.conf

# Static assets
COPY --from=build --chown=app:app /app/dist /usr/share/nginx/html

USER app

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost:8080/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
