# ============================================
# Stage 1 — Composer : install des dépendances PHP
# ============================================
FROM composer:2.7 AS vendor

WORKDIR /app

# Copier les manifests Composer d'abord (cache des dépendances)
COPY composer.json composer.lock ./

# Installer uniquement les dépendances de production
# --no-scripts évite d'exécuter les scripts artisan qui ont besoin du code complet
RUN composer install \
    --no-dev \
    --no-scripts \
    --no-autoloader \
    --prefer-dist \
    --no-interaction \
    --no-progress

# Copier le code complet et générer l'autoloader optimisé
COPY . .
RUN composer dump-autoload --optimize --no-dev

# ============================================
# Stage 2 — Node : build des assets front (Vite/Mix)
# ============================================
FROM node:20-alpine AS assets

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
# Adapter selon ton outil de build :
#   Vite          -> npm run build  (produit /public/build)
#   Laravel Mix   -> npm run production (produit /public/css, /public/js)
RUN npm run build

# ============================================
# Stage 3 — Runtime : PHP-FPM + Nginx
# ============================================
FROM php:8.3-fpm-alpine

# Installer les extensions PHP nécessaires à Laravel
# (pdo_pgsql pour Postgres + pgvector, bcmath, gd, zip, intl, redis si besoin)
RUN apk add --no-cache \
        nginx \
        supervisor \
        postgresql-dev \
        libzip-dev \
        libpng-dev \
        libxml2-dev \
        icu-dev \
        oniguruma-dev \
    && docker-php-ext-install \
        pdo_pgsql \
        pgsql \
        bcmath \
        gd \
        zip \
        intl \
        opcache \
        pcntl \
    && rm -rf /var/cache/apk/*

# Créer un utilisateur non-root pour la sécurité
RUN addgroup -S laravel && adduser -S laravel -G laravel

WORKDIR /var/www/html

# Copier les vendors depuis le stage Composer
COPY --from=vendor --chown=laravel:laravel /app/vendor ./vendor

# Copier les assets buildés depuis le stage Node
COPY --from=assets --chown=laravel:laravel /app/public/build ./public/build

# Copier le code applicatif
COPY --chown=laravel:laravel . .

# Préparer les dossiers nécessaires à Laravel (storage + cache)
RUN mkdir -p storage/framework/{sessions,views,cache} storage/logs bootstrap/cache \
    && chown -R laravel:laravel storage bootstrap/cache \
    && chmod -R 775 storage bootstrap/cache

# Optimisations Laravel pour la prod
# (à exécuter après le COPY pour avoir le code complet)
RUN php artisan config:cache \
    && php artisan route:cache \
    && php artisan view:cache \
    || true  # || true car Laravel peut ne pas être configurable au build (DB pas dispo)

# Configurations Nginx + Supervisor (créés en dehors du Dockerfile)
COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/php-fpm.conf /usr/local/etc/php-fpm.d/www.conf
COPY docker/php.ini /usr/local/etc/php/conf.d/custom.ini

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/health || exit 1

# Supervisor lance Nginx + PHP-FPM ensemble dans le même conteneur
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
