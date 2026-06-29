# ============================================
# Stage 1 — Build : compiler le front
# ============================================
FROM node:20-alpine AS builder

WORKDIR /build

# Copier les manifests d'abord pour cacher l'install
COPY package*.json ./
RUN npm ci

# Copier le code et builder
COPY . .
RUN npm run build

# ============================================
# Stage 2 — Runtime : Nginx léger
# ============================================
FROM nginx:1.27-alpine

# Copier la config nginx custom
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copier le build du stage précédent
# Adapter le chemin selon le framework :
#   React/Vite      -> /build/dist
#   Create React    -> /build/build
#   Next.js static  -> /build/out
COPY --from=builder /build/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
